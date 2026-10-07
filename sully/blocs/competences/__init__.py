from pathlib import Path

from ...contexte import Contexte, Resultat

NOM = "competences"
PLACEMENT = "section"
DOSSIER = Path(__file__).parent


async def collecte(contexte: Contexte) -> Resultat | None:
    competences = contexte.fiche.competences
    if not competences:
        return None
    return Resultat(donnees=[{"nom": c.nom} for c in competences])
