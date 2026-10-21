"""BANATIC, la base nationale sur l'intercommunalité : les groupements (EPCI,
syndicats, PETR…).

L'export national est un classeur d'une seule feuille, une ligne par membre de
chaque groupement. Il pèse 1,5 Go décompressé : il est lu en flux.

https://www.data.gouv.fr/datasets/5e1f20058b4c414d3f94460d
"""

import io
import zipfile
from datetime import date
from xml.etree.ElementTree import iterparse

import httpx

from . import base
from .registry import Schedule, source

URL = (
    "https://www.banatic.interieur.gouv.fr/consultation/api/export/pregenere/"
    "telecharger/France"
)
SHEET = "xl/worksheets/sheet1.xml"
NS = "{http://schemas.openxmlformats.org/spreadsheetml/2006/main}"

SCHEMA = """
CREATE TABLE IF NOT EXISTS groupement (
    siren            TEXT PRIMARY KEY,
    nom              TEXT NOT NULL,
    type             TEXT NOT NULL,
    population       INTEGER,
    code_departement TEXT,
    nom_departement  TEXT,
    mode_financement TEXT,
    date_creation    DATE
);
"""

COLUMNS = (
    "siren",
    "nom",
    "type",
    "population",
    "code_departement",
    "nom_departement",
    "mode_financement",
    "date_creation",
)

INSERT = base.insert("groupement", COLUMNS)


def _sheet_rows(archive: zipfile.ZipFile):
    """Each row as {column letters: text}: the export writes every cell as an
    inline string."""
    with archive.open(SHEET) as sheet:
        for _, element in iterparse(sheet):
            if element.tag != f"{NS}row":
                continue
            cells = {}
            for cell in element.iter(f"{NS}c"):
                text = cell.find(f"{NS}is/{NS}t")
                if text is not None and text.text:
                    cells[cell.get("r").rstrip("0123456789")] = text.text.strip()
            element.clear()
            yield cells


def _date(text: str | None) -> date | None:
    if not text:
        return None
    day, month, year = text.split("/")
    return date(int(year), int(month), int(day))


def _groupement(cells: dict, column: dict) -> dict:
    code, _, nom = cells.get(column["Département"], "").partition(" - ")
    population = cells.get(column["Population totale"])
    return {
        "siren": cells[column["N° SIREN"]],
        "nom": cells[column["Nom du groupement"]],
        "type": cells[column["Nature juridique"]],
        "population": int(population) if population else None,
        "code_departement": code or None,
        "nom_departement": nom or None,
        "mode_financement": cells.get(column["Mode de financement"]),
        "date_creation": _date(cells.get(column["Date de création"])),
    }


def parse(content: bytes) -> list[dict]:
    rows = _sheet_rows(zipfile.ZipFile(io.BytesIO(content)))
    column = {name: letters for letters, name in next(rows).items()}
    groupements = {}
    for cells in rows:
        siren = cells.get(column["N° SIREN"])
        if siren and siren not in groupements:
            groupements[siren] = _groupement(cells, column)
    return list(groupements.values())


@source(
    name="banatic",
    label="BANATIC, base nationale sur l'intercommunalité : groupements",
    schedule=Schedule.MONTHLY,
    schema=SCHEMA,
)
def fetch(client: httpx.Client, connection: base.Connection) -> str:
    response = client.get(URL, timeout=600)
    response.raise_for_status()
    written = base.write(connection, INSERT, parse(response.content))
    return f"{written} groupement(s)"
