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
    years = [row[0].value for row in rows if row[0].value is not None]
    title = "Historique des subventions"
    return Table(
        title=f"{title} ({len(rows)})" if rows else title,
        columns=COLUMNS,
        rows=rows,
        header=f"{min(years)} – {max(years)}" if years else "",
        empty="Aucun financement",
    )
