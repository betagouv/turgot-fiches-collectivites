from dataclasses import dataclass

from ...context import Context, Result
from ...sources import api_collectivites
from ..formats import Display, euros, percent, plain, text
from ..registry import component


@dataclass
class Ligne:
    annee: Display
    financeur: Display
    projet: Display
    cout: Display
    montant: Display
    taux: Display


@dataclass
class Historique:
    lignes: list[Ligne]


@component(
    name="historique",
    description="Liste des financements reçus, projet par projet, avec leur "
    "coût et leur taux de financement.",
)
async def collect(context: Context) -> Result | None:
    lignes = []
    for row in api_collectivites.financements_recus(
        context.connection, context.fiche.siren
    ):
        cout = row["budget_previsionnel"] or None
        montant = row["montant_attribue"]
        lignes.append(
            Ligne(
                annee=plain(row["annee"]),
                financeur=text(row["source"]),
                projet=text(row["nom"]),
                cout=euros(cout),
                montant=euros(montant),
                taux=percent(montant / cout if cout and montant else None),
            )
        )
    return Result(data=Historique(lignes)) if lignes else None
