"""Choroplèthes du taux de financement des projets que porte chaque commune."""

from ....context import Context, Result
from ....sources import api_collectivites
from ...formats import percent
from .. import Echelle, choroplethe

ECHELLE = Echelle(
    titre="Taux de financement",
    couleurs=("#ececfe", "#cacafb", "#9a9af8", "#6a6af4", "#000091"),
    seuils=(0.15, 0.25, 0.35, 0.50),
    format=percent,
)


def carte(context: Context, titre: str, geojson: dict) -> Result | None:
    if not geojson["features"]:
        return None
    codes = [f["properties"]["code"] for f in geojson["features"]]
    taux = api_collectivites.taux_par_commune(context.connection, codes)
    focus = context.fiche.code_insee
    return Result(data=choroplethe(titre, geojson, taux, ECHELLE, focus))
