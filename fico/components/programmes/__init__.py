from datetime import date

from ...sources.collectivites import COMMUNE, Fiche
from ...sources.programmes import BY_CODE, for_commune
from ..formats import Display, long_date, text
from ..registry import component
from ..table import Table


def _depuis(value: date | None) -> Display:
    if value is None:
        return Display(None, "")
    depuis = long_date(value)
    return Display(depuis.value, f"depuis le {depuis.label}")


@component(
    description="Programmes nationaux dont relève la commune : Action cœur de "
    "ville, Petites villes de demain, Territoires d'industrie, Villages d'avenir.",
    width="1/2",
)
def programmes(fiche: Fiche) -> Table | None:
    if fiche.famille != COMMUNE:
        return None
    rows = for_commune(fiche.code_insee)
    return Table(
        title="Programmes",
        columns=["Programme", "Depuis"],
        rows=[
            [text(BY_CODE[row["programme"]].nom), _depuis(row["depuis"])]
            for row in rows
        ],
        empty="Aucun programme national recensé.",
    )
