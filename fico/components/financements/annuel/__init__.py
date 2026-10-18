import math
from dataclasses import dataclass
from datetime import UTC, datetime

from ....context import Context, Result
from ....render.table import Table
from ....sources import api_collectivites
from ...formats import Display, compact_euros
from ...registry import component

TICK_COUNT = 4
YEARS = 5


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
class Annuel:
    periode: str
    bars: list[Bar]
    ticks: list[Tick]
    sans_date: int


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


def table(data: Annuel) -> Table:
    return Table(
        columns=["Année", "Montant reçu"],
        rows=[[bar.annee, bar.montant.value] for bar in data.bars],
    )


@component(
    description="Montants reçus par année, sur les cinq dernières années révolues.",
    width="1/2",
    table=table,
)
def collect(context: Context) -> Result | None:
    par_annee = api_collectivites.totaux_par_annee(
        context.connection, context.fiche.siren
    )
    if not par_annee:
        return None

    sans_date = sum(
        ligne["financements"] for ligne in par_annee if ligne["annee"] is None
    )
    # The current year is still running: its total would look like a drop.
    current_year = datetime.now(UTC).year
    window = range(current_year - YEARS, current_year)
    by_year = {ligne["annee"]: ligne["montant"] or 0 for ligne in par_annee}
    histogram = [(annee, by_year.get(annee, 0)) for annee in window]
    top, ticks = _scale([montant for _, montant in histogram])

    annuel = Annuel(
        periode=f"{window[0]} – {window[-1]}",
        bars=[
            Bar(annee, compact_euros(montant), montant / top)
            for annee, montant in histogram
        ],
        ticks=ticks,
        sans_date=sans_date,
    )
    return Result(data=annuel)
