"""API Collectivités: consolidated projets and their financements (State
dotations, Fonds vert, agences de l'eau, ADEME, public procurement…).

Access is restricted to State services: this data must not be redistributed.

The database keeps only the fields the fiches read.

https://api.collectivites.beta.gouv.fr/api/consultation
"""

import gzip
import hashlib
import json
import os
import tempfile
from itertools import batched
from typing import IO

import httpx

from . import database
from .registry import Schedule, source

SCHEMA = """
CREATE TABLE IF NOT EXISTS projet (
    id                  BIGINT PRIMARY KEY,
    siren               TEXT,
    nom                 TEXT,
    budget_previsionnel DOUBLE PRECISION
);
CREATE INDEX IF NOT EXISTS projet_siren ON projet (siren);

CREATE TABLE IF NOT EXISTS financement (
    projet_id         BIGINT NOT NULL REFERENCES projet (id),
    source            TEXT,
    reference         TEXT,
    annee             INTEGER,
    montant_attribue  DOUBLE PRECISION,
    statut            TEXT
);
CREATE INDEX IF NOT EXISTS financement_projet ON financement (projet_id);
"""

INSERT_PROJET = database.insert_statement(
    "projet", ("id", "siren", "nom", "budget_previsionnel")
)
INSERT_FINANCEMENT = database.insert_statement(
    "financement",
    ("projet_id", "source", "reference", "annee", "montant_attribue", "statut"),
)


def _projet(projet_id: int, projet: dict) -> dict:
    return {
        "id": projet_id,
        "siren": projet.get("collectiviteResponsableSiren"),
        "nom": projet.get("nom"),
        "budget_previsionnel": projet.get("budgetPrevisionnel"),
    }


def _financements(projet_id: int, projet: dict) -> list[dict]:
    return [
        {
            "projet_id": projet_id,
            "source": financement.get("source"),
            "reference": financement.get("referenceExterne"),
            "annee": int(financement["dateAttribution"][:4])
            if financement.get("dateAttribution")
            else None,
            "montant_attribue": financement.get("montantAttribue"),
            "statut": financement.get("statut"),
        }
        for financement in projet.get("financements") or []
    ]


def _download(client: httpx.Client, url: str, archive: IO[bytes]) -> str:
    """Write the export into `archive` as served, and return its SHA-256."""
    digest = hashlib.sha256()
    with client.stream("GET", url, timeout=600) as response:
        response.raise_for_status()
        for chunk in response.iter_raw():
            digest.update(chunk)
            archive.write(chunk)
    return digest.hexdigest()


def _store(connection: database.Connection, lines: IO[str]) -> tuple[int, int]:
    projets = financements = 0
    numbered = enumerate(map(json.loads, lines), start=1)
    with connection.transaction(), connection.cursor() as cursor:
        for batch in batched(numbered, database.BATCH_SIZE):
            funding = [row for item in batch for row in _financements(*item)]
            cursor.executemany(INSERT_PROJET, [_projet(*item) for item in batch])
            cursor.executemany(INSERT_FINANCEMENT, funding)
            projets += len(batch)
            financements += len(funding)
            print(f"    {projets} projets, {financements} financements", flush=True)
    return projets, financements


@source(
    name="api-collectivites",
    label="API Collectivités (api.collectivites.beta.gouv.fr) : projets et "
    "financements consolidés",
    schedule=Schedule.DAILY,
    schema=SCHEMA,
)
def fetch(client: httpx.Client, connection: database.Connection) -> str:
    token = os.environ["API_COLLECTIVITES_TOKEN"]
    # Describes the nightly export, one projet per line, and gives its download URL.
    response = client.get(
        "https://api.collectivites.beta.gouv.fr/consultation/v1/export/description",
        headers={"Authorization": f"Bearer {token}"},
    )
    response.raise_for_status()
    export = response.json()
    with tempfile.TemporaryFile() as archive:
        if _download(client, export["url"], archive) != export["sha256"]:
            raise ValueError(f"Empreinte inattendue pour l'export {export['url']}.")
        archive.seek(0)
        with gzip.open(archive, "rt", encoding="utf-8") as lines:
            projets, financements = _store(connection, lines)
    return f"{projets} projets, {financements} financements ({export['generatedAt']})"


RECEIVED = "f.statut IN ('Obtenu', 'Payé')"
# From `since` on when given, the financements without a year included.
SINCE = "(%(since)s::int IS NULL OR f.annee IS NULL OR f.annee >= %(since)s)"
FINANCEUR = "(%(financeur)s::text IS NULL OR f.source = %(financeur)s)"


def financements_recus(
    connection: database.Connection, siren: str, since: int | None = None
) -> list[dict]:
    return connection.execute(
        f"""
        SELECT f.annee, f.source, f.reference, f.montant_attribue,
               p.nom, p.budget_previsionnel
        FROM financement f JOIN projet p ON p.id = f.projet_id
        WHERE p.siren = %(siren)s AND {RECEIVED} AND {SINCE}
        ORDER BY f.annee DESC NULLS LAST,
                 f.source COLLATE "fr-x-icu", p.nom COLLATE "fr-x-icu"
        """,
        {"siren": siren, "since": since},
    ).fetchall()


def totaux(
    connection: database.Connection,
    siren: str,
    since: int | None = None,
    financeur: str | None = None,
) -> dict:
    return connection.execute(
        f"""
        SELECT SUM(f.montant_attribue) AS montant,
               COUNT(DISTINCT f.projet_id) AS projets,
               MIN(f.annee) AS first_year, MAX(f.annee) AS last_year
        FROM financement f JOIN projet p ON p.id = f.projet_id
        WHERE p.siren = %(siren)s AND {RECEIVED} AND {SINCE} AND {FINANCEUR}
        """,
        {"siren": siren, "since": since, "financeur": financeur},
    ).fetchone()


def montants_by_siren(
    connection: database.Connection,
    sirens: list[str],
    years: range,
    financeur: str | None = None,
) -> dict[str, float]:
    """What the projets each of `sirens` carries received during `years`; a
    SIREN that received nothing is absent."""
    rows = connection.execute(
        f"""
        SELECT p.siren, SUM(f.montant_attribue) AS montant
        FROM financement f JOIN projet p ON p.id = f.projet_id
        WHERE p.siren = ANY(%(sirens)s) AND {RECEIVED} AND {FINANCEUR}
          AND f.annee >= %(start)s AND f.annee < %(stop)s
          AND f.montant_attribue IS NOT NULL
        GROUP BY p.siren
        """,
        {
            "sirens": sirens,
            "start": years.start,
            "stop": years.stop,
            "financeur": financeur,
        },
    ).fetchall()
    return {row["siren"]: row["montant"] for row in rows}


def totaux_by_source(
    connection: database.Connection, siren: str, since: int | None = None
) -> list[dict]:
    return connection.execute(
        f"""
        SELECT f.source,
               SUM(f.montant_attribue) AS montant,
               COUNT(DISTINCT f.projet_id) AS projets
        FROM financement f JOIN projet p ON p.id = f.projet_id
        WHERE p.siren = %(siren)s AND {RECEIVED} AND {SINCE}
        GROUP BY f.source
        ORDER BY montant DESC
        """,
        {"siren": siren, "since": since},
    ).fetchall()


def totaux_by_annee(
    connection: database.Connection, siren: str, since: int | None = None
) -> list[dict]:
    return connection.execute(
        f"""
        SELECT f.annee,
               SUM(f.montant_attribue) AS montant,
               COUNT(*) AS financements
        FROM financement f JOIN projet p ON p.id = f.projet_id
        WHERE p.siren = %(siren)s AND {RECEIVED} AND {SINCE}
        GROUP BY f.annee
        ORDER BY f.annee
        """,
        {"siren": siren, "since": since},
    ).fetchall()


def _by_projet(siren_condition: str) -> str:
    """Attribué and budget per projet, over the projets that publish both, as
    upstream's own taux de financement does: a budget alone would deflate the
    rate."""
    return f"""
        SELECT p.siren, p.budget_previsionnel AS budget,
               SUM(f.montant_attribue) AS attribue
        FROM projet p JOIN financement f ON f.projet_id = p.id
        WHERE {siren_condition} AND {RECEIVED} AND {SINCE} AND {FINANCEUR}
          AND p.budget_previsionnel > 0 AND f.montant_attribue IS NOT NULL
        GROUP BY p.id
    """


def taux_by_commune(connection: database.Connection, codes_insee) -> dict[str, float]:
    """Taux de financement of the projets each commune carries."""
    codes = list(codes_insee)
    if not codes:
        return {}
    by_projet = _by_projet(
        "p.siren IN (SELECT siren FROM commune WHERE code_insee = ANY(%(codes)s))"
    )
    rows = connection.execute(
        f"""
        SELECT c.code_insee, SUM(attribue) AS montant, SUM(budget) AS cout
        FROM ({by_projet}) AS by_projet
        JOIN commune c ON c.siren = by_projet.siren
        GROUP BY c.code_insee
        """,
        {"codes": codes, "since": None, "financeur": None},
    ).fetchall()
    return {row["code_insee"]: row["montant"] / row["cout"] for row in rows}


def taux_by_siren(
    connection: database.Connection, sirens: list[str]
) -> dict[str, float]:
    """Taux de financement of the projets each of `sirens` carries."""
    by_projet = _by_projet("p.siren = ANY(%(sirens)s)")
    rows = connection.execute(
        f"""
        SELECT siren, SUM(attribue) AS montant, SUM(budget) AS cout
        FROM ({by_projet}) AS by_projet
        GROUP BY siren
        """,
        {"sirens": sirens, "since": None, "financeur": None},
    ).fetchall()
    return {row["siren"]: row["montant"] / row["cout"] for row in rows}


def cofinancement(
    connection: database.Connection,
    siren: str,
    since: int | None = None,
    financeur: str | None = None,
) -> dict:
    """A projet's whole budget counts as soon as one of its financements falls
    from `since` on, or comes from `financeur`: the rate is then the share of
    that budget the selected financements cover."""
    by_projet = _by_projet("p.siren = %(siren)s")
    return connection.execute(
        f"""
        SELECT SUM(attribue) AS montant, SUM(budget) AS cout, COUNT(*) AS projets
        FROM ({by_projet}) AS by_projet
        """,
        {"siren": siren, "since": since, "financeur": financeur},
    ).fetchone()
