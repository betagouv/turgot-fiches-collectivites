"""Local database: connection, schemas, and fetch bookkeeping.

Each source declares its own tables; this module only owns the bookkeeping ones:
when each source was last fetched, and where to resume an interrupted paginated
fetch.
"""

import sqlite3
from datetime import UTC, datetime
from pathlib import Path

from .registry import Source, schemas

DB_PATH = Path(__file__).parent.parent.parent / ".cache" / "sully.db"

FETCH_SCHEMA = """
CREATE TABLE IF NOT EXISTS fetch_log (
    source    TEXT PRIMARY KEY,
    fetched_at TEXT NOT NULL,
    report    TEXT
);

CREATE TABLE IF NOT EXISTS fetch_cursor (
    source TEXT PRIMARY KEY,
    cursor TEXT NOT NULL
);
"""


def connect(path: Path = DB_PATH) -> sqlite3.Connection:
    path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(path)
    connection.row_factory = sqlite3.Row
    # Sorting 200k rows otherwise spills into a temp file.
    connection.execute("PRAGMA temp_store = MEMORY")
    connection.executescript(FETCH_SCHEMA)
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


def saved_cursor(connection: sqlite3.Connection, name: str) -> str | None:
    row = connection.execute(
        "SELECT cursor FROM fetch_cursor WHERE source = ?", (name,)
    ).fetchone()
    return row["cursor"] if row else None


def save_cursor(connection: sqlite3.Connection, name: str, cursor: str | None) -> None:
    """`None` clears the cursor once the fetch has reached its end. Call it in the
    transaction that writes the page, so the cursor never runs ahead of the data."""
    if cursor is None:
        connection.execute("DELETE FROM fetch_cursor WHERE source = ?", (name,))
        return
    connection.execute(
        "INSERT INTO fetch_cursor (source, cursor) VALUES (?, ?) "
        "ON CONFLICT (source) DO UPDATE SET cursor = excluded.cursor",
        (name, cursor),
    )


def is_due(connection: sqlite3.Connection, source: Source) -> bool:
    previous = last_fetch(connection, source.name)
    if previous is None:
        return True
    if source.interval is None:
        return False
    return datetime.now(UTC) - previous >= source.interval
