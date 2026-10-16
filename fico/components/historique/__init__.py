from dataclasses import dataclass

from ...context import Context, Result
from ...render.table import Table
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


def table(data: Historique) -> Table:
    return Table(
        columns=["Année", "Dotation", "Projet", "Coût", "Subvention", "Taux"],
        rows=[
            [
                ligne.annee.value,
                ligne.financeur.value,
                ligne.projet.value,
                ligne.cout.value,
                ligne.montant.value,
                ligne.taux.value,
            ]
            for ligne in data.lignes
        ],
    )


@component(
    description="Liste des financements reçus, projet par projet, avec leur "
    "coût et leur taux de financement.",
    table=table,
)
def collect(context: Context, since: int | None = None) -> Result | None:
    lignes = []
    for row in api_collectivites.financements_recus(
        context.connection, context.fiche.siren, since
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
