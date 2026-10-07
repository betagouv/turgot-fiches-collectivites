"""La table des subventions d'investissement, alimentée par `dgcl` et
`fonds_vert`."""

import sqlite3

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
    cout_total        REAL,
    montant_accorde   REAL,
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
VALUES ({", ".join(f":{c}" for c in COLUMNS)})
ON CONFLICT (source, source_id) DO UPDATE SET
{", ".join(f"{c} = excluded.{c}" for c in COLUMNS if c not in ("source", "source_id"))}
"""


def par_siren(connection: sqlite3.Connection, siren: str) -> list[sqlite3.Row]:
    return connection.execute(
        "SELECT * FROM subvention WHERE siren = ? ORDER BY annee DESC, dispositif",
        (siren,),
    ).fetchall()


def totaux_par_annee(connection: sqlite3.Connection, siren: str) -> list[sqlite3.Row]:
    return connection.execute(
        """
        SELECT annee, dispositif,
               SUM(montant_accorde) AS montant,
               COUNT(*) AS projets
        FROM subvention
        WHERE siren = ?
        GROUP BY annee, dispositif
        ORDER BY annee
        """,
        (siren,),
    ).fetchall()


def totaux_par_dispositif(
    connection: sqlite3.Connection, siren: str
) -> list[sqlite3.Row]:
    return connection.execute(
        """
        SELECT dispositif,
               SUM(montant_accorde) AS montant,
               COUNT(*) AS projets
        FROM subvention
        WHERE siren = ?
        GROUP BY dispositif
        ORDER BY montant DESC
        """,
        (siren,),
    ).fetchall()


def cofinancement(connection: sqlite3.Connection, siren: str) -> sqlite3.Row:
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
        WHERE siren = ? AND cout_total IS NOT NULL AND cout_total > 0
        """,
        (siren,),
    ).fetchone()


def taux_par_commune(connection: sqlite3.Connection, codes_insee) -> dict[str, float]:
    codes = list(codes_insee)
    if not codes:
        return {}
    marks = ", ".join("?" * len(codes))
    rows = connection.execute(
        f"""
        SELECT code_insee,
               SUM(montant_accorde) AS montant,
               SUM(cout_total) AS cout
        FROM subvention
        WHERE cout_total IS NOT NULL AND cout_total > 0 AND code_insee IN ({marks})
        GROUP BY code_insee
        """,
        codes,
    ).fetchall()
    return {
        row["code_insee"]: row["montant"] / row["cout"] for row in rows if row["cout"]
    }
