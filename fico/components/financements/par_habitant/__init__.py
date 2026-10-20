from dataclasses import dataclass
from datetime import UTC, datetime
from enum import StrEnum

from ....context import Context, Result
from ....render.table import Table
from ....sources import api_collectivites, base, collectivites
from ....sources.collectivites import COMMUNE, Fiche
from ...formats import Display, euros, number
from ...registry import component

HIGHLIGHTED = 3
YEARS = 6


class Accent(StrEnum):
    TOP = "top"
    BOTTOM = "bottom"
    FOCUS = "focus"
    NEIGHBOUR = "neighbour"
    NONE = ""


@dataclass
class Barre:
    rang: int
    code: str
    nom: str
    population: Display
    montant: Display
    par_habitant: Display
    share: float
    accent: Accent


@dataclass
class ParHabitant:
    titre: str
    periode: str
    barres: list[Barre]


def _accent(rang: int, count: int, focus: int | None) -> Accent:
    if rang == focus:
        return Accent.FOCUS
    if rang <= HIGHLIGHTED:
        return Accent.TOP
    if rang > count - HIGHLIGHTED:
        return Accent.BOTTOM
    if focus is not None and abs(rang - focus) == 1:
        return Accent.NEIGHBOUR
    return Accent.NONE


def table(data: ParHabitant) -> Table:
    return Table(
        columns=[
            "Rang",
            "Code",
            "Collectivité",
            "Population",
            "Montant reçu",
            "Moyenne annuelle par habitant",
        ],
        rows=[
            [
                barre.rang,
                barre.code,
                barre.nom,
                barre.population.value,
                barre.montant.value,
                barre.par_habitant.value,
            ]
            for barre in data.barres
        ],
    )


def _pairs(connection: base.Connection, fiche: Fiche) -> tuple[str, list[dict]] | None:
    """What the collectivité compares to, named, with their siren, nom and
    population."""
    if fiche.famille == COMMUNE:
        if not fiche.code_epci:
            return None
        communes = collectivites.communes_de_epci(connection, fiche.code_epci)
        return f"communes de {fiche.nom_epci}", communes
    if fiche.type not in collectivites.EPCI_A_FISCALITE_PROPRE:
        return None
    epci = collectivites.epci_du_departement(connection, fiche.code_departement)
    return f"EPCI à fiscalité propre, {fiche.nom_departement}", epci


@component(
    description="Montant reçu en moyenne par an et par habitant, comparé : une "
    "commune aux autres communes de son intercommunalité, un EPCI aux autres "
    "EPCI à fiscalité propre du département ; sur les six dernières années "
    "révolues ou depuis l'année since.",
    table=table,
)
def collect(
    context: Context, since: int | None = None, financeur: str | None = None
) -> Result | None:
    fiche = context.fiche
    pairs = _pairs(context.connection, fiche)
    if pairs is None:
        return None
    perimetre, voisines = pairs

    # The current year is still running: it would pull the average down.
    current_year = datetime.now(UTC).year
    annees = range(since or current_year - YEARS, current_year)
    montants = api_collectivites.montants_par_siren(
        context.connection,
        [voisine["siren"] for voisine in voisines],
        annees,
        financeur,
    )
    rows = [
        {**voisine, "montant": montants.get(voisine["siren"], 0)}
        for voisine in voisines
        if voisine["population"]
    ]

    rows.sort(key=lambda row: row["montant"] / row["population"], reverse=True)
    maximum = max((row["montant"] / row["population"] for row in rows), default=0)
    focus = next(
        (rang for rang, row in enumerate(rows, start=1) if row["siren"] == fiche.siren),
        None,
    )

    barres = []
    for rang, row in enumerate(rows, start=1):
        par_habitant = row["montant"] / row["population"]
        barres.append(
            Barre(
                rang=rang,
                code=row.get("code_insee") or row["siren"],
                nom=row["nom"],
                population=number(row["population"]),
                montant=euros(row["montant"]),
                par_habitant=euros(par_habitant / max(len(annees), 1)),
                share=par_habitant / maximum if maximum else 0,
                accent=_accent(rang, len(rows), focus),
            )
        )

    sujet = financeur or "Montants reçus"
    return Result(
        data=ParHabitant(
            titre=f"{sujet}, moyenne annuelle par habitant, {perimetre}",
            periode=f"{annees[0]} – {annees[-1]}" if annees else f"depuis {since}",
            barres=barres,
        )
    )
