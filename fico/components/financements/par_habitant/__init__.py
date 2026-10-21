from datetime import UTC, datetime

from ....context import Context
from ....sources import api_collectivites, base, collectivites
from ....sources.collectivites import COMMUNE, Fiche
from ...formats import euros, number, plain, text
from ...registry import component
from ...table import Table

YEARS = 6
COLUMNS = [
    "Rang",
    "Code",
    "Collectivité",
    "Population",
    "Montant reçu",
    "Moyenne annuelle par habitant",
]


def _pairs(connection: base.Connection, fiche: Fiche) -> tuple[str, list[dict]] | None:
    """What the collectivité compares to, named, with their siren, nom and
    population."""
    if fiche.famille == COMMUNE:
        if not fiche.code_epci:
            return None
        communes = collectivites.communes_of_epci(connection, fiche.code_epci)
        return f"communes de {fiche.nom_epci}", communes
    if fiche.type not in collectivites.EPCI_A_FISCALITE_PROPRE:
        return None
    epci = collectivites.epci_of_departement(connection, fiche.code_departement)
    return f"EPCI à fiscalité propre, {fiche.nom_departement}", epci


@component(
    description="Montant reçu en moyenne par an et par habitant, comparé : une "
    "commune aux autres communes de son intercommunalité, un EPCI aux autres "
    "EPCI à fiscalité propre du département ; sur les six dernières années "
    "révolues ou depuis l'année since.",
)
def par_habitant(
    context: Context, since: int | None = None, financeur: str | None = None
) -> Table | None:
    fiche = context.fiche
    pairs = _pairs(context.connection, fiche)
    if pairs is None:
        return None
    perimetre, peers = pairs

    # The current year is still running: it would pull the average down.
    current_year = datetime.now(UTC).year
    years = range(since or current_year - YEARS, current_year)
    montants = api_collectivites.montants_by_siren(
        context.connection,
        [peer["siren"] for peer in peers],
        years,
        financeur,
    )
    rows = [
        {**peer, "montant": montants.get(peer["siren"], 0)}
        for peer in peers
        if peer["population"]
    ]
    if not any(row["montant"] for row in rows):
        rows = []
    rows.sort(key=lambda row: row["montant"] / row["population"], reverse=True)
    focus = next(
        (index for index, row in enumerate(rows) if row["siren"] == fiche.siren), None
    )
    year_count = max(len(years), 1)

    subject = financeur or "Montants reçus"
    return Table(
        header=f"{years[0]} – {years[-1]}" if years else f"depuis {since}",
        title=f"{subject}, moyenne annuelle par habitant, {perimetre}",
        columns=COLUMNS,
        rows=[
            [
                plain(rank),
                text(row.get("code_insee") or row["siren"]),
                text(row["nom"]),
                number(row["population"]),
                euros(row["montant"]),
                euros(row["montant"] / row["population"] / year_count),
            ]
            for rank, row in enumerate(rows, start=1)
        ],
        empty="Aucun financement",
        focus=focus,
    )
