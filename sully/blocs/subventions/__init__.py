from pathlib import Path

from ...contexte import Contexte, Resultat
from ...sources import base

NOM = "subventions"
PLACEMENT = "section"
DOSSIER = Path(__file__).parent


def _euros(montant) -> str:
    return f"{round(montant):,}".replace(",", " ") + " €"


async def collecte(contexte: Contexte) -> Resultat | None:
    if contexte.connection is None:
        return None
    lignes = []
    for ligne in base.par_siren(contexte.connection, contexte.fiche.siren):
        cout = ligne["cout_total"]
        montant = ligne["montant_accorde"]
        lignes.append(
            {
                "annee": ligne["annee"],
                "dispositif": ligne["dispositif"],
                "libelle": ligne["libelle"] or "—",
                "cout": _euros(cout) if cout else "—",
                "montant": _euros(montant) if montant else "—",
                "taux": f"{montant / cout:.0%}".replace("%", " %")
                if cout and montant
                else "—",
            }
        )
    return Resultat(donnees=lignes) if lignes else None
