from .....context import Context, Result
from .....sources import contours
from .....sources.collectivites import COMMUNE
from ....registry import component
from .. import carte


@component(
    description="Carte des communes du département de la commune, colorées par "
    "taux de financement.",
    width="1/2",
)
def collect(context: Context) -> Result | None:
    fiche = context.fiche
    if fiche.famille != COMMUNE:
        return None
    geojson = contours.par_departement(context.connection, fiche.code_departement)
    return carte(context, "Département", geojson)
