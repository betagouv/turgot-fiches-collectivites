from dataclasses import dataclass

from ...context import Context, Result
from ...sources import programmes
from ...sources.collectivites import COMMUNE
from ..formats import Display, long_date
from ..registry import component


@dataclass
class Programme:
    code: str
    nom: str
    depuis: Display


@dataclass
class Programmes:
    programmes: list[Programme]


@component(
    name="programmes",
    description="Programmes nationaux dont relève la commune : Action cœur de "
    "ville, Petites villes de demain, Territoires d'industrie, Villages d'avenir.",
    width="1/2",
)
async def collect(context: Context) -> Result | None:
    if context.fiche.famille != COMMUNE:
        return None
    rows = programmes.de_commune(context.connection, context.fiche.code_insee)
    return Result(
        data=Programmes(
            [
                Programme(
                    code=row["programme"],
                    nom=programmes.PAR_CODE[row["programme"]].nom,
                    depuis=long_date(row["depuis"]),
                )
                for row in rows
            ]
        )
    )
