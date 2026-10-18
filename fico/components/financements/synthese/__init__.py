from dataclasses import dataclass

from ....context import Context, Result
from ....sources import api_collectivites
from ...formats import Display, euros, number, percent
from ...registry import component


@dataclass
class Synthese:
    titre: str
    periode: str
    montant: Display
    projets: Display
    cout: Display
    taux: Display


@component(
    description="Total reçu, nombre de projets, coût des projets et taux de "
    "financement, tous financeurs ou pour un seul.",
    width="1/4",
)
def collect(
    context: Context, since: int | None = None, financeur: str | None = None
) -> Result:
    connection, siren = context.connection, context.fiche.siren
    totaux = api_collectivites.totaux(connection, siren, since, financeur)
    cofinancement = api_collectivites.cofinancement(connection, siren, since, financeur)
    cout = cofinancement["cout"] or 0
    premiere, derniere = totaux["premiere_annee"], totaux["derniere_annee"]

    synthese = Synthese(
        titre=financeur or "Tous financeurs",
        periode=f"{premiere} – {derniere}" if premiere else "",
        montant=euros(totaux["montant"]),
        projets=number(totaux["projets"]),
        cout=euros(cout),
        taux=percent(cofinancement["montant"] / cout if cout else None),
    )
    return Result(data=synthese)
