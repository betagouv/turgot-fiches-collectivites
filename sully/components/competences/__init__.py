from dataclasses import dataclass

from ...context import Context, Result
from ..registry import component


@dataclass
class Competence:
    code: str
    nom: str


@dataclass
class Competences:
    competences: list[Competence]


@component(name="competences")
async def collect(context: Context) -> Result | None:
    competences = context.fiche.competences
    if not competences:
        return None
    return Result(data=Competences([Competence(c.code, c.nom) for c in competences]))
