"""Choroplèthe du taux de financement des projets que porte chaque commune."""

from enum import StrEnum

from ....context import Context
from ....sources import api_collectivites, collectivites, contours
from ....sources.collectivites import COMMUNE
from ...formats import Display, percent, text
from ...registry import component
from ...table import Table

COLUMNS = ["Code", "Collectivité", "Taux de financement", "Contour"]


class Perimetre(StrEnum):
    DEPARTEMENT = "departement"
    INTERCO = "interco"


def _table(
    title: str, unit: str, territoire: list[dict], taux: dict[str, float], focus: str
) -> Table:
    return Table(
        header=f"{len(territoire)} {unit}",
        title=title,
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


def _epci(context: Context, perimetre: Perimetre) -> Table | None:
    fiche = context.fiche
    if (
        perimetre is not Perimetre.DEPARTEMENT
        or fiche.type not in collectivites.EPCI_A_FISCALITE_PROPRE
    ):
        return None
    peers = collectivites.epci_of_departement(
        context.connection, fiche.code_departement
    )
    sirens = [peer["siren"] for peer in peers]
    territoire = contours.epci(context.connection, sirens)
    if not territoire:
        return None
    taux = api_collectivites.taux_by_siren(context.connection, sirens)
    return _table("Département", "EPCI", territoire, taux, fiche.siren)


@component(
    description="Communes du département ou de l'intercommunalité de la commune, "
    "colorées par taux de financement ; pour un EPCI, les EPCI à fiscalité propre "
    "du département.",
    width="1/2",
)
def carte(context: Context, perimetre: Perimetre) -> Table | None:
    fiche = context.fiche
    if fiche.famille != COMMUNE:
        return _epci(context, perimetre)
    match perimetre:
        case Perimetre.DEPARTEMENT:
            title = "Département"
            communes = contours.by_departement(
                context.connection, fiche.code_departement
            )
        case Perimetre.INTERCO:
            if not fiche.code_epci:
                return None
            title = "Intercommunalité"
            communes = contours.by_epci(context.connection, fiche.code_epci)
    if not communes:
        return None
    codes = [commune["code"] for commune in communes]
    taux = api_collectivites.taux_by_commune(context.connection, codes)
    return _table(title, "communes", communes, taux, fiche.code_insee)
