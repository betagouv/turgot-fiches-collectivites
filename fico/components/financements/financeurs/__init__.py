from dataclasses import dataclass

from ....context import Context, Result
from ....render.table import Table
from ....sources import api_collectivites
from ...formats import Display, compact_euros
from ...registry import component


@dataclass
class Financeur:
    financeur: str
    montant: Display
    share: float


@dataclass
class Financeurs:
    financeurs: list[Financeur]


def table(data: Financeurs) -> Table:
    return Table(
        columns=["Financeur", "Montant reçu"],
        rows=[[ligne.financeur, ligne.montant.value] for ligne in data.financeurs],
    )


@component(
    description="Répartition des financements reçus par financeur.",
    width="1/2",
    table=table,
)
def collect(context: Context) -> Result | None:
    par_source = api_collectivites.totaux_par_source(
        context.connection, context.fiche.siren
    )
    if not par_source:
        return None
    montants = {ligne["source"]: ligne["montant"] or 0 for ligne in par_source}
    total = sum(montants.values())
    financeurs = Financeurs(
        [
            Financeur(source, compact_euros(montant), montant / total if total else 0)
            for source, montant in montants.items()
        ]
    )
    return Result(data=financeurs)
