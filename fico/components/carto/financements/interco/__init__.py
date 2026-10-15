from .....context import Context, Result
from .....sources import contours
from .....sources.collectivites import COMMUNE
from ....registry import component
from .. import carte


@component(
    description="Carte des communes de l'intercommunalité de la commune, colorées "
    "par taux de financement.",
    width="1/2",
)
def collect(context: Context) -> Result | None:
    fiche = context.fiche
    if fiche.famille != COMMUNE or not fiche.code_epci:
        return None
    geojson = contours.par_epci(context.connection, fiche.code_epci)
    return carte(context, "Intercommunalité", geojson)
