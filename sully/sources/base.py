"""La base locale : connexion, application des schémas, suivi des récupérations.

Chaque source déclare sa propre table ; ce module n'en possède qu'une, celle
qui retient quand chaque source a été récupérée.
"""

import sqlite3
from datetime import UTC, datetime
from pathlib import Path

from .registry import Source, schemas

DB_PATH = Path(__file__).parent.parent.parent / ".cache" / "sully.db"

FETCH_LOG_SCHEMA = """
CREATE TABLE IF NOT EXISTS fetch_log (
    source    TEXT PRIMARY KEY,
    fetched_at TEXT NOT NULL,
    report    TEXT
);
"""


def connect(path: Path = DB_PATH) -> sqlite3.Connection:
    path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(path)
    connection.row_factory = sqlite3.Row
    # Trier 200 000 lignes déborde sinon dans un fichier temporaire.
    connection.execute("PRAGMA temp_store = MEMORY")
    connection.executescript(FETCH_LOG_SCHEMA)
    for schema in schemas():
        connection.executescript(schema)
    return connection


def batched(rows, size: int = 5_000):
    batch = []
    for row in rows:
        batch.append(row)
        if len(batch) == size:
            yield batch
            batch = []
    if batch:
        yield batch


def upsert(connection: sqlite3.Connection, statement: str, rows) -> int:
    written = 0
    with connection:
        for batch in batched(rows):
            connection.executemany(statement, batch)
            written += len(batch)
    return written


def last_fetch(connection: sqlite3.Connection, name: str) -> datetime | None:
    row = connection.execute(
        "SELECT fetched_at FROM fetch_log WHERE source = ?", (name,)
    ).fetchone()
    return datetime.fromisoformat(row["fetched_at"]) if row else None


def record_fetch(connection: sqlite3.Connection, name: str, report: str) -> None:
    with connection:
        connection.execute(
            "INSERT INTO fetch_log (source, fetched_at, report) VALUES (?, ?, ?) "
            "ON CONFLICT (source) DO UPDATE SET "
            "fetched_at = excluded.fetched_at, report = excluded.report",
            (name, datetime.now(UTC).isoformat(), report),
        )


def is_due(connection: sqlite3.Connection, source: Source) -> bool:
    previous = last_fetch(connection, source.name)
    if previous is None:
        return True
    if source.interval is None:
        return False
    return datetime.now(UTC) - previous >= source.interval
