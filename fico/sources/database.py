"""Database: connection, schemas, and fetch bookkeeping.

Each source declares its own tables; this module only owns the bookkeeping one:
when each source was last fetched.

A fetch writes into a schema of its own, `staging_<source>`, created from the
source's current schema; its tables then replace the public ones in a single
transaction, so readers see the previous snapshot until the new one is complete.
"""

import os
from collections.abc import Iterator
from contextlib import contextmanager
from contextvars import ContextVar
from datetime import UTC, datetime
from itertools import batched

import psycopg
from psycopg import sql
from psycopg.rows import dict_row

from ..errors import FicoError
from .registry import Source, schemas

BATCH_SIZE = 5_000

FETCH_SCHEMA = """
CREATE TABLE IF NOT EXISTS fetch_log (
    source     TEXT PRIMARY KEY,
    fetched_at TIMESTAMPTZ NOT NULL,
    report     TEXT
);
"""


class DatabaseMissing(FicoError):
    def __init__(self):
        super().__init__("Variable DATABASE_URL absente de l'environnement.")


class CurrentConnection:
    """The connection the innermost `connect()` block opened, in this thread or
    this request: `connection.execute(...)` runs on it."""

    def __init__(self):
        self._opened: ContextVar[psycopg.Connection[dict]] = ContextVar("connection")

    @contextmanager
    def connect(self) -> Iterator[None]:
        url = os.environ.get("DATABASE_URL")
        if not url:
            raise DatabaseMissing()
        with psycopg.connect(url, autocommit=True, row_factory=dict_row) as opened:
            token = self._opened.set(opened)
            try:
                yield
            finally:
                self._opened.reset(token)

    def __getattr__(self, name: str):
        return getattr(self._opened.get(), name)


connection = CurrentConnection()


def migrate() -> None:
    with connection.transaction():
        connection.execute(FETCH_SCHEMA)
        for schema in schemas():
            connection.execute(schema)


def _staging(source: Source) -> str:
    return f"staging_{source.name}"


@contextmanager
def staged(source: Source) -> Iterator[None]:
    """Within the block, the source's tables are those of a fresh staging
    schema."""
    identifier = sql.Identifier(_staging(source))
    connection.execute(sql.SQL("DROP SCHEMA IF EXISTS {} CASCADE").format(identifier))
    connection.execute(sql.SQL("CREATE SCHEMA {}").format(identifier))
    connection.execute(sql.SQL("SET search_path TO {}, public").format(identifier))
    try:
        connection.execute(source.schema)
        yield
    finally:
        connection.execute("RESET search_path")


def publish(source: Source) -> None:
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


def insert_statement(table: str, columns: tuple[str, ...]) -> str:
    """An INSERT of `columns` into `table`, its rows given as dicts."""
    names = ", ".join(columns)
    values = ", ".join(f"%({column})s" for column in columns)
    return f"INSERT INTO {table} ({names}) VALUES ({values})"


def write(statement: str, rows) -> int:
    """Run `statement` once per row, by batches, in one transaction."""
    written = 0
    with connection.transaction(), connection.cursor() as cursor:
        for batch in batched(rows, BATCH_SIZE):
            cursor.executemany(statement, batch)
            written += len(batch)
    return written


def last_fetch(name: str) -> datetime | None:
    row = connection.execute(
        "SELECT fetched_at FROM fetch_log WHERE source = %s", (name,)
    ).fetchone()
    return row["fetched_at"] if row else None


def record_fetch(name: str, report: str) -> None:
    connection.execute(
        "INSERT INTO fetch_log (source, fetched_at, report) VALUES (%s, %s, %s) "
        "ON CONFLICT (source) DO UPDATE SET "
        "fetched_at = excluded.fetched_at, report = excluded.report",
        (name, datetime.now(UTC), report),
    )


def is_due(source: Source) -> bool:
    previous = last_fetch(source.name)
    if previous is None:
        return True
    if source.interval is None:
        return False
    return datetime.now(UTC) - previous >= source.interval
