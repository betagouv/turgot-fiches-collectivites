"""Each test module reads its tables from the `input/` folder next to it, loaded
into a schema of its own, and compares what it renders to `output/`.

`TEST_DATABASE_URL` names the database the schemas are created in; each is
dropped at the end of its module."""

import json
import os
import uuid
from datetime import datetime
from pathlib import Path

import psycopg
import pytest
from fastapi.testclient import TestClient
from psycopg import sql
from psycopg.conninfo import make_conninfo

from fico.main import app
from fico.sources import base
from fico.sources.registry import schemas

TEST_URL_VARIABLE = "TEST_DATABASE_URL"


def pytest_addoption(parser):
    parser.addoption(
        "--update-references",
        action="store_true",
        help="Réécrit les rendus de référence au lieu de les comparer.",
    )


def _creation_rank(path: Path) -> int:
    """Schemas declare a table before those referencing it: loading in that
    order satisfies foreign keys."""
    return "\n".join(schemas()).find(f"CREATE TABLE IF NOT EXISTS {path.stem} ")


def _load(connection: base.Connection, data: Path) -> None:
    """Each `<table>.csv` into its table, its header naming the columns."""
    for path in sorted(data.glob("*.csv"), key=_creation_rank):
        with path.open(encoding="utf-8") as file:
            columns = file.readline().strip().split(",")
        statement = sql.SQL("COPY {} ({}) FROM STDIN WITH (FORMAT csv, HEADER true)")
        statement = statement.format(
            sql.Identifier(path.stem),
            sql.SQL(", ").join(sql.Identifier(column) for column in columns),
        )
        with connection.cursor().copy(statement) as copy:
            copy.write(path.read_bytes())


@pytest.fixture(scope="module")
def client(request):
    url = os.environ.get(TEST_URL_VARIABLE)
    if not url:
        pytest.fail(f"Variable {TEST_URL_VARIABLE} absente de l'environnement.")
    schema = sql.Identifier(f"test_{uuid.uuid4().hex[:12]}")
    with psycopg.connect(url, autocommit=True) as connection:
        connection.execute(sql.SQL("CREATE SCHEMA {}").format(schema))
    try:
        with pytest.MonkeyPatch.context() as patch:
            scoped = make_conninfo(url, options=f"-csearch_path={schema.as_string()}")
            patch.setenv(base.URL_VARIABLE, scoped)
            with base.connect() as connection:
                base.migrate(connection)
                _load(connection, request.path.parent / "input")
            yield TestClient(app)
    finally:
        with psycopg.connect(url, autocommit=True) as connection:
            connection.execute(sql.SQL("DROP SCHEMA {} CASCADE").format(schema))


@pytest.fixture
def reference(request):
    """Compares a rendering to `output/<name>.json`, or rewrites it under
    `--update-references`."""
    folder = request.path.parent / "output"
    update = request.config.getoption("--update-references")

    def check(name: str, rendered) -> None:
        path = folder / f"{name}.json"
        if update:
            folder.mkdir(exist_ok=True)
            text = json.dumps(rendered, indent=2, ensure_ascii=False)
            path.write_text(text + "\n", encoding="utf-8")
            return
        assert path.exists(), f"{path} absent : à créer avec --update-references"
        assert rendered == json.loads(path.read_text(encoding="utf-8"))

    return check


@pytest.fixture
def freeze(monkeypatch):
    """Sets what `datetime.now()` returns in `module`."""

    def apply(module, now: datetime) -> None:
        class Frozen(datetime):
            @classmethod
            def now(cls, tz=None):
                return now.replace(tzinfo=tz)

        monkeypatch.setattr(module, "datetime", Frozen)

    return apply
