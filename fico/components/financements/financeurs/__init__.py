from ....context import Context
from ....sources import api_collectivites
from ...formats import compact_euros, text
from ...registry import component
from ...table import Table


@component(
    description="Répartition des financements reçus par financeur.",
    width="1/2",
)
def financeurs(context: Context, since: int | None = None) -> Table:
    totals = api_collectivites.totaux_by_source(
        context.connection, context.fiche.siren, since
    )
    return Table(
        title="Répartition par financeur",
        columns=["Financeur", "Montant reçu"],
        rows=[
            [text(total["source"]), compact_euros(total["montant"] or 0)]
            for total in totals
        ],
        empty="Aucun financement",
    )
