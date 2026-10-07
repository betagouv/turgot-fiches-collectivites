import json

from ...context import Context, Result
from ...sources import contours, subventions
from ...sources.referentiel import COMMUNE
from ..registry import component

PALETTE = ("#ececfe", "#cacafb", "#9a9af8", "#6a6af4", "#000091")
SEUILS_TAUX = (0.15, 0.25, 0.35, 0.50)
COULEUR_FOCUS = "#e1000f"
COULEUR_SANS_DONNEE = "#e5e5e5"


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
            "nom": proprietes.get("nom", ""),
            "couleur": COULEUR_SANS_DONNEE if connu is None else _teinte(connu),
            "contour": COULEUR_FOCUS if focus else "#ffffff",
        }
        feature["_focus"] = focus
    # La bordure de la commune serait recouverte par ses voisines : elle est
    # peinte en dernier.
    geojson["features"].sort(key=lambda f: f.pop("_focus"))
    return geojson


@component(name="carto")
async def collect(context: Context) -> Result | None:
    fiche = context.fiche
    if fiche.famille != COMMUNE or context.connection is None:
        return None

    territoires = [
        (
            "Département",
            "departement.geojson",
            contours.par_departement,
            fiche.code_departement,
        )
    ]
    if fiche.code_epci:
        territoires.append(
            (
                "Intercommunalité",
                "intercommunalite.geojson",
                contours.par_epci,
                fiche.code_epci,
            )
        )

    cartes, files = [], {}
    for titre, fichier, recupere, cle in territoires:
        geojson = recupere(context.connection, cle)
        if not geojson["features"]:
            continue
        codes = [f["properties"]["code"] for f in geojson["features"]]
        taux = subventions.taux_par_commune(context.connection, codes)
        cartes.append(
            {"titre": titre, "fichier": fichier, "communes": len(geojson["features"])}
        )
        files[fichier] = json.dumps(_colorise(geojson, fiche.code_insee, taux))

    return Result(data=cartes, files=files) if cartes else None
