import json
from pathlib import Path

from ...contexte import Contexte, Resultat
from ...sources import base, geo
from ...sources.referentiel import COMMUNE

NOM = "carto"
PLACEMENT = "section"
DOSSIER = Path(__file__).parent

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


async def collecte(contexte: Contexte) -> Resultat | None:
    fiche = contexte.fiche
    if fiche.famille != COMMUNE:
        return None

    territoires = [
        (
            "Département",
            "departement.geojson",
            geo.contours_departement,
            fiche.code_departement,
        )
    ]
    if fiche.code_epci:
        territoires.append(
            (
                "Intercommunalité",
                "intercommunalite.geojson",
                geo.contours_epci,
                fiche.code_epci,
            )
        )

    cartes, fichiers = [], {}
    for titre, fichier, recupere, cle in territoires:
        geojson = await recupere(contexte.client, cle)
        codes = [f["properties"].get("code") for f in geojson["features"]]
        taux = (
            base.taux_par_commune(contexte.connection, codes)
            if contexte.connection
            else {}
        )
        cartes.append(
            {
                "titre": titre,
                "fichier": fichier,
                "communes": len(geojson["features"]),
            }
        )
        fichiers[fichier] = json.dumps(_colorise(geojson, fiche.code_insee, taux))

    return Resultat(donnees=cartes, fichiers=fichiers)
