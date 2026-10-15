"""API Collectivités: consolidated projets and their financements (State
dotations, Fonds vert, agences de l'eau, ADEME, public procurement…).

Access is restricted to State services: this data must not be redistributed.

The database keeps only the fields the fiches read.

https://api.collectivites.beta.gouv.fr/api/consultation
"""

import json
import os
import time

import httpx
import psycopg

from . import base
from .registry import Interrupted, Schedule, source

NAME = "api-collectivites"
URL = "https://api.collectivites.beta.gouv.fr/consultation/v1/projets"
TOKEN_VARIABLE = "API_COLLECTIVITES_TOKEN"
PAGE_SIZE = 1000
ATTEMPTS = 6

SCHEMA = """
CREATE TABLE IF NOT EXISTS projet (
    id                  BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    provenances         TEXT NOT NULL,
    siren               TEXT,
    nom                 TEXT,
    porteur_nom         TEXT,
    budget_previsionnel DOUBLE PRECISION,
    phase               TEXT,
    phase_statut        TEXT,
    ouverture           TEXT,
    thematiques         TEXT
);
CREATE INDEX IF NOT EXISTS projet_siren ON projet (siren);

CREATE TABLE IF NOT EXISTS projet_commune (
    projet_id  BIGINT NOT NULL REFERENCES projet (id),
    code_insee TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS projet_commune_insee ON projet_commune (code_insee);

CREATE TABLE IF NOT EXISTS financement (
    projet_id         BIGINT NOT NULL REFERENCES projet (id),
    source            TEXT,
    annee             INTEGER,
    montant_demande   DOUBLE PRECISION,
    montant_attribue  DOUBLE PRECISION,
    statut            TEXT
);
CREATE INDEX IF NOT EXISTS financement_projet ON financement (projet_id);
"""

INSERT_PROJET = """
INSERT INTO projet (
    provenances, siren, nom, porteur_nom, budget_previsionnel, phase,
    phase_statut, ouverture, thematiques
)
VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
RETURNING id
"""

INSERT_COMMUNE = "INSERT INTO projet_commune (projet_id, code_insee) VALUES (%s, %s)"

INSERT_FINANCEMENT = """
INSERT INTO financement
    (projet_id, source, annee, montant_demande, montant_attribue, statut)
VALUES (%s, %s, %s, %s, %s, %s)
"""


class TokenMissing(Exception):
    pass


def _retry_delay(response: httpx.Response, attempt: int) -> int:
    # Retry-After may also be an HTTP date, which falls back to the backoff.
    retry_after = response.headers.get("retry-after", "")
    return int(retry_after) if retry_after.isdigit() else 5 * 2**attempt


def _page(client: httpx.Client, token: str, cursor: str | None) -> httpx.Response:
    params = {"limit": PAGE_SIZE}
    if cursor:
        params["cursor"] = cursor
    headers = {"Authorization": f"Bearer {token}"}
    for attempt in range(ATTEMPTS):
        response = client.get(URL, params=params, headers=headers)
        if response.status_code != 429 and response.status_code < 500:
            break
        if attempt < ATTEMPTS - 1:
            time.sleep(_retry_delay(response, attempt))
    response.raise_for_status()
    return response


def _store(cursor: psycopg.Cursor, projet: dict) -> None:
    provenances = "|".join(
        sorted(f"{p['provenance']}:{p['idSource']}" for p in projet["provenances"])
    )
    labels = projet.get("labels") or {}
    cursor.execute(
        INSERT_PROJET,
        (
            provenances,
            projet.get("collectiviteResponsableSiren"),
            projet.get("nom"),
            projet.get("porteurNom"),
            projet.get("budgetPrevisionnel"),
            projet.get("phase"),
            projet.get("phaseStatut"),
            projet.get("ouverture"),
            json.dumps(
                labels.get("classificationThematiques") or [], ensure_ascii=False
            ),
        ),
    )
    projet_id = cursor.fetchone()["id"]
    # Upstream sometimes packs a whole territory into one comma-separated item.
    codes = [
        code.strip()
        for item in projet.get("territoireCommunes") or []
        for code in item.split(",")
        if code.strip()
    ]
    cursor.executemany(INSERT_COMMUNE, [(projet_id, code) for code in codes])
    cursor.executemany(
        INSERT_FINANCEMENT,
        [
            (
                projet_id,
                f.get("source"),
                int(f["dateAttribution"][:4]) if f.get("dateAttribution") else None,
                f.get("montantDemande"),
                f.get("montantAttribue"),
                f.get("statut"),
            )
            for f in projet.get("financements") or []
        ],
    )


def _counts(connection: base.Connection) -> tuple[int, int]:
    row = connection.execute(
        "SELECT (SELECT COUNT(*) FROM projet) AS projets, "
        "(SELECT COUNT(*) FROM financement) AS financements"
    ).fetchone()
    return row["projets"], row["financements"]


@source(
    name=NAME,
    label="API Collectivités : projets et financements consolidés",
    schedule=Schedule.DAILY,
    schema=SCHEMA,
    paginated=True,
)
def fetch(
    client: httpx.Client, connection: base.Connection, max_pages: int | None = None
) -> str:
    token = os.environ.get(TOKEN_VARIABLE)
    if not token:
        raise TokenMissing(f"Variable {TOKEN_VARIABLE} absente de l'environnement.")

    cursor = base.saved_cursor(connection, NAME)
    if cursor is None:
        # Upstream rebuilds its base without stable identifiers, so a fresh
        # snapshot replaces the previous one instead of merging into it.
        connection.execute("TRUNCATE financement, projet_commune, projet")

    start = time.perf_counter()
    pages = 0
    downloaded = 0
    projets, financements = _counts(connection)
    while True:
        response = _page(client, token, cursor)
        payload = response.json()
        cursor = payload.get("nextCursor")
        with connection.transaction(), connection.cursor() as writer:
            for projet in payload["data"]:
                _store(writer, projet)
            base.save_cursor(connection, NAME, cursor)
        pages += 1
        downloaded += response.num_bytes_downloaded
        projets += len(payload["data"])
        financements += sum(len(p.get("financements") or []) for p in payload["data"])
        minutes = (time.perf_counter() - start) / 60
        print(
            f"    page {pages:>4} — {projets} projets, "
            f"{financements} financements en base, "
            f"{downloaded / 1e6:.1f} Mo reçus, {minutes:.1f} min",
            flush=True,
        )
        if not cursor:
            break
        if max_pages and pages >= max_pages:
            raise Interrupted(
                f"arrêt après {pages} pages et {downloaded / 1e6:.1f} Mo reçus, "
                f"{projets} projets en base — reprise au prochain appel"
            )

    return f"{projets} projets, {financements} financements"


RECEIVED = "f.statut IN ('Obtenu', 'Payé')"


def financements_recus(
    connection: base.Connection, siren: str, since: int | None = None
) -> list[dict]:
    """From `since` on when given, the financements without a year included."""
    return connection.execute(
        f"""
        SELECT f.annee, f.source, f.montant_attribue,
               p.nom, p.budget_previsionnel
        FROM financement f JOIN projet p ON p.id = f.projet_id
        WHERE p.siren = %(siren)s AND {RECEIVED}
          AND (%(since)s::int IS NULL OR f.annee IS NULL OR f.annee >= %(since)s)
        ORDER BY f.annee DESC NULLS LAST,
                 f.source COLLATE "fr-x-icu", p.nom COLLATE "fr-x-icu"
        """,
        {"siren": siren, "since": since},
    ).fetchall()


def totaux_par_source(connection: base.Connection, siren: str) -> list[dict]:
    return connection.execute(
        f"""
        SELECT f.source,
               SUM(f.montant_attribue) AS montant,
               COUNT(DISTINCT f.projet_id) AS projets
        FROM financement f JOIN projet p ON p.id = f.projet_id
        WHERE p.siren = %s AND {RECEIVED}
        GROUP BY f.source
        ORDER BY montant DESC
        """,
        (siren,),
    ).fetchall()


def totaux_par_annee(connection: base.Connection, siren: str) -> list[dict]:
    return connection.execute(
        f"""
        SELECT f.annee,
               SUM(f.montant_attribue) AS montant,
               COUNT(*) AS financements
        FROM financement f JOIN projet p ON p.id = f.projet_id
        WHERE p.siren = %s AND {RECEIVED}
        GROUP BY f.annee
        ORDER BY f.annee
        """,
        (siren,),
    ).fetchall()


def _par_projet(siren_condition: str) -> str:
    """Attribué and budget per projet, over the projets that publish both, as
    upstream's own taux de financement does: a budget alone would deflate the
    rate."""
    return f"""
        SELECT p.siren, p.budget_previsionnel AS budget,
               SUM(f.montant_attribue) AS attribue
        FROM projet p JOIN financement f ON f.projet_id = p.id
        WHERE {siren_condition} AND {RECEIVED}
          AND p.budget_previsionnel > 0 AND f.montant_attribue IS NOT NULL
        GROUP BY p.id
    """


def taux_par_commune(connection: base.Connection, codes_insee) -> dict[str, float]:
    """Taux de financement of the projets each commune carries."""
    codes = list(codes_insee)
    if not codes:
        return {}
    par_projet = _par_projet(
        "p.siren IN (SELECT siren FROM collectivite WHERE code_insee = ANY(%s))"
    )
    rows = connection.execute(
        f"""
        SELECT c.code_insee, SUM(attribue) AS montant, SUM(budget) AS cout
        FROM ({par_projet}) AS par_projet
        JOIN collectivite c ON c.siren = par_projet.siren
        GROUP BY c.code_insee
        """,
        (codes,),
    ).fetchall()
    return {row["code_insee"]: row["montant"] / row["cout"] for row in rows}


def cofinancement(connection: base.Connection, siren: str) -> dict:
    par_projet = _par_projet("p.siren = %s")
    return connection.execute(
        f"""
        SELECT SUM(attribue) AS montant, SUM(budget) AS cout, COUNT(*) AS projets
        FROM ({par_projet}) AS par_projet
        """,
        (siren,),
    ).fetchone()
