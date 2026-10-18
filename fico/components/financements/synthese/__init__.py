from dataclasses import dataclass

from ....context import Context, Result
from ....sources import api_collectivites
from ...formats import Display, euros, number, percent
from ...registry import component


@dataclass
class Tile:
    main: Display
    main_caption: str
    secondary: Display
    secondary_caption: str


@dataclass
class Synthese:
    periode: str
    tiles: list[Tile]


@component(
    description="Totaux des financements reçus : tous financeurs, DETR, DSIL, "
    "Fonds vert, coût des projets et taux de financement.",
)
def collect(context: Context) -> Result | None:
    siren = context.fiche.siren
    par_source = api_collectivites.totaux_par_source(context.connection, siren)
    if not par_source:
        return None

    par_annee = api_collectivites.totaux_par_annee(context.connection, siren)
    annees = [ligne["annee"] for ligne in par_annee if ligne["annee"] is not None]

    cofinancement = api_collectivites.cofinancement(context.connection, siren)
    cout = cofinancement["cout"] or 0
    taux = cofinancement["montant"] / cout if cout else None

    montants = {ligne["source"]: ligne["montant"] or 0 for ligne in par_source}
    total = sum(montants.values())
    detr = montants.get("DETR", 0)
    dsil = montants.get("DSIL", 0)
    fonds_vert = montants.get("Fonds Vert", 0)
    projets = sum(ligne["projets"] for ligne in par_source)

    synthese = Synthese(
        periode=f"{annees[0]} – {annees[-1]}" if annees else "",
        tiles=[
            Tile(
                euros(total),
                "reçus, tous financeurs",
                number(projets),
                "projets financés",
            ),
            Tile(euros(detr), "de DETR", euros(dsil), "de DSIL"),
            Tile(
                euros(fonds_vert),
                "de Fonds vert",
                euros(total - detr - dsil - fonds_vert),
                "autres financeurs",
            ),
            Tile(
                euros(cout),
                "de coût des projets renseignés",
                percent(taux),
                "de taux de financement",
            ),
        ],
    )
    return Result(data=synthese)
