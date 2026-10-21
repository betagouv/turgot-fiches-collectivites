from ....context import Context
from ....sources import api_collectivites
from ...formats import compact_euros, text
from ...registry import component
from ...table import Table


@component(
    description="Répartition des financements reçus par financeur.",
    width="1/2",
)
def financeurs(context: Context, since: int | None = None) -> Table:
    par_source = api_collectivites.totaux_par_source(
        context.connection, context.fiche.siren, since
    )
    return Table(
        titre="Répartition par financeur",
        columns=["Financeur", "Montant reçu"],
        rows=[
            [text(ligne["source"]), compact_euros(ligne["montant"] or 0)]
            for ligne in par_source
        ],
        vide="Aucun financement",
    )
