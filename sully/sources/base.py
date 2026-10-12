"""Database: connection, schemas, and fetch bookkeeping.

Each source declares its own tables; this module only owns the bookkeeping ones:
when each source was last fetched, and where to resume an interrupted paginated
fetch.
"""

import os
from datetime import UTC, datetime

import psycopg
from psycopg.rows import dict_row

from .registry import Source, schemas

URL_VARIABLE = "DATABASE_URL"

FETCH_SCHEMA = """
CREATE TABLE IF NOT EXISTS fetch_log (
    source     TEXT PRIMARY KEY,
    fetched_at TIMESTAMPTZ NOT NULL,
    report     TEXT
);

CREATE TABLE IF NOT EXISTS fetch_cursor (
    source TEXT PRIMARY KEY,
    cursor TEXT NOT NULL
);
"""

Connection = psycopg.Connection[dict]


class DatabaseMissing(Exception):
    pass


def connect() -> Connection:
    url = os.environ.get(URL_VARIABLE)
    if not url:
        raise DatabaseMissing(f"Variable {URL_VARIABLE} absente de l'environnement.")
    return psycopg.connect(url, autocommit=True, row_factory=dict_row)


def migrate(connection: Connection) -> None:
    with connection.transaction():
        connection.execute(FETCH_SCHEMA)
        for schema in schemas():
            connection.execute(schema)


def batched(rows, size: int = 5_000):
    batch = []
    for row in rows:
        batch.append(row)
        if len(batch) == size:
            yield batch
            batch = []
    if batch:
        yield batch


def upsert(connection: Connection, statement: str, rows) -> int:
    written = 0
    with connection.transaction(), connection.cursor() as cursor:
        for batch in batched(rows):
            cursor.executemany(statement, batch)
            written += len(batch)
    return written


def last_fetch(connection: Connection, name: str) -> datetime | None:
    row = connection.execute(
        "SELECT fetched_at FROM fetch_log WHERE source = %s", (name,)
    ).fetchone()
    return row["fetched_at"] if row else None


def record_fetch(connection: Connection, name: str, report: str) -> None:
    connection.execute(
        "INSERT INTO fetch_log (source, fetched_at, report) VALUES (%s, %s, %s) "
        "ON CONFLICT (source) DO UPDATE SET "
        "fetched_at = excluded.fetched_at, report = excluded.report",
        (name, datetime.now(UTC), report),
    )


def saved_cursor(connection: Connection, name: str) -> str | None:
    row = connection.execute(
        "SELECT cursor FROM fetch_cursor WHERE source = %s", (name,)
    ).fetchone()
    return row["cursor"] if row else None


def save_cursor(connection: Connection, name: str, cursor: str | None) -> None:
    """`None` clears the cursor once the fetch has reached its end. Call it in the
    transaction that writes the page, so the cursor never runs ahead of the data."""
    if cursor is None:
        connection.execute("DELETE FROM fetch_cursor WHERE source = %s", (name,))
        return
    connection.execute(
        "INSERT INTO fetch_cursor (source, cursor) VALUES (%s, %s) "
        "ON CONFLICT (source) DO UPDATE SET cursor = excluded.cursor",
        (name, cursor),
    )


def is_due(connection: Connection, source: Source) -> bool:
    previous = last_fetch(connection, source.name)
    if previous is None:
        return True
    if source.interval is None:
        return False
    return datetime.now(UTC) - previous >= source.interval
