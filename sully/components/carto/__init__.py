import json
import math
from dataclasses import dataclass
from itertools import pairwise

from ...context import Context, Result
from ...sources import contours, subventions
from ...sources.collectivites import COMMUNE
from ..formats import percent
from ..registry import component

PALETTE = ("#ececfe", "#cacafb", "#9a9af8", "#6a6af4", "#000091")
SEUILS_TAUX = (0.15, 0.25, 0.35, 0.50)
COULEUR_FOCUS = "#000000"
COULEUR_SANS_DONNEE = "#e5e5e5"
VIEWBOX_MARGIN = 0.01
STROKE_RATIO = 0.0015


@dataclass
class Carte:
    titre: str
    geojson: str
    projected: str
    communes: int
    viewbox: list[float]
    stroke: float


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
class Carto:
    cartes: list[Carte]
    legend: Legend


def _pourcent(taux: float) -> int:
    return round(taux * 100)


def _legend() -> Legend:
    bornes = [None, *SEUILS_TAUX, None]
    steps = []
    for color, (bas, haut) in zip(PALETTE, pairwise(bornes), strict=True):
        if bas is None:
            label = f"< {_pourcent(haut)} %"
        elif haut is None:
            label = f"≥ {_pourcent(bas)} %"
        else:
            label = f"{_pourcent(bas)} à {_pourcent(haut)} %"
        steps.append(LegendStep(color, label))
    return Legend(
        title="Taux de financement",
        steps=steps,
        no_data=LegendStep(COULEUR_SANS_DONNEE, "n.c."),
        focus=LegendStep(COULEUR_FOCUS, "cette commune"),
    )


def _teinte(taux: float) -> str:
    for rang, seuil in enumerate(SEUILS_TAUX):
        if taux < seuil:
            return PALETTE[rang]
    return PALETTE[-1]


def _colorise(geojson: dict, code_focus: str, taux: dict[str, float]) -> dict:
    for feature in geojson["features"]:
        proprietes = feature["properties"]
        code = proprietes.get("code")
        connu = taux.get(code)
        focus = code == code_focus
        feature["properties"] = {
            "code": code,
            "nom": proprietes.get("nom", ""),
            "taux": percent(connu).label,
            "couleur": COULEUR_SANS_DONNEE if connu is None else _teinte(connu),
            "contour": COULEUR_FOCUS if focus else "#ffffff",
        }
        feature["_focus"] = focus
    # Neighbours would paint over the commune's outline: it goes last.
    geojson["features"].sort(key=lambda f: f.pop("_focus"))
    return geojson


@component(
    name="carto",
    description="Cartes du département et de l'intercommunalité de la commune, "
    "colorées par taux de financement.",
)
async def collect(context: Context) -> Result | None:
    fiche = context.fiche
    if fiche.famille != COMMUNE:
        return None

    territoires = [
        ("Département", "departement", contours.par_departement, fiche.code_departement)
    ]
    if fiche.code_epci:
        territoires.append(
            ("Intercommunalité", "intercommunalite", contours.par_epci, fiche.code_epci)
        )

    cartes, files = [], {}
    for titre, base, recupere, cle in territoires:
        geojson = recupere(context.connection, cle)
        if not geojson["features"]:
            continue
        codes = [f["properties"]["code"] for f in geojson["features"]]
        taux = subventions.taux_par_commune(context.connection, codes)
        _colorise(geojson, fiche.code_insee, taux)
        # Third parties get standard WGS84 GeoJSON; renderers get it projected,
        # so they only draw.
        standard, projected = f"{base}.geojson", f"{base}.projected.json"
        files[standard] = json.dumps(geojson)
        viewbox = _project(geojson)
        files[projected] = json.dumps(geojson)
        cartes.append(
            Carte(
                titre=titre,
                geojson=standard,
                projected=projected,
                communes=len(geojson["features"]),
                viewbox=viewbox,
                stroke=max(viewbox[2], viewbox[3]) * STROKE_RATIO,
            )
        )

    if not cartes:
        return None
    return Result(data=Carto(cartes, _legend()), files=files)


def _points(coordinates):
    if isinstance(coordinates[0], (int, float)):
        yield coordinates
    else:
        for part in coordinates:
            yield from _points(part)


def _project(geojson: dict) -> list[float]:
    """Project in place and return the framing viewbox.

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
    return [
        min(xs) - margin,
        -max(ys) - margin,
        width + 2 * margin,
        height + 2 * margin,
    ]
