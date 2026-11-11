from ....context import Context
from ....sources import api_collectivites
from ... import financements
from ...formats import euros, number, percent, text
from ...registry import component
from ...table import Table


@component(
    description="Total reçu, nombre de projets, coût des projets et taux de "
    "financement, tous financeurs ou pour un seul, sur les six dernières années "
    "révolues ou depuis l'année since.",
    width="1/4",
)
def synthese(
    context: Context, since: int | None = None, financeur: str | None = None
) -> Table:
    connection, siren = context.connection, context.fiche.siren
    years = financements.years(since)
    totaux = api_collectivites.totaux(connection, siren, years, financeur)
    cofinancement = api_collectivites.cofinancement(connection, siren, years, financeur)
    cout = cofinancement["cout"] or 0

    rows = []
    if totaux["projets"]:
        rows = [
            [text("reçus"), euros(totaux["montant"])],
            [text("projets financés"), number(totaux["projets"])],
            [text("de coût des projets renseignés"), euros(cout)],
            [
                text("de taux de financement"),
                percent(cofinancement["montant"] / cout if cout else None),
            ],
        ]
    return Table(
        header=f"{years[0]} – {years[-1]}",
        title=financeur or "Tous financeurs",
        columns=["Indicateur", "Valeur"],
        rows=rows,
        empty="Aucun financement",
    )
