from dataclasses import dataclass

from ...context import Context, Result
from ...sources import geo
from ...sources.referentiel import COMMUNE
from ..formats import Display, decimal, number, text
from ..registry import Width, component


@dataclass
class Row:
    label: str
    value: Display


@dataclass
class Identite:
    rows: list[Row]


def _nom(details: dict, key: str) -> str | None:
    return (details.get(key) or {}).get("nom")


def _rows(pairs: list[tuple[str, Display]]) -> Identite:
    return Identite([Row(label, value) for label, value in pairs if value.value])


@component(
    name="identite",
    description="Identité de la collectivité : SIREN, code INSEE, population, "
    "superficie, densité, codes postaux, intercommunalité, département, région.",
    width=Width.NARROW,
)
async def collect(context: Context) -> Result | None:
    fiche = context.fiche
    pairs = [("SIREN", text(fiche.siren))]

    if fiche.famille != COMMUNE:
        pairs += [
            ("Type", text(fiche.type)),
            ("Mode de financement", text(fiche.mode_financement)),
            ("Date de création", text(fiche.date_creation)),
            ("Départements", text(", ".join(fiche.departements))),
        ]
        return Result(data=_rows(pairs))

    details = await geo.commune(context.client, fiche.code_insee)
    surface = details["surface"] / 100 if details.get("surface") else None
    densite = (
        fiche.population / surface if surface and fiche.population is not None else None
    )

    pairs += [
        ("Code INSEE", text(fiche.code_insee)),
        ("Population", number(fiche.population, "habitants")),
        ("Superficie", decimal(surface, "km²")),
        ("Densité", number(densite, "hab./km²")),
        ("Codes postaux", text(", ".join(fiche.codes_postaux))),
        ("Intercommunalité", text(_nom(details, "epci"))),
        ("Département", text(_nom(details, "departement"))),
        ("Région", text(_nom(details, "region"))),
    ]
    return Result(data=_rows(pairs))
