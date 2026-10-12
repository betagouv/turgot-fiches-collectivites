import inspect
from collections.abc import Callable
from dataclasses import dataclass
from enum import StrEnum
from fractions import Fraction
from pathlib import Path


class Access(StrEnum):
    PUBLIC = "public"
    RESTRICTED = "restricted"


@dataclass(frozen=True)
class Component:
    name: str
    description: str
    width: Fraction
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
    width: str = "1",
    access: Access = Access.PUBLIC,
):
    """`width` is the share of a line the content needs, as "1/3", "1/2" or "1"."""
    share = Fraction(width)
    if not 0 < share <= 1:
        raise ValueError(f"{name} : largeur {width} hors de ]0, 1].")

    def decorate(collect: Callable) -> Callable:
        COMPONENTS[name] = Component(
            name=name,
            description=description,
            width=share,
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
    """The lines of a page, in the given order: each component joins the current
    line while their widths add up to one at most, otherwise starts the next."""
    lines, used = [], Fraction(0)
    for component in chosen:
        if lines and used + component.width <= 1:
            lines[-1] = (*lines[-1], component)
            used += component.width
        else:
            lines.append((component,))
            used = component.width
    return lines
