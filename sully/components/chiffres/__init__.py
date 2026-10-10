from ...context import Context, Result
from ...sources import api_collectivites
from ..registry import component


def euros(montant) -> str:
    return f"{round(montant):,}".replace(",", " ") + " €"


@component(name="chiffres")
async def collect(context: Context) -> Result | None:
    if context.connection is None:
        return None
    siren = context.fiche.siren
    par_source = {
        ligne["source"]: (ligne["montant"] or 0, ligne["projets"])
        for ligne in api_collectivites.totaux_par_source(context.connection, siren)
    }
    if not par_source:
        return None

    par_annee = api_collectivites.totaux_par_annee(context.connection, siren)
    datees = [ligne for ligne in par_annee if ligne["annee"] is not None]
    sans_date = sum(
        ligne["financements"] for ligne in par_annee if ligne["annee"] is None
    )
    annees = [ligne["annee"] for ligne in datees]

    cofinancement = api_collectivites.cofinancement(context.connection, siren)
    cout = cofinancement["cout"] or 0
    taux = cofinancement["montant"] / cout if cout else None

    montants = {source: montant for source, (montant, _) in par_source.items()}
    total = sum(montants.values())
    detr = montants.get("DETR", 0)
    dsil = montants.get("DSIL", 0)
    fonds_vert = montants.get("Fonds Vert", 0)
    projets = sum(n for _, n in par_source.values())

    return Result(
        data={
            "periode": f"{annees[0]} – {annees[-1]}" if annees else "",
            "tuiles": [
                (
                    euros(total),
                    "reçus, tous financeurs",
                    str(projets),
                    "projets financés",
                ),
                (euros(detr), "de DETR", euros(dsil), "de DSIL"),
                (
                    euros(fonds_vert),
                    "de Fonds vert",
                    euros(total - detr - dsil - fonds_vert),
                    "autres financeurs",
                ),
                (
                    euros(cout),
                    "de coût des projets renseignés",
                    f"{taux:.0%}".replace("%", " %") if taux else "—",
                    "de taux de financement",
                ),
            ],
            "annees": annees,
            "montants": [ligne["montant"] or 0 for ligne in datees],
            "sans_date": sans_date,
            "financeurs": [
                {"nom": source, "montant": montant}
                for source, montant in montants.items()
            ],
        }
    )
