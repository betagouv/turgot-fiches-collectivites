from ...context import Context, Result
from ...sources import programmes
from ...sources.referentiel import COMMUNE
from ..registry import Placement, component


@component(name="programmes", placement=Placement.CARD)
async def collect(context: Context) -> Result | None:
    if context.fiche.famille != COMMUNE or context.connection is None:
        return None
    noms = {p.code: p.nom for p in programmes.PROGRAMMES}
    return Result(
        data=[
            (noms.get(ligne["programme"], ligne["programme"]), ligne["depuis"] or "")
            for ligne in programmes.de_commune(
                context.connection, context.fiche.code_insee
            )
        ]
    )
