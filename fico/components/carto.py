"""Cartes choroplèthes : les communes d'un territoire colorées selon une valeur,
d'après une échelle de seuils."""

import math
from collections.abc import Callable
from dataclasses import dataclass
from itertools import pairwise

from ..render.table import Table
from .formats import Display

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
    """`territoire` keeps its longitudes and latitudes: renderers draw each point
    at (longitude × scale, latitude) and frame it with `viewbox`."""

    titre: str
    territoire: dict
    scale: float
    effectif: str
    viewbox: list[float]
    stroke: float
    legend: Legend
    focus: str


def _legend(echelle: Echelle, focus: str) -> Legend:
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
        focus=LegendStep(COULEUR_FOCUS, focus),
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
    unite: str = "communes",
    focus_label: str = "cette commune",
) -> Carte:
    """Colour and frame the features of `geojson` by their value in `valeurs`,
    keyed by their `code`; `unite` names them in the count."""
    _colorise(geojson, valeurs, echelle)
    scale, viewbox = _frame(geojson)
    return Carte(
        titre=titre,
        territoire=geojson,
        scale=scale,
        effectif=f"{len(geojson['features'])} {unite}",
        viewbox=viewbox,
        stroke=max(viewbox[2], viewbox[3]) * STROKE_RATIO,
        legend=_legend(echelle, focus_label),
        focus=focus,
    )


def _points(coordinates):
    if isinstance(coordinates[0], (int, float)):
        yield coordinates
    else:
        for part in coordinates:
            yield from _points(part)


def _frame(geojson: dict) -> tuple[float, list[float]]:
    """The longitude scale and the framing viewbox.

    mercator frames every map in a square and pins it to the top, so a wide
    territory fills only a strip: the extent is computed here, and mercator
    only draws. Scaling longitudes by the cosine of the central latitude keeps
    shapes undistorted at this scale.
    """
    points = [
        point
        for feature in geojson["features"]
        for point in _points(feature["geometry"]["coordinates"])
    ]
    latitudes = [point[1] for point in points]
    scale = math.cos(math.radians((min(latitudes) + max(latitudes)) / 2))
    xs = [point[0] * scale for point in points]
    ys = latitudes
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


def table(carte: Carte) -> Table:
    return Table(
        columns=["Code", "Collectivité", carte.legend.title],
        rows=[
            [
                feature["properties"]["code"],
                feature["properties"]["nom"],
                feature["properties"]["valeur"].value,
            ]
            for feature in carte.territoire["features"]
        ],
    )


def geojson(carte: Carte) -> dict:
    """The map's communes with their raw value."""
    return {
        "type": "FeatureCollection",
        "features": [
            {
                "type": "Feature",
                "properties": {
                    "code": feature["properties"]["code"],
                    "nom": feature["properties"]["nom"],
                    "valeur": feature["properties"]["valeur"].value,
                },
                "geometry": feature["geometry"],
            }
            for feature in carte.territoire["features"]
        ],
    }
