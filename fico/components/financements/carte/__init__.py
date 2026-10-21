"""Choroplèthe du taux de financement des projets que porte chaque commune."""

from enum import StrEnum

from ....context import Context
from ....sources import api_collectivites, collectivites, contours
from ....sources.collectivites import COMMUNE
from ...formats import Display, percent, text
from ...registry import component
from ...table import Table

COLUMNS = ["Code", "Collectivité", "Taux de financement", "Contour"]


class Perimeter(StrEnum):
    DEPARTEMENT = "departement"
    INTERCO = "interco"


def _table(
    titre: str, unite: str, territoire: list[dict], taux: dict[str, float], focus: str
) -> Table:
    return Table(
        header=f"{len(territoire)} {unite}",
        titre=titre,
        columns=COLUMNS,
        rows=[
            [
                text(contour["code"]),
                text(contour["nom"]),
                percent(taux.get(contour["code"])),
                Display(contour["geometry"], ""),
            ]
            for contour in territoire
        ],
        focus=next(
            (i for i, contour in enumerate(territoire) if contour["code"] == focus),
            None,
        ),
    )


def _epci(context: Context, perimeter: Perimeter) -> Table | None:
    fiche = context.fiche
    if (
        perimeter is not Perimeter.DEPARTEMENT
        or fiche.type not in collectivites.EPCI_A_FISCALITE_PROPRE
    ):
        return None
    voisins = collectivites.epci_du_departement(
        context.connection, fiche.code_departement
    )
    sirens = [voisin["siren"] for voisin in voisins]
    territoire = contours.epci(context.connection, sirens)
    if not territoire:
        return None
    taux = api_collectivites.taux_par_siren(context.connection, sirens)
    return _table("Département", "EPCI", territoire, taux, fiche.siren)


@component(
    description="Communes du département ou de l'intercommunalité de la commune, "
    "colorées par taux de financement ; pour un EPCI, les EPCI à fiscalité propre "
    "du département.",
    width="1/2",
)
def carte(context: Context, perimeter: Perimeter) -> Table | None:
    fiche = context.fiche
    if fiche.famille != COMMUNE:
        return _epci(context, perimeter)
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
    if not communes:
        return None
    codes = [commune["code"] for commune in communes]
    taux = api_collectivites.taux_par_commune(context.connection, codes)
    return _table(titre, "communes", communes, taux, fiche.code_insee)
