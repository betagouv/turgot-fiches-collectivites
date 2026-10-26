"""Contours des communes et des EPCI simplifiés au palier 100 m, simplification
faite par le producteur sur la couverture entière.

https://www.data.gouv.fr/datasets/contours-administratifs
"""

import gzip
import json

import httpx

from . import database
from .registry import Schedule, source

BASE_URL = "https://object.data.gouv.fr/contours-administratifs/2025/geojson"
COMMUNES = f"{BASE_URL}/communes-100m.geojson.gz"
EPCI = f"{BASE_URL}/epci-100m.geojson.gz"

SCHEMA = """
CREATE TABLE IF NOT EXISTS contour (
    code        TEXT PRIMARY KEY,
    nom         TEXT,
    departement TEXT,
    epci        TEXT,
    geometry    TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS contour_departement ON contour (departement);
CREATE INDEX IF NOT EXISTS contour_epci ON contour (epci);

CREATE TABLE IF NOT EXISTS epci_contour (
    code     TEXT PRIMARY KEY,
    nom      TEXT,
    geometry TEXT NOT NULL
);
"""

COLUMNS = ("code", "nom", "departement", "epci", "geometry")

INSERT = database.insert_statement("contour", COLUMNS)
INSERT_EPCI = database.insert_statement("epci_contour", ("code", "nom", "geometry"))


def _features(client: httpx.Client, url: str) -> list[dict]:
    response = client.get(url, follow_redirects=True, timeout=300)
    response.raise_for_status()
    return json.loads(gzip.decompress(response.content).decode("utf-8"))["features"]


def _rows(features: list[dict]):
    for feature in features:
        properties = feature["properties"]
        yield {
            "code": properties["code"],
            "nom": properties.get("nom", ""),
            "departement": properties.get("departement", ""),
            "epci": properties.get("epci") or "",
            "geometry": json.dumps(feature["geometry"]),
        }


@source(
    name="contours",
    label="data.gouv.fr, contours administratifs : contours des communes et des "
    "EPCI simplifiés à 100 m",
    schedule=Schedule.ONESHOT,
    schema=SCHEMA,
)
def fetch(client: httpx.Client, connection: database.Connection) -> str:
    communes = database.write(connection, INSERT, _rows(_features(client, COMMUNES)))
    epci = database.write(connection, INSERT_EPCI, _rows(_features(client, EPCI)))
    return f"{communes} commune(s), {epci} EPCI"


def _contours(rows) -> list[dict]:
    """Each row with its GeoJSON geometry decoded."""
    return [
        {
            "code": row["code"],
            "nom": row["nom"],
            "geometry": json.loads(row["geometry"]),
        }
        for row in rows
    ]


def by_departement(connection: database.Connection, code: str) -> list[dict]:
    return _contours(
        connection.execute(
            "SELECT code, nom, geometry FROM contour WHERE departement = %s "
            "ORDER BY code",
            (code,),
        )
    )


def by_epci(connection: database.Connection, siren: str) -> list[dict]:
    return _contours(
        connection.execute(
            "SELECT code, nom, geometry FROM contour WHERE epci = %s ORDER BY code",
            (siren,),
        )
    )


def epci(connection: database.Connection, sirens: list[str]) -> list[dict]:
    """The contours of the EPCI of `sirens`, their SIREN in `code`."""
    return _contours(
        connection.execute(
            "SELECT code, nom, geometry FROM epci_contour WHERE code = ANY(%s) "
            "ORDER BY code",
            (sirens,),
        )
    )
