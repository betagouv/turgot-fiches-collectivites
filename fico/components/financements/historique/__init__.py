from ....sources import api_collectivites
from ....sources.collectivites import Fiche
from ... import financements
from ...formats import euros, percent, plain, text
from ...registry import component
from ...table import Table

COLUMNS = ["Année", "Financeur", "Référence", "Projet", "Coût", "Subvention", "Taux"]


@component(
    description="Liste des financements reçus, projet par projet, avec leur "
    "coût et leur taux de financement, sur les six dernières années révolues ou "
    "depuis l'année since.",
)
def historique(fiche: Fiche, since: int | None = None) -> Table:
    years = financements.years(since)
    rows = []
    for row in api_collectivites.financements_recus(fiche.siren, years):
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
    title = "Historique des subventions"
    return Table(
        title=f"{title} ({len(rows)})" if rows else title,
        columns=COLUMNS,
        rows=rows,
        header=f"{years[0]} – {years[-1]}",
        empty="Aucun financement",
    )
