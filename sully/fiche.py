import re
import sqlite3
from datetime import UTC, datetime

import httpx

from .components import COMPONENTS
from .context import Context
from .render import typst
from .sources import base, geo
from .sources.referentiel import COMMUNE, Fiche, NotFound, Referentiel

SOURCE = (
    "Sources : API Référentiel Collectivités, geo.api.gouv.fr, "
    "contours et subventions publiés sur data.gouv.fr"
)

CODE_INSEE = re.compile(r"\d{5}|2[AB]\d{3}")
SIREN = re.compile(r"\d{9}")


class IdentifiantInvalide(Exception):
    pass


async def resolve(
    client: httpx.AsyncClient, identifiant: str, connection: sqlite3.Connection | None
) -> Fiche:
    """Trouve la collectivité derrière un code INSEE ou un SIREN.

    Un code INSEE désigne une commune et s'adresse directement. Un SIREN peut
    désigner l'une ou l'autre : l'API amont adresse les groupements par SIREN
    mais pas les communes, donc tenter le groupement d'abord réserve l'index
    aux seules communes.
    """
    referentiel = Referentiel(client)
    if CODE_INSEE.fullmatch(identifiant):
        return await referentiel.commune(identifiant)
    if not SIREN.fullmatch(identifiant):
        raise IdentifiantInvalide(
            f"{identifiant} n'est ni un code INSEE de commune (5 caractères) "
            f"ni un SIREN (9 chiffres)."
        )

    try:
        return await referentiel.groupement(identifiant)
    except NotFound:
        pass
    code_insee = (
        geo.code_insee_de(connection, identifiant) if connection is not None else None
    )
    if code_insee is None:
        raise NotFound(identifiant)
    return await referentiel.commune(code_insee)


async def collect(
    client: httpx.AsyncClient, identifiant: str, components
) -> tuple[dict, dict]:
    connection = base.connect() if base.DB_PATH.exists() else None
    fiche = await resolve(client, identifiant, connection)
    names = tuple(component.name for component in components)
    context = Context(
        client=client, fiche=fiche, connection=connection, components=names
    )

    results = {}
    for component in components:
        result = await component.collect(context)
        if result is not None:
            results[component.name] = result

    header = {
        "nom": fiche.nom,
        "libelle_type": "Commune" if fiche.famille == COMMUNE else fiche.type,
        "source": f"{SOURCE} — généré le {datetime.now(UTC):%d/%m/%Y}",
    }
    return header, results


def render(header: dict, results: dict) -> bytes:
    return typst.compile_fiche(header, results)


__all__ = ["COMPONENTS", "IdentifiantInvalide", "collect", "render", "resolve"]
