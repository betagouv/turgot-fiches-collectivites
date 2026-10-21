from ....context import Context
from ....sources import api_collectivites
from ...formats import euros, percent, plain, text
from ...registry import component
from ...table import Table

COLUMNS = ["Année", "Financeur", "Référence", "Projet", "Coût", "Subvention", "Taux"]


@component(
    description="Liste des financements reçus, projet par projet, avec leur "
    "coût et leur taux de financement.",
)
def historique(context: Context, since: int | None = None) -> Table:
    rows = []
    for row in api_collectivites.financements_recus(
        context.connection, context.fiche.siren, since
    ):
        cout = row["budget_previsionnel"] or None
        montant = row["montant_attribue"]
        rows.append(
            [
                plain(row["annee"]),
                text(row["source"]),
                text(row["reference"]),
                text(row["nom"]),
                euros(cout),
                euros(montant),
                percent(montant / cout if cout and montant else None),
            ]
        )
    titre = "Historique des subventions"
    return Table(
        titre=f"{titre} ({len(rows)})" if rows else titre,
        columns=COLUMNS,
        rows=rows,
        vide="Aucun financement",
    )
