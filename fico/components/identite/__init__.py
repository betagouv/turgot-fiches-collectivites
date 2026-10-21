from ...context import Context
from ...sources import rne
from ...sources.collectivites import COMMUNE
from ..formats import Display, decimal, long_date, number, text
from ..registry import component
from ..table import Table


def _table(pairs: list[tuple[str, Display]]) -> Table:
    return Table(
        title="Identité",
        columns=["Libellé", "Valeur"],
        rows=[[text(label), value] for label, value in pairs if value.value],
    )


def _executif(executif: rne.Executif | None) -> Display:
    if executif is None:
        return text(None)
    nom = f"{executif.prenom} {executif.nom}"
    if executif.depuis is None:
        return text(nom)
    return Display(nom, f"{nom}, depuis le {long_date(executif.depuis).label}")


@component(
    description="Identité de la collectivité : maire ou président, SIREN, code "
    "INSEE, population, superficie, densité, codes postaux, intercommunalité, "
    "département, région.",
    width="1/2",
)
def identite(context: Context) -> Table:
    fiche = context.fiche
    connection = context.connection

    if fiche.famille != COMMUNE:
        president = rne.for_collectivite(
            connection, rne.Fonction.PRESIDENT, fiche.siren
        )
        return _table(
            [
                ("Président", _executif(president)),
                ("SIREN", text(fiche.siren)),
                ("Type", text(fiche.type)),
                ("Mode de financement", text(fiche.mode_financement)),
                ("Date de création", long_date(fiche.date_creation)),
                ("Département", text(fiche.nom_departement)),
            ]
        )

    superficie = fiche.superficie
    densite = (
        fiche.population / superficie
        if superficie and fiche.population is not None
        else None
    )

    maire = rne.for_collectivite(connection, rne.Fonction.MAIRE, fiche.code_insee)
    return _table(
        [
            ("Maire", _executif(maire)),
            ("SIREN", text(fiche.siren)),
            ("Code INSEE", text(fiche.code_insee)),
            ("Population", number(fiche.population, "habitants")),
            ("Superficie", decimal(superficie, "km²")),
            ("Densité", number(densite, "hab./km²")),
            ("Codes postaux", text(", ".join(fiche.codes_postaux))),
            ("Intercommunalité", text(fiche.nom_epci)),
            ("Département", text(fiche.nom_departement)),
            ("Région", text(fiche.nom_region)),
        ]
    )
