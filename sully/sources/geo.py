"""geo.api.gouv.fr : superficie d'une commune, et index SIREN → code INSEE.

L'API Référentiel adresse les communes par code INSEE seulement, d'où cet index.
"""

import sqlite3

import httpx

from . import base
from .registry import source

BASE_URL = "https://geo.api.gouv.fr"

SCHEMA = """
CREATE TABLE IF NOT EXISTS siren_insee (
    siren      TEXT PRIMARY KEY,
    code_insee TEXT NOT NULL
);
"""

UPSERT = """
INSERT INTO siren_insee (siren, code_insee) VALUES (:siren, :code_insee)
ON CONFLICT (siren) DO UPDATE SET code_insee = excluded.code_insee
"""


@source(
    name="siren",
    label="Index SIREN → code INSEE",
    schedule=source.MONTHLY,
    schema=SCHEMA,
)
def fetch(client: httpx.Client, connection: sqlite3.Connection) -> str:
    response = client.get(f"{BASE_URL}/communes", params={"fields": "code,siren"})
    response.raise_for_status()
    rows = (
        {"siren": commune["siren"], "code_insee": commune["code"]}
        for commune in response.json()
        if commune.get("siren")
    )
    written = base.upsert(connection, UPSERT, rows)
    return f"{written} commune(s)"


def code_insee_de(connection: sqlite3.Connection, siren: str) -> str | None:
    row = connection.execute(
        "SELECT code_insee FROM siren_insee WHERE siren = ?", (siren,)
    ).fetchone()
    return row["code_insee"] if row else None


async def commune(client: httpx.AsyncClient, code_insee: str) -> dict:
    response = await client.get(
        f"{BASE_URL}/communes/{code_insee}", params={"fields": "nom,surface,centre"}
    )
    response.raise_for_status()
    return response.json()
