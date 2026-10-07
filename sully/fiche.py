import re
from datetime import UTC, datetime

import httpx

from . import blocs as registre
from .contexte import Contexte
from .rendu import typst
from .sources import base, geo
from .sources.referentiel import COMMUNE, Fiche, NotFound, Referentiel

SOURCE = "Sources : API Référentiel Collectivités (alpha) et geo.api.gouv.fr"

CODE_INSEE = re.compile(r"\d{5}|2[AB]\d{3}")
SIREN = re.compile(r"\d{9}")


class IdentifiantInvalide(Exception):
    pass


async def resolve(client: httpx.AsyncClient, identifiant: str) -> Fiche:
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
    index = await geo.siren_index(client)
    code_insee = index.get(identifiant)
    if code_insee is None:
        raise NotFound(identifiant)
    return await referentiel.commune(code_insee)


async def collect(
    client: httpx.AsyncClient, identifiant: str, blocs: tuple[str, ...] = registre.NOMS
) -> tuple[dict, dict]:
    fiche = await resolve(client, identifiant)
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
