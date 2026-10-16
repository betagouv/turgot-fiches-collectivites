from dataclasses import dataclass

from ...context import Context, Result
from ...sources import rne
from ...sources.collectivites import COMMUNE
from ..formats import Display, decimal, long_date, number, text
from ..registry import component


@dataclass
class Row:
    label: str
    value: Display


@dataclass
class Identite:
    rows: list[Row]


def _rows(pairs: list[tuple[str, Display]]) -> Identite:
    return Identite([Row(label, value) for label, value in pairs if value.value])


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
def collect(context: Context) -> Result | None:
    fiche = context.fiche
    connection = context.connection

    if fiche.famille != COMMUNE:
        president = rne.de_collectivite(connection, rne.Fonction.PRESIDENT, fiche.siren)
        creation = fiche.date_creation.isoformat() if fiche.date_creation else None
        pairs = [
            ("Président", _executif(president)),
            ("SIREN", text(fiche.siren)),
            ("Type", text(fiche.type)),
            ("Mode de financement", text(fiche.mode_financement)),
            ("Date de création", text(creation)),
            ("Département", text(fiche.nom_departement)),
        ]
        return Result(data=_rows(pairs))

    superficie = fiche.superficie
    densite = (
        fiche.population / superficie
        if superficie and fiche.population is not None
        else None
    )

    maire = rne.de_collectivite(connection, rne.Fonction.MAIRE, fiche.code_insee)
    pairs = [
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
    return Result(data=_rows(pairs))
