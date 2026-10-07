from ...context import Context, Result
from ...sources import geo
from ...sources.referentiel import COMMUNE
from ..registry import Placement, component


def _number(value) -> str:
    return f"{value:,}".replace(",", " ")


@component(name="identite", placement=Placement.CARD)
async def collect(context: Context) -> Result | None:
    fiche = context.fiche
    lignes = [("SIREN", fiche.siren)]

    if fiche.famille != COMMUNE:
        lignes += [
            ("Type", fiche.type),
            ("Mode de financement", fiche.mode_financement),
            ("Date de création", fiche.date_creation),
            ("Départements", ", ".join(fiche.departements)),
        ]
        return Result(data=[p for p in lignes if p[1]])

    details = await geo.commune(context.client, fiche.code_insee)
    surface = details["surface"] / 100 if details.get("surface") else None

    lignes.append(("Code INSEE", fiche.code_insee))
    if fiche.population is not None:
        lignes.append(("Population", f"{_number(fiche.population)} habitants"))
    if surface:
        lignes.append(("Superficie", f"{surface:.1f}".replace(".", ",") + " km²"))
        if fiche.population is not None:
            densite = round(fiche.population / surface)
            lignes.append(("Densité", f"{_number(densite)} hab./km²"))
    lignes += [
        ("Codes postaux", ", ".join(fiche.codes_postaux)),
        ("Département", fiche.code_departement),
        ("Région", fiche.code_region),
    ]
    return Result(data=[p for p in lignes if p[1]])
