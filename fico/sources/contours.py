"""Contours communaux simplifiés au palier 100 m, simplification faite par le
producteur sur la couverture entière.

https://www.data.gouv.fr/datasets/contours-administratifs
"""

import gzip
import json

import httpx

from . import base
from .registry import Schedule, source

URL = (
    "https://object.data.gouv.fr/contours-administratifs/2025/geojson/"
    "communes-100m.geojson.gz"
)

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
"""

COLUMNS = ("code", "nom", "departement", "epci", "geometry")

UPSERT = f"""
INSERT INTO contour ({", ".join(COLUMNS)})
VALUES ({", ".join(f"%({c})s" for c in COLUMNS)})
ON CONFLICT (code) DO UPDATE SET
{", ".join(f"{c} = excluded.{c}" for c in COLUMNS if c != "code")}
"""


def _rows(payload: dict):
    for feature in payload["features"]:
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
    label="data.gouv.fr, contours administratifs : contours communaux simplifiés "
    "à 100 m",
    schedule=Schedule.ONESHOT,
    schema=SCHEMA,
)
def fetch(client: httpx.Client, connection: base.Connection) -> str:
    response = client.get(URL, follow_redirects=True, timeout=300)
    response.raise_for_status()
    payload = json.loads(gzip.decompress(response.content).decode("utf-8"))
    written = base.upsert(connection, UPSERT, _rows(payload))
    return f"{written} commune(s)"


def _collection(rows) -> dict:
    return {
        "type": "FeatureCollection",
        "features": [
            {
                "type": "Feature",
                "properties": {"code": row["code"], "nom": row["nom"]},
                "geometry": json.loads(row["geometry"]),
            }
            for row in rows
        ],
    }


def par_departement(connection: base.Connection, code: str) -> dict:
    return _collection(
        connection.execute(
            "SELECT code, nom, geometry FROM contour WHERE departement = %s "
            "ORDER BY code",
            (code,),
        )
    )


def par_epci(connection: base.Connection, siren: str) -> dict:
    return _collection(
        connection.execute(
            "SELECT code, nom, geometry FROM contour WHERE epci = %s ORDER BY code",
            (siren,),
        )
    )
