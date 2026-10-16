"""Choroplèthe du taux de financement des projets que porte chaque commune."""

from enum import StrEnum

from ....context import Context, Result
from ....sources import api_collectivites, contours
from ....sources.collectivites import COMMUNE
from ...formats import percent
from ...registry import component
from .. import Echelle, choroplethe, geojson, table

ECHELLE = Echelle(
    titre="Taux de financement",
    couleurs=("#ececfe", "#cacafb", "#9a9af8", "#6a6af4", "#000091"),
    seuils=(0.15, 0.25, 0.35, 0.50),
    format=percent,
)


class Perimeter(StrEnum):
    DEPARTEMENT = "departement"
    INTERCO = "interco"


@component(
    description="Communes du département ou de l'intercommunalité de la commune, "
    "colorées par taux de financement.",
    width="1/2",
    table=table,
    geojson=geojson,
)
def collect(context: Context, perimeter: Perimeter) -> Result | None:
    fiche = context.fiche
    if fiche.famille != COMMUNE:
        return None
    match perimeter:
        case Perimeter.DEPARTEMENT:
            titre = "Département"
            communes = contours.par_departement(
                context.connection, fiche.code_departement
            )
        case Perimeter.INTERCO:
            if not fiche.code_epci:
                return None
            titre = "Intercommunalité"
            communes = contours.par_epci(context.connection, fiche.code_epci)
    if not communes["features"]:
        return None
    codes = [f["properties"]["code"] for f in communes["features"]]
    taux = api_collectivites.taux_par_commune(context.connection, codes)
    carte = choroplethe(titre, communes, taux, ECHELLE, fiche.code_insee)
    return Result(data=carte)
