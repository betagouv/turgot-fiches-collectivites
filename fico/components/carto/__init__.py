"""Cartes choroplèthes : les communes d'un territoire colorées selon une valeur,
d'après une échelle de seuils."""

import math
from collections.abc import Callable
from dataclasses import dataclass
from itertools import pairwise

from ...render.table import Table
from ..formats import Display

COULEUR_FOCUS = "#000000"
COULEUR_SANS_DONNEE = "#e5e5e5"
VIEWBOX_MARGIN = 0.01
STROKE_RATIO = 0.0015


@dataclass(frozen=True)
class Echelle:
    """`couleurs` has one more entry than `seuils`: below the first, between
    each pair, above the last."""

    titre: str
    couleurs: tuple[str, ...]
    seuils: tuple[float, ...]
    format: Callable[[float | None], Display]


@dataclass
class LegendStep:
    color: str
    label: str


@dataclass
class Legend:
    title: str
    steps: list[LegendStep]
    no_data: LegendStep
    focus: LegendStep


@dataclass
class Carte:
    titre: str
    projected: dict
    scale: float
    communes: int
    viewbox: list[float]
    stroke: float
    legend: Legend
    focus: str


def _legend(echelle: Echelle) -> Legend:
    bornes = [None, *echelle.seuils, None]
    steps = []
    for color, (bas, haut) in zip(echelle.couleurs, pairwise(bornes), strict=True):
        if bas is None:
            label = f"< {echelle.format(haut).label}"
        elif haut is None:
            label = f"≥ {echelle.format(bas).label}"
        else:
            label = f"{echelle.format(bas).label} à {echelle.format(haut).label}"
        steps.append(LegendStep(color, label))
    return Legend(
        title=echelle.titre,
        steps=steps,
        no_data=LegendStep(COULEUR_SANS_DONNEE, "n.c."),
        focus=LegendStep(COULEUR_FOCUS, "cette commune"),
    )


def _teinte(echelle: Echelle, valeur: float) -> str:
    for rang, seuil in enumerate(echelle.seuils):
        if valeur < seuil:
            return echelle.couleurs[rang]
    return echelle.couleurs[-1]


def _colorise(geojson: dict, valeurs: dict[str, float], echelle: Echelle) -> None:
    """The map stays the same whichever commune the fiche is about: renderers
    outline that one from `Carte.focus`."""
    for feature in geojson["features"]:
        proprietes = feature["properties"]
        code = proprietes.get("code")
        connue = valeurs.get(code)
        feature["properties"] = {
            "code": code,
            "nom": proprietes.get("nom", ""),
            "valeur": echelle.format(connue),
            "couleur": COULEUR_SANS_DONNEE
            if connue is None
            else _teinte(echelle, connue),
        }


def choroplethe(
    titre: str,
    geojson: dict,
    valeurs: dict[str, float],
    echelle: Echelle,
    focus: str,
) -> Carte:
    """Colour, project and frame the communes of `geojson` by their value in
    `valeurs`, keyed by code INSEE."""
    _colorise(geojson, valeurs, echelle)
    scale, viewbox = _project(geojson)
    return Carte(
        titre=titre,
        projected=geojson,
        scale=scale,
        communes=len(geojson["features"]),
        viewbox=viewbox,
        stroke=max(viewbox[2], viewbox[3]) * STROKE_RATIO,
        legend=_legend(echelle),
        focus=focus,
    )


def _points(coordinates):
    if isinstance(coordinates[0], (int, float)):
        yield coordinates
    else:
        for part in coordinates:
            yield from _points(part)


def _project(geojson: dict) -> tuple[float, list[float]]:
    """Project in place and return the longitude scale and the framing viewbox.

    mercator frames every map in a square and pins it to the top, so a wide
    territory fills only a strip: the projection and its exact extent are
    computed here, and mercator only draws. Scaling longitudes by the cosine of
    the central latitude keeps shapes undistorted at this scale.
    """
    latitudes = [
        point[1]
        for feature in geojson["features"]
        for point in _points(feature["geometry"]["coordinates"])
    ]
    scale = math.cos(math.radians((min(latitudes) + max(latitudes)) / 2))
    xs, ys = [], []
    for feature in geojson["features"]:
        for point in _points(feature["geometry"]["coordinates"]):
            point[0] *= scale
            xs.append(point[0])
            ys.append(point[1])
    width, height = max(xs) - min(xs), max(ys) - min(ys)
    margin = max(width, height) * VIEWBOX_MARGIN
    # SVG's y axis points down, hence the negated latitude.
    viewbox = [
        min(xs) - margin,
        -max(ys) - margin,
        width + 2 * margin,
        height + 2 * margin,
    ]
    return scale, viewbox


def _unproject(coordinates, scale: float):
    if isinstance(coordinates[0], (int, float)):
        return [coordinates[0] / scale, *coordinates[1:]]
    return [_unproject(part, scale) for part in coordinates]


def table(carte: Carte) -> Table:
    return Table(
        columns=["Code INSEE", "Commune", carte.legend.title],
        rows=[
            [
                feature["properties"]["code"],
                feature["properties"]["nom"],
                feature["properties"]["valeur"].value,
            ]
            for feature in carte.projected["features"]
        ],
    )


def geojson(carte: Carte) -> dict:
    """The map's communes back in longitude and latitude, with their raw value."""
    features = []
    for feature in carte.projected["features"]:
        proprietes = feature["properties"]
        geometry = feature["geometry"]
        features.append(
            {
                "type": "Feature",
                "properties": {
                    "code": proprietes["code"],
                    "nom": proprietes["nom"],
                    "valeur": proprietes["valeur"].value,
                },
                "geometry": {
                    "type": geometry["type"],
                    "coordinates": _unproject(geometry["coordinates"], carte.scale),
                },
            }
        )
    return {"type": "FeatureCollection", "features": features}
