from ....context import Context
from ....sources import api_collectivites
from ... import financements
from ...formats import compact_euros, plain
from ...registry import component
from ...table import Table


@component(
    description="Montants reçus par année révolue, sur les six dernières ou "
    "depuis l'année since.",
    width="1/2",
)
def annuel(context: Context, since: int | None = None) -> Table:
    years = financements.years(since)
    totals = api_collectivites.totaux_by_annee(context.fiche.siren, years)
    by_year = {total["annee"]: total["montant"] or 0 for total in totals}
    montants = {year: by_year.get(year, 0) for year in years}
    rows = []
    if any(montants.values()):
        rows = [
            [plain(year), compact_euros(montant)] for year, montant in montants.items()
        ]
    return Table(
        header=f"{years[0]} – {years[-1]}",
        title="Montants reçus par année",
        columns=["Année", "Montant reçu"],
        rows=rows,
        empty="Aucun financement",
    )
