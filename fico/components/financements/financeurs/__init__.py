from ....context import Context
from ....sources import api_collectivites
from ... import financements
from ...formats import compact_euros, text
from ...registry import component
from ...table import Table


@component(
    description="Répartition des financements reçus par financeur, sur les six "
    "dernières années révolues ou depuis l'année since.",
    width="1/2",
)
def financeurs(context: Context, since: int | None = None) -> Table:
    years = financements.years(since)
    totals = api_collectivites.totaux_by_source(context.fiche.siren, years)
    return Table(
        header=f"{years[0]} – {years[-1]}",
        title="Répartition par financeur",
        columns=["Financeur", "Montant reçu"],
        rows=[
            [text(total["source"]), compact_euros(total["montant"] or 0)]
            for total in totals
        ],
        empty="Aucun financement",
    )
