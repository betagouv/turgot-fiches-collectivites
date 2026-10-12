import inspect
from collections.abc import Callable
from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path


class Access(StrEnum):
    PUBLIC = "public"
    RESTRICTED = "restricted"


class Width(StrEnum):
    NARROW = "narrow"
    LARGE = "large"


@dataclass(frozen=True)
class Component:
    name: str
    description: str
    width: Width
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
    description: str,
    width: Width = Width.LARGE,
    access: Access = Access.PUBLIC,
):
    def decorate(collect: Callable) -> Callable:
        COMPONENTS[name] = Component(
            name=name,
            description=description,
            width=width,
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


def rows(chosen) -> list[tuple[Component, ...]]:
    """The lines of a page, in the given order: two narrow components in a row
    share a line, any other component has one to itself."""
    lines = []
    for component in chosen:
        previous = lines[-1] if lines else ()
        pairs = (
            component.width is Width.NARROW
            and len(previous) == 1
            and previous[0].width is Width.NARROW
        )
        if pairs:
            lines[-1] = (*previous, component)
        else:
            lines.append((component,))
    return lines
