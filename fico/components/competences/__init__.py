from ...context import Context
from ...sources import collectivites
from ..formats import text
from ..registry import component
from ..table import Table


@component(
    description="Compétences exercées par un groupement, selon la nomenclature "
    "Banatic.",
)
def competences(context: Context) -> Table | None:
    noms = collectivites.competences(context.connection, context.fiche.siren)
    if not noms:
        return None
    return Table(
        titre=f"Compétences ({len(noms)})",
        columns=["Compétence"],
        rows=[[text(nom)] for nom in noms],
    )
