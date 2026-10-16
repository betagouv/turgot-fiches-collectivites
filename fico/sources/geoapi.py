"""geo.api.gouv.fr : les communes, avec leur population, leur superficie et leurs
rattachements (EPCI, département, région), noms compris.

Les collectivités d'outre-mer hors départements n'ont pas de SIREN : elles sont
écartées.

https://geo.api.gouv.fr/decoupage-administratif/communes
"""

import httpx

from . import base, collectivites
from .registry import Schedule, source

URL = "https://geo.api.gouv.fr/communes"
FIELDS = "nom,code,siren,population,surface,codesPostaux,epci,departement,region"

COLUMNS = (
    "siren",
    "famille",
    "nom",
    "type",
    "code_insee",
    "population",
    "superficie",
    "codes_postaux",
    "code_epci",
    "nom_epci",
    "code_departement",
    "nom_departement",
    "code_region",
    "nom_region",
)

INSERT = f"""
INSERT INTO collectivite ({", ".join(COLUMNS)})
VALUES ({", ".join(f"%({c})s" for c in COLUMNS)})
"""


def _row(commune: dict) -> dict:
    epci = commune.get("epci") or {}
    departement = commune.get("departement") or {}
    region = commune.get("region") or {}
    surface = commune.get("surface")
    return {
        "siren": commune["siren"],
        "famille": collectivites.COMMUNE,
        "nom": commune["nom"],
        "type": "COM",
        "code_insee": commune["code"],
        "population": commune.get("population"),
        # geo.api.gouv.fr gives hectares.
        "superficie": surface / 100 if surface is not None else None,
        "codes_postaux": commune.get("codesPostaux") or [],
        "code_epci": epci.get("code"),
        "nom_epci": epci.get("nom"),
        "code_departement": departement.get("code"),
        "nom_departement": departement.get("nom"),
        "code_region": region.get("code"),
        "nom_region": region.get("nom"),
    }


@source(
    name="geoapi",
    label="geo.api.gouv.fr : communes, population, superficie, rattachements",
    schedule=Schedule.MONTHLY,
    schema=collectivites.SCHEMA,
)
def fetch(client: httpx.Client, connection: base.Connection) -> str:
    response = client.get(URL, params={"fields": FIELDS})
    response.raise_for_status()
    communes = response.json()
    rows = [_row(c) for c in communes if c.get("siren")]
    with connection.transaction():
        connection.execute(
            "DELETE FROM collectivite WHERE famille = %s", (collectivites.COMMUNE,)
        )
        written = base.upsert(connection, INSERT, rows)
    return f"{written} commune(s), {len(communes) - written} sans SIREN écartée(s)"
