from datetime import UTC, datetime

from ....context import Context
from ....sources import api_collectivites
from ...formats import compact_euros, plain
from ...registry import component
from ...table import Table

YEARS = 5


@component(
    description="Montants reçus par année révolue, sur les cinq dernières ou "
    "depuis l'année since.",
    width="1/2",
)
def annuel(context: Context, since: int | None = None) -> Table:
    totals = api_collectivites.totaux_by_annee(
        context.connection, context.fiche.siren, since
    )
    # The current year is still running: its total would look like a drop.
    current_year = datetime.now(UTC).year
    window = range(since or current_year - YEARS, current_year)

    undated = sum(total["financements"] for total in totals if total["annee"] is None)
    by_year = {total["annee"]: total["montant"] or 0 for total in totals}
    montants = {year: by_year.get(year, 0) for year in window}
    rows = []
    if any(montants.values()):
        rows = [
            [plain(year), compact_euros(montant)] for year, montant in montants.items()
        ]
    return Table(
        header=f"{window[0]} – {window[-1]}" if window else f"depuis {since}",
        title="Montants reçus par année",
        columns=["Année", "Montant reçu"],
        rows=rows,
        empty="Aucun financement",
        note=f"{undated} financement(s) sans date d'attribution, non représenté(s)."
        if undated
        else "",
    )
