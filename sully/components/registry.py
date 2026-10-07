import inspect
from collections.abc import Callable
from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path


class Access(StrEnum):
    PUBLIC = "public"
    RESTRICTED = "restricted"


class Placement(StrEnum):
    CARD = "card"
    SECTION = "section"


@dataclass(frozen=True)
class Component:
    name: str
    placement: Placement
    access: Access
    folder: Path
    collect: Callable

    def template(self, extension: str) -> Path:
        return self.folder / f"{self.name}.{extension}"


COMPONENTS: dict[str, Component] = {}


class UnknownComponent(Exception):
    pass


def component(
    name: str,
    placement: Placement = Placement.SECTION,
    access: Access = Access.PUBLIC,
):
    def decorate(collect: Callable) -> Callable:
        COMPONENTS[name] = Component(
            name=name,
            placement=placement,
            access=access,
            folder=Path(inspect.getfile(collect)).parent,
            collect=collect,
        )
        return collect

    return decorate


def order(*names: str) -> None:
    """Fixe l'ordre d'apparition des composants dans la page."""
    declared, wanted = set(COMPONENTS), set(names)
    if declared != wanted:
        raise UnknownComponent(
            f"L'ordre ne couvre pas les composants déclarés : "
            f"manquants {sorted(declared - wanted)}, "
            f"inconnus {sorted(wanted - declared)}."
        )
    ordered = {name: COMPONENTS[name] for name in names}
    COMPONENTS.clear()
    COMPONENTS.update(ordered)


def names() -> tuple[str, ...]:
    return tuple(COMPONENTS)


def selected(
    requested: str | None, authenticated: bool = False
) -> tuple[Component, ...]:
    if requested:
        asked = tuple(name.strip() for name in requested.split(",") if name.strip())
        unknown = [name for name in asked if name not in COMPONENTS]
        if unknown:
            raise UnknownComponent(
                f"Composant(s) inconnu(s) : {', '.join(unknown)}. "
                f"Composants disponibles : {', '.join(COMPONENTS)}."
            )
    else:
        asked = tuple(COMPONENTS)
    chosen = tuple(COMPONENTS[name] for name in asked)
    if authenticated:
        return chosen
    return tuple(c for c in chosen if c.access is Access.PUBLIC)
