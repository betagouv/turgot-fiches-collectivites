"""Programmes nationaux d'accompagnement dont une commune peut relever.

Les listes sont publiées par commune, chacune avec son propre en-tête. Pour ACV
la source retenue est la Caisse des Dépôts : la liste ANCT ne couvre que la
seconde vague, 50 communes contre 244.
"""

import csv
import io
from dataclasses import dataclass
from datetime import date

import httpx

from . import database
from .registry import Schedule, source

DATA_GOUV_URL = "https://www.data.gouv.fr/api/1/datasets"

SCHEMA = """
CREATE TABLE IF NOT EXISTS programme (
    code_insee TEXT NOT NULL,
    programme  TEXT NOT NULL,
    depuis     DATE,
    PRIMARY KEY (code_insee, programme)
);
"""

COLUMNS = ("code_insee", "programme", "depuis")

UPSERT = f"""
{database.insert_statement("programme", COLUMNS)}
ON CONFLICT (code_insee, programme) DO UPDATE SET depuis = excluded.depuis
"""


@dataclass(frozen=True)
class DateColumn:
    name: str
    format: str


@dataclass(frozen=True)
class Programme:
    code: str
    nom: str
    dataset: str
    resource: str | None = None
    date_column: DateColumn | None = None


PROGRAMMES = (
    Programme(
        code="ACV",
        nom="Action cœur de ville",
        dataset="5fa9901c66cff095591963e8",
        date_column=DateColumn("date_signature", "%Y-%m-%d"),
    ),
    Programme(
        code="PVD",
        nom="Petites villes de demain",
        dataset="5fc1259b703620ed60a49d97",
        date_column=DateColumn("date_signature", "%d/%m/%Y"),
    ),
    Programme(
        code="TI",
        nom="Territoires d'industrie",
        dataset="5fc1472f114718d419e42f8a",
        resource="communes couvertes",
    ),
    Programme(
        code="VA",
        nom="Villages d'avenir",
        dataset="65a11234a86f08c56f0c47b0",
    ),
)

BY_CODE = {programme.code: programme for programme in PROGRAMMES}


def _resource(client: httpx.Client, programme: Programme) -> dict:
    response = client.get(f"{DATA_GOUV_URL}/{programme.dataset}/")
    response.raise_for_status()
    files = [
        r
        for r in response.json().get("resources", [])
        if r.get("format", "").lower() == "csv"
    ]
    if programme.resource:
        files = [r for r in files if programme.resource in r.get("title", "").lower()]
    if not files:
        raise ValueError(f"Aucune ressource CSV pour {programme.code}")
    return files[0]


def _depuis(row: dict, programme: Programme) -> date | None:
    column = programme.date_column
    if column is None:
        return None
    text = (row.get(column.name) or "").strip()
    if not text:
        return None
    return date.strptime(text, column.format)


def rows(client: httpx.Client, programme: Programme):
    resource = _resource(client, programme)
    response = client.get(resource["url"], follow_redirects=True)
    response.raise_for_status()
    text = response.content.decode("utf-8-sig", errors="replace")
    header = text.split("\n", 1)[0]
    delimiter = ";" if header.count(";") > header.count(",") else ","

    for row in csv.DictReader(io.StringIO(text), delimiter=delimiter):
        code_insee = (row.get("insee_com") or "").strip()
        if not code_insee:
            continue
        yield {
            "code_insee": code_insee,
            "programme": programme.code,
            "depuis": _depuis(row, programme),
        }


@source(
    name="programmes",
    label="data.gouv.fr : programmes Action cœur de ville (liste de la Caisse des "
    "Dépôts), Petites villes de demain, Territoires d'industrie, Villages d'avenir",
    schedule=Schedule.MONTHLY,
    schema=SCHEMA,
)
def fetch(client: httpx.Client, connection: database.Connection) -> str:
    counts = []
    for programme in PROGRAMMES:
        written = database.write(connection, UPSERT, rows(client, programme))
        counts.append(f"{programme.code} {written}")
    return ", ".join(counts)


def for_commune(connection: database.Connection, code_insee: str) -> list[dict]:
    return connection.execute(
        "SELECT * FROM programme WHERE code_insee = %s ORDER BY programme",
        (code_insee,),
    ).fetchall()
