from dataclasses import dataclass

from ...context import Context, Result
from ...sources.collectivites import COMMUNE
from ..formats import Display, decimal, number, text
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


@component(
    name="identite",
    description="Identité de la collectivité : SIREN, code INSEE, population, "
    "superficie, densité, codes postaux, intercommunalité, département, région.",
    width="1/2",
)
async def collect(context: Context) -> Result | None:
    fiche = context.fiche
    pairs = [("SIREN", text(fiche.siren))]

    if fiche.famille != COMMUNE:
        creation = fiche.date_creation.isoformat() if fiche.date_creation else None
        pairs += [
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

    pairs += [
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
