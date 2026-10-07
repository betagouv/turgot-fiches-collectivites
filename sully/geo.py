"""Client for geo.api.gouv.fr: surfaces, contours, and the SIREN index.

The Référentiel API addresses communes by INSEE code only, so a SIREN entry
point needs the index built here. Groupements need no index: they are addressed
by SIREN upstream.
"""

import json
from pathlib import Path

import httpx

BASE_URL = "https://geo.api.gouv.fr"
CACHE_PATH = Path(__file__).parent.parent / ".cache" / "siren_to_insee.json"


async def _get(client: httpx.AsyncClient, path: str, **params):
    response = await client.get(f"{BASE_URL}{path}", params=params)
    response.raise_for_status()
    return response.json()


async def siren_index(
    client: httpx.AsyncClient, refresh: bool = False
) -> dict[str, str]:
    if CACHE_PATH.exists() and not refresh:
        return json.loads(CACHE_PATH.read_text())
    communes = await _get(client, "/communes", fields="code,siren")
    index = {c["siren"]: c["code"] for c in communes if c.get("siren")}
    CACHE_PATH.parent.mkdir(parents=True, exist_ok=True)
    CACHE_PATH.write_text(json.dumps(index))
    return index


async def commune(client: httpx.AsyncClient, code_insee: str) -> dict:
    return await _get(client, f"/communes/{code_insee}", fields="nom,surface,centre")


async def contours_departement(client: httpx.AsyncClient, code: str) -> dict:
    return await _get(
        client,
        f"/departements/{code}/communes",
        fields="nom,code,population,contour",
        format="geojson",
        geometry="contour",
    )


async def contours_epci(client: httpx.AsyncClient, siren: str) -> dict:
    return await _get(
        client,
        f"/epcis/{siren}/communes",
        fields="nom,code,population,contour",
        format="geojson",
        geometry="contour",
    )
