from ...context import Context, Result
from ...sources import api_collectivites
from ..registry import component


def _euros(montant) -> str:
    return f"{round(montant):,}".replace(",", " ") + " €"


@component(name="subventions")
async def collect(context: Context) -> Result | None:
    if context.connection is None:
        return None
    lignes = []
    for ligne in api_collectivites.financements_recus(
        context.connection, context.fiche.siren
    ):
        cout = ligne["budget_previsionnel"]
        montant = ligne["montant_attribue"]
        lignes.append(
            {
                "annee": str(ligne["annee"]) if ligne["annee"] else "—",
                "financeur": ligne["source"] or "—",
                "libelle": ligne["nom"] or "—",
                "cout": _euros(cout) if cout else "—",
                "montant": _euros(montant) if montant else "—",
                "taux": f"{montant / cout:.0%}".replace("%", " %")
                if cout and montant
                else "—",
            }
        )
    return Result(data=lignes) if lignes else None
