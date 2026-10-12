import re
from datetime import UTC, datetime

from .components import COMPONENTS
from .context import Context
from .render import typst
from .sources import base, collectivites
from .sources.collectivites import COMMUNE, Fiche

SOURCE = (
    "Sources : geo.api.gouv.fr, BANATIC, API Collectivités, "
    "contours et subventions publiés sur data.gouv.fr"
)

CODE_INSEE = re.compile(r"\d{5}|2[AB]\d{3}")
SIREN = re.compile(r"\d{9}")


class IdentifiantInvalide(Exception):
    pass


def resolve(connection: base.Connection, identifiant: str) -> Fiche:
    """Trouve la collectivité derrière un code INSEE de commune ou un SIREN."""
    if CODE_INSEE.fullmatch(identifiant):
        return collectivites.par_code_insee(connection, identifiant)
    if SIREN.fullmatch(identifiant):
        return collectivites.par_siren(connection, identifiant)
    raise IdentifiantInvalide(
        f"{identifiant} n'est ni un code INSEE de commune (5 caractères) "
        f"ni un SIREN (9 chiffres)."
    )


def _header(fiche: Fiche) -> dict:
    return {
        "nom": fiche.nom,
        "libelle_type": "Commune" if fiche.famille == COMMUNE else fiche.type,
        "source": f"{SOURCE} — généré le {datetime.now(UTC):%d/%m/%Y}",
    }


def describe(identifiant: str) -> dict:
    """The fiche's header alone, without collecting any component."""
    with base.connect() as connection:
        return _header(resolve(connection, identifiant))


async def collect(identifiant: str, components) -> tuple[dict, dict]:
    names = tuple(component.name for component in components)
    results = {}
    with base.connect() as connection:
        fiche = resolve(connection, identifiant)
        context = Context(fiche=fiche, connection=connection, components=names)
        for component in components:
            result = await component.collect(context)
            if result is not None:
                results[component.name] = result

    return _header(fiche), results


def render(header: dict, results: dict) -> bytes:
    return typst.compile_fiche(header, results)


__all__ = [
    "COMPONENTS",
    "IdentifiantInvalide",
    "collect",
    "describe",
    "render",
    "resolve",
]
