import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).parent.parent.parent / ".cache" / "subventions.db"

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

CREATE TABLE IF NOT EXISTS programme (
    code_insee TEXT NOT NULL,
    programme  TEXT NOT NULL,
    libelle    TEXT,
    depuis     TEXT,
    PRIMARY KEY (code_insee, programme)
);
"""

PROGRAMME_COLUMNS = ("code_insee", "programme", "libelle", "depuis")

UPSERT_PROGRAMME = f"""
INSERT INTO programme ({", ".join(PROGRAMME_COLUMNS)})
VALUES ({", ".join(f":{c}" for c in PROGRAMME_COLUMNS)})
ON CONFLICT (code_insee, programme) DO UPDATE SET
libelle = excluded.libelle, depuis = excluded.depuis
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


def connect(path: Path = DB_PATH) -> sqlite3.Connection:
    path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(path)
    connection.row_factory = sqlite3.Row
    # Sorting 200k rows spills to a temp file otherwise.
    connection.execute("PRAGMA temp_store = MEMORY")
    connection.executescript(SCHEMA)
    return connection


def upsert(connection: sqlite3.Connection, rows) -> int:
    written = 0
    with connection:
        for batch in _batched(rows, 5_000):
            connection.executemany(UPSERT, batch)
            written += len(batch)
    return written


def _batched(rows, size):
    batch = []
    for row in rows:
        batch.append(row)
        if len(batch) == size:
            yield batch
            batch = []
    if batch:
        yield batch


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
               SUM(cout_total) AS cout,
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
    marques = ", ".join("?" * len(codes))
    lignes = connection.execute(
        f"""
        SELECT code_insee,
               SUM(montant_accorde) AS montant,
               SUM(cout_total) AS cout
        FROM subvention
        WHERE cout_total IS NOT NULL AND cout_total > 0 AND code_insee IN ({marques})
        GROUP BY code_insee
        """,
        codes,
    ).fetchall()
    return {
        ligne["code_insee"]: ligne["montant"] / ligne["cout"]
        for ligne in lignes
        if ligne["cout"]
    }


def upsert_programmes(connection: sqlite3.Connection, rows) -> int:
    written = 0
    with connection:
        for batch in _batched(rows, 5_000):
            connection.executemany(UPSERT_PROGRAMME, batch)
            written += len(batch)
    return written


def programmes_de(connection: sqlite3.Connection, code_insee: str) -> list[sqlite3.Row]:
    return connection.execute(
        "SELECT * FROM programme WHERE code_insee = ? ORDER BY programme",
        (code_insee,),
    ).fetchall()


def compte(connection: sqlite3.Connection) -> int:
    return connection.execute("SELECT COUNT(*) FROM subvention").fetchone()[0]


def compte_programmes(connection: sqlite3.Connection) -> int:
    return connection.execute("SELECT COUNT(*) FROM programme").fetchone()[0]
