from datetime import UTC, datetime

import httpx

from . import blocs as registre
from .contexte import Contexte
from .rendu import typst
from .sources import base, geo
from .sources.referentiel import COMMUNE, Fiche, NotFound, Referentiel

SOURCE = "Sources : API Référentiel Collectivités (alpha) et geo.api.gouv.fr"


async def resolve(client: httpx.AsyncClient, siren: str) -> Fiche:
    """Trouve la collectivité derrière un SIREN.

    L'API amont adresse les groupements par SIREN, mais pas les communes :
    tenter le groupement d'abord réserve l'index aux seules communes.
    """
    referentiel = Referentiel(client)
    try:
        return await referentiel.groupement(siren)
    except NotFound:
        pass
    index = await geo.siren_index(client)
    code_insee = index.get(siren)
    if code_insee is None:
        raise NotFound(siren)
    return await referentiel.commune(code_insee)


async def collect(
    client: httpx.AsyncClient, siren: str, blocs: tuple[str, ...] = registre.NOMS
) -> tuple[dict, dict]:
    fiche = await resolve(client, siren)
    contexte = Contexte(
        client=client,
        fiche=fiche,
        connection=base.connect() if base.DB_PATH.exists() else None,
        blocs=blocs,
    )

    resultats = {}
    for nom in registre.NOMS:
        if nom not in blocs:
            continue
        resultat = await registre.PAR_NOM[nom].collecte(contexte)
        if resultat is not None:
            resultats[nom] = resultat

    entete = {
        "nom": fiche.nom,
        "libelle_type": "Commune" if fiche.famille == COMMUNE else fiche.type,
        "source": f"{SOURCE} — généré le {datetime.now(UTC):%d/%m/%Y}",
    }
    return entete, resultats


def render(entete: dict, resultats: dict) -> bytes:
    return typst.compile_fiche(entete, resultats)
