import math
from dataclasses import dataclass
from datetime import UTC, datetime

from ...context import Context, Result
from ...sources import api_collectivites
from ..formats import Display, compact_euros, euros, number, percent
from ..registry import component

TICK_COUNT = 4
HISTOGRAM_YEARS = 5


@dataclass
class Tile:
    main: Display
    main_caption: str
    secondary: Display
    secondary_caption: str


@dataclass
class Bar:
    annee: int
    montant: Display
    share: float


@dataclass
class Tick:
    montant: Display
    share: float


@dataclass
class Financeur:
    financeur: str
    montant: Display
    share: float


@dataclass
class Chiffres:
    periode: str
    tiles: list[Tile]
    histogram_periode: str
    bars: list[Bar]
    ticks: list[Tick]
    sans_date: int
    financeurs: list[Financeur]


def _nice_step(maximum: float) -> float:
    raw = maximum / TICK_COUNT
    magnitude = 10 ** math.floor(math.log10(raw))
    for factor in (1, 2, 2.5, 5, 10):
        if raw <= factor * magnitude:
            return factor * magnitude
    return 10 * magnitude


def _scale(values: list[float]) -> tuple[float, list[Tick]]:
    maximum = max(values, default=0)
    if maximum <= 0:
        return 1, [Tick(compact_euros(0), 0)]
    step = _nice_step(maximum)
    top = math.ceil(maximum / step) * step
    ticks = [
        Tick(compact_euros(step * i), step * i / top)
        for i in range(round(top / step) + 1)
    ]
    return top, ticks


@component(
    name="chiffres",
    description="Financements reçus : totaux par dispositif, montants des cinq "
    "dernières années révolues, répartition par financeur.",
)
async def collect(context: Context) -> Result | None:
    siren = context.fiche.siren
    par_source = api_collectivites.totaux_par_source(context.connection, siren)
    if not par_source:
        return None

    par_annee = api_collectivites.totaux_par_annee(context.connection, siren)
    datees = [ligne for ligne in par_annee if ligne["annee"] is not None]
    sans_date = sum(
        ligne["financements"] for ligne in par_annee if ligne["annee"] is None
    )
    # The current year is still running: its total would look like a drop.
    current_year = datetime.now(UTC).year
    window = range(current_year - HISTOGRAM_YEARS, current_year)
    by_year = {ligne["annee"]: ligne["montant"] or 0 for ligne in datees}
    histogram = [(annee, by_year.get(annee, 0)) for annee in window]
    top, ticks = _scale([montant for _, montant in histogram])

    cofinancement = api_collectivites.cofinancement(context.connection, siren)
    cout = cofinancement["cout"] or 0
    taux = cofinancement["montant"] / cout if cout else None

    montants = {ligne["source"]: ligne["montant"] or 0 for ligne in par_source}
    total = sum(montants.values())
    detr = montants.get("DETR", 0)
    dsil = montants.get("DSIL", 0)
    fonds_vert = montants.get("Fonds Vert", 0)
    projets = sum(ligne["projets"] for ligne in par_source)

    chiffres = Chiffres(
        periode=f"{datees[0]['annee']} – {datees[-1]['annee']}" if datees else "",
        tiles=[
            Tile(
                euros(total),
                "reçus, tous financeurs",
                number(projets),
                "projets financés",
            ),
            Tile(euros(detr), "de DETR", euros(dsil), "de DSIL"),
            Tile(
                euros(fonds_vert),
                "de Fonds vert",
                euros(total - detr - dsil - fonds_vert),
                "autres financeurs",
            ),
            Tile(
                euros(cout),
                "de coût des projets renseignés",
                percent(taux),
                "de taux de financement",
            ),
        ],
        histogram_periode=f"{window[0]} – {window[-1]}",
        bars=[
            Bar(annee, compact_euros(montant), montant / top)
            for annee, montant in histogram
        ],
        ticks=ticks,
        sans_date=sans_date,
        financeurs=[
            Financeur(source, compact_euros(montant), montant / total if total else 0)
            for source, montant in montants.items()
        ],
    )
    return Result(data=chiffres)
