"""La table des subventions d'investissement, alimentée par `dgcl` et
`fonds_vert`."""

from . import base

SOURCE_DGCL = "dgcl"
SOURCE_FONDS_VERT = "fonds_vert"

SCHEMA = """
CREATE TABLE IF NOT EXISTS subvention (
    source            TEXT NOT NULL,
    source_id         TEXT NOT NULL,
    dispositif        TEXT NOT NULL,
    annee             INTEGER NOT NULL,
    siren             TEXT NOT NULL,
    beneficiaire_nom  TEXT,
    code_insee        TEXT,
    code_departement  TEXT,
    libelle           TEXT,
    cout_total        DOUBLE PRECISION,
    montant_accorde   DOUBLE PRECISION,
    PRIMARY KEY (source, source_id)
);
CREATE INDEX IF NOT EXISTS subvention_siren ON subvention (siren);
CREATE INDEX IF NOT EXISTS subvention_insee ON subvention (code_insee);
"""

COLUMNS = (
    "source",
    "source_id",
    "dispositif",
    "annee",
    "siren",
    "beneficiaire_nom",
    "code_insee",
    "code_departement",
    "libelle",
    "cout_total",
    "montant_accorde",
)

UPSERT = f"""
INSERT INTO subvention ({", ".join(COLUMNS)})
VALUES ({", ".join(f"%({c})s" for c in COLUMNS)})
ON CONFLICT (source, source_id) DO UPDATE SET
{", ".join(f"{c} = excluded.{c}" for c in COLUMNS if c not in ("source", "source_id"))}
"""


def par_siren(connection: base.Connection, siren: str) -> list[dict]:
    return connection.execute(
        "SELECT * FROM subvention WHERE siren = %s ORDER BY annee DESC, dispositif",
        (siren,),
    ).fetchall()


def totaux_par_annee(connection: base.Connection, siren: str) -> list[dict]:
    return connection.execute(
        """
        SELECT annee, dispositif,
               SUM(montant_accorde) AS montant,
               COUNT(*) AS projets
        FROM subvention
        WHERE siren = %s
        GROUP BY annee, dispositif
        ORDER BY annee
        """,
        (siren,),
    ).fetchall()


def totaux_par_dispositif(connection: base.Connection, siren: str) -> list[dict]:
    return connection.execute(
        """
        SELECT dispositif,
               SUM(montant_accorde) AS montant,
               COUNT(*) AS projets
        FROM subvention
        WHERE siren = %s
        GROUP BY dispositif
        ORDER BY montant DESC
        """,
        (siren,),
    ).fetchall()


def cofinancement(connection: base.Connection, siren: str) -> dict:
    """Accordé et coût des projets, restreint aux lignes qui publient un coût.

    Le Fonds vert ne publie que le montant engagé : l'inclure gonflerait le taux
    en ajoutant de l'accordé sans son coût.
    """
    return connection.execute(
        """
        SELECT SUM(montant_accorde) AS montant,
               SUM(cout_total) AS cout,
               COUNT(*) AS projets
        FROM subvention
        WHERE siren = %s AND cout_total IS NOT NULL AND cout_total > 0
        """,
        (siren,),
    ).fetchone()


def taux_par_commune(connection: base.Connection, codes_insee) -> dict[str, float]:
    codes = list(codes_insee)
    if not codes:
        return {}
    rows = connection.execute(
        """
        SELECT code_insee,
               SUM(montant_accorde) AS montant,
               SUM(cout_total) AS cout
        FROM subvention
        WHERE cout_total IS NOT NULL AND cout_total > 0 AND code_insee = ANY(%s)
        GROUP BY code_insee
        """,
        (codes,),
    ).fetchall()
    return {
        row["code_insee"]: row["montant"] / row["cout"] for row in rows if row["cout"]
    }
