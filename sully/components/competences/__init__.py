from dataclasses import dataclass

from ...context import Context, Result
from ...sources import collectivites
from ..registry import component


@dataclass
class Competence:
    nom: str


@dataclass
class Competences:
    competences: list[Competence]


@component(
    name="competences",
    description="Compétences exercées par un groupement, selon la nomenclature "
    "Banatic.",
)
async def collect(context: Context) -> Result | None:
    noms = collectivites.competences(context.connection, context.fiche.siren)
    if not noms:
        return None
    return Result(data=Competences([Competence(nom) for nom in noms]))
