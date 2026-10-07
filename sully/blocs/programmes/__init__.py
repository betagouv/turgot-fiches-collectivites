from pathlib import Path

from ...contexte import Contexte, Resultat
from ...sources import programmes
from ...sources.referentiel import COMMUNE

NOM = "programmes"
PLACEMENT = "cartouche"
DOSSIER = Path(__file__).parent


async def collecte(contexte: Contexte) -> Resultat | None:
    if contexte.fiche.famille != COMMUNE or contexte.connection is None:
        return None
    noms = {p.code: p.nom for p in programmes.PROGRAMMES}
    return Resultat(
        donnees=[
            (noms.get(ligne["programme"], ligne["programme"]), ligne["depuis"] or "")
            for ligne in programmes.de_commune(
                contexte.connection, contexte.fiche.code_insee
            )
        ]
    )
