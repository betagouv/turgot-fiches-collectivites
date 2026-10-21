"""Database: connection, schemas, and fetch bookkeeping.

Each source declares its own tables; this module only owns the bookkeeping ones:
when each source was last fetched, and where to resume an interrupted paginated
fetch.

A fetch writes into a schema of its own, `staging_<source>`, created from the
source's current schema; its tables then replace the public ones in a single
transaction, so readers see the previous snapshot until the new one is complete.
"""

import os
from collections.abc import Iterator
from contextlib import contextmanager
from datetime import UTC, datetime
from itertools import batched

import psycopg
from psycopg import sql
from psycopg.rows import dict_row

from .registry import Source, schemas

URL_VARIABLE = "DATABASE_URL"
BATCH_SIZE = 5_000

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


def _staging(source: Source) -> str:
    return f"staging_{source.name}"


def _exists(connection: Connection, schema: str) -> bool:
    row = connection.execute(
        "SELECT 1 FROM pg_namespace WHERE nspname = %s", (schema,)
    ).fetchone()
    return row is not None


@contextmanager
def staged(connection: Connection, source: Source) -> Iterator[None]:
    """Within the block, the source's tables are those of its staging schema.

    A paginated fetch interrupted midway resumes into the schema it left;
    otherwise the schema starts afresh."""
    schema = _staging(source)
    identifier = sql.Identifier(schema)
    resuming = saved_cursor(connection, source.name) is not None and _exists(
        connection, schema
    )
    if not resuming:
        save_cursor(connection, source.name, None)
        connection.execute(
            sql.SQL("DROP SCHEMA IF EXISTS {} CASCADE").format(identifier)
        )
        connection.execute(sql.SQL("CREATE SCHEMA {}").format(identifier))
    connection.execute(sql.SQL("SET search_path TO {}, public").format(identifier))
    try:
        if not resuming:
            connection.execute(source.schema)
        yield
    finally:
        connection.execute("RESET search_path")


def publish(connection: Connection, source: Source) -> None:
    """Replace the source's public tables with its staged ones. CASCADE takes the
    foreign keys between a source's own tables with them, whatever their order."""
    schema = _staging(source)
    tables = connection.execute(
        "SELECT tablename FROM pg_tables WHERE schemaname = %s", (schema,)
    ).fetchall()
    with connection.transaction():
        for row in tables:
            table = sql.Identifier(row["tablename"])
            connection.execute(
                sql.SQL("DROP TABLE IF EXISTS public.{} CASCADE").format(table)
            )
            connection.execute(
                sql.SQL("ALTER TABLE {}.{} SET SCHEMA public").format(
                    sql.Identifier(schema), table
                )
            )
        connection.execute(sql.SQL("DROP SCHEMA {}").format(sql.Identifier(schema)))


def insert(table: str, columns: tuple[str, ...]) -> str:
    """An INSERT of `columns` into `table`, its rows given as dicts."""
    names = ", ".join(columns)
    values = ", ".join(f"%({column})s" for column in columns)
    return f"INSERT INTO {table} ({names}) VALUES ({values})"


def write(connection: Connection, statement: str, rows) -> int:
    """Run `statement` once per row, by batches, in one transaction."""
    written = 0
    with connection.transaction(), connection.cursor() as cursor:
        for batch in batched(rows, BATCH_SIZE):
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
