from ...context import Context, Result
from ...sources import subventions
from ..registry import component


def _euros(montant) -> str:
    return f"{round(montant):,}".replace(",", " ") + " €"


@component(name="subventions")
async def collect(context: Context) -> Result | None:
    if context.connection is None:
        return None
    lignes = []
    for ligne in subventions.par_siren(context.connection, context.fiche.siren):
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
    return Result(data=lignes) if lignes else None
