from ....context import Context
from ....sources import api_collectivites
from ...formats import euros, number, percent, text
from ...registry import component
from ...table import Table


@component(
    description="Total reçu, nombre de projets, coût des projets et taux de "
    "financement, tous financeurs ou pour un seul.",
    width="1/4",
)
def synthese(
    context: Context, since: int | None = None, financeur: str | None = None
) -> Table:
    connection, siren = context.connection, context.fiche.siren
    totaux = api_collectivites.totaux(connection, siren, since, financeur)
    cofinancement = api_collectivites.cofinancement(connection, siren, since, financeur)
    cout = cofinancement["cout"] or 0
    first, last = totaux["first_year"], totaux["last_year"]

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
        header=f"{first} – {last}" if first else "",
        title=financeur or "Tous financeurs",
        columns=["Indicateur", "Valeur"],
        rows=rows,
        empty="Aucun financement",
    )
