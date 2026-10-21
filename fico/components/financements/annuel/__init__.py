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
    par_annee = api_collectivites.totaux_par_annee(
        context.connection, context.fiche.siren, since
    )
    # The current year is still running: its total would look like a drop.
    current_year = datetime.now(UTC).year
    window = range(since or current_year - YEARS, current_year)

    sans_date = sum(
        ligne["financements"] for ligne in par_annee if ligne["annee"] is None
    )
    by_year = {ligne["annee"]: ligne["montant"] or 0 for ligne in par_annee}
    montants = {annee: by_year.get(annee, 0) for annee in window}
    rows = []
    if any(montants.values()):
        rows = [
            [plain(annee), compact_euros(montant)]
            for annee, montant in montants.items()
        ]
    return Table(
        header=f"{window[0]} – {window[-1]}" if window else f"depuis {since}",
        titre="Montants reçus par année",
        columns=["Année", "Montant reçu"],
        rows=rows,
        vide="Aucun financement",
        note=f"{sans_date} financement(s) sans date d'attribution, non représenté(s)."
        if sans_date
        else "",
    )
