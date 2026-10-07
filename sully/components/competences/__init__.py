from ...context import Context, Result
from ..registry import component


@component(name="competences")
async def collect(context: Context) -> Result | None:
    competences = context.fiche.competences
    if not competences:
        return None
    return Result(data=[{"nom": c.nom} for c in competences])
