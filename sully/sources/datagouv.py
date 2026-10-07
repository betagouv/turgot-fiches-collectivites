"""Accès au catalogue data.gouv.fr, partagé par les sources qui y puisent."""

import httpx

API_URL = "https://www.data.gouv.fr/api/1/datasets"


def resources(client: httpx.Client, dataset: str) -> list[dict]:
    response = client.get(f"{API_URL}/{dataset}/")
    response.raise_for_status()
    return [
        r
        for r in response.json().get("resources", [])
        if r.get("format", "").lower() == "csv"
    ]


def download(client: httpx.Client, url: str) -> str:
    response = client.get(url, follow_redirects=True)
    response.raise_for_status()
    return response.content.decode("utf-8-sig", errors="replace")
