import re
from datetime import UTC, datetime

from .components import Instance, rows
from .context import Context
from .errors import FicoError
from .render import typst
from .sources import collectivites
from .sources.collectivites import COMMUNE, Fiche
from .sources.database import connection

SOURCE = (
    "Sources : geo.api.gouv.fr, BANATIC, API Collectivités, "
    "contours et programmes publiés sur data.gouv.fr"
)

CODE_INSEE = re.compile(r"\d{5}|2[AB]\d{3}")
SIREN = re.compile(r"\d{9}")


class InvalidIdentifier(FicoError):
    def __init__(self, identifiant: str):
        super().__init__(
            f"{identifiant} n'est ni un code INSEE de commune (5 caractères) "
            "ni un SIREN (9 chiffres)."
        )


def resolve(identifiant: str) -> Fiche:
    """Trouve la collectivité derrière un code INSEE de commune ou un SIREN."""
    if CODE_INSEE.fullmatch(identifiant):
        return collectivites.by_code_insee(identifiant)
    if SIREN.fullmatch(identifiant):
        return collectivites.by_siren(identifiant)
    raise InvalidIdentifier(identifiant)


def _header(fiche: Fiche) -> dict:
    return {
        "nom": fiche.nom,
        "libelle_type": "Commune" if fiche.famille == COMMUNE else fiche.type,
        "source": f"{SOURCE} — généré le {datetime.now(UTC):%d/%m/%Y}",
    }


def describe(identifiant: str) -> dict:
    """The fiche's header alone, without collecting any component."""
    with connection.connect():
        return _header(resolve(identifiant))


def collect_one(identifiant: str, instance: Instance):
    with connection.connect():
        return instance(Context(fiche=resolve(identifiant)))


def collect(identifiant: str, instances) -> tuple[dict, list[list[dict]]]:
    """The header, and the lines of the instances that have something to show,
    each with its data: the fiche's contract with every renderer."""
    shown, data = [], {}
    with connection.connect():
        fiche = resolve(identifiant)
        context = Context(fiche=fiche)
        for instance in instances:
            result = instance(context)
            if result is not None:
                shown.append(instance)
                data[instance.spec] = result

    lines = [
        [
            {
                "name": instance.name,
                "parameters": instance.arguments,
                "width": str(instance.component.width),
                "data": data[instance.spec],
            }
            for instance in line
        ]
        for line in rows(shown)
    ]
    return _header(fiche), lines


def render(header: dict, lines: list[list[dict]]) -> bytes:
    return typst.compile_fiche(header, lines)


def render_component(instance: Instance, data, image_format: str) -> bytes:
    return typst.compile_component(
        instance.name, instance.component.width, data, image_format
    )


__all__ = [
    "InvalidIdentifier",
    "collect",
    "collect_one",
    "describe",
    "render",
    "render_component",
    "resolve",
]
