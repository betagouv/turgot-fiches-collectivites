from collections.abc import Callable
from dataclasses import dataclass
from enum import StrEnum
from fractions import Fraction
from pathlib import Path

ROOT = Path(__file__).parent


class Access(StrEnum):
    PUBLIC = "public"
    RESTRICTED = "restricted"


def template(module: str, extension: str) -> Path:
    """A module's template sits in its package, named after its last segment:
    `carto.financements` → `carto/financements/financements.js`."""
    parts = module.split(".")
    return ROOT.joinpath(*parts, f"{parts[-1]}.{extension}")


def ancestors(module: str) -> list[str]:
    """The enclosing modules, outermost first, whose templates the module's own
    may import: `carto.financements.departement` → `carto`, `carto.financements`."""
    parts = module.split(".")
    return [".".join(parts[:end]) for end in range(1, len(parts))]


@dataclass(frozen=True)
class Component:
    name: str
    description: str
    width: Fraction
    access: Access
    collect: Callable

    def template(self, extension: str) -> Path:
        return template(self.name, extension)


COMPONENTS: dict[str, Component] = {}


class UnknownComponent(Exception):
    pass


def component(
    description: str,
    width: str = "1",
    access: Access = Access.PUBLIC,
):
    """The component is named after its package: `components/carto/financements/
    departement/` is `carto.financements.departement`.

    `width` is the share of a line the content needs, as "1/3", "1/2" or "1"."""
    share = Fraction(width)

    def decorate(collect: Callable) -> Callable:
        name = collect.__module__.removeprefix(f"{__package__}.")
        if not 0 < share <= 1:
            raise ValueError(f"{name} : largeur {width} hors de ]0, 1].")
        COMPONENTS[name] = Component(
            name=name,
            description=description,
            width=share,
            access=access,
            collect=collect,
        )
        return collect

    return decorate


def modules() -> set[str]:
    """Every component and enclosing module, the ones whose templates may exist."""
    return {module for name in COMPONENTS for module in (*ancestors(name), name)}


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


def _expand(pattern: str) -> list[str]:
    """`carto.*` stands for every component under `carto`, in page order."""
    if not pattern.endswith(".*"):
        return [pattern] if pattern in COMPONENTS else []
    prefix = pattern.removesuffix("*")
    return [name for name in COMPONENTS if name.startswith(prefix)]


def selected(
    requested: str | None, authenticated: bool = False
) -> tuple[Component, ...]:
    if requested:
        patterns = [part.strip() for part in requested.split(",") if part.strip()]
        expanded = {pattern: _expand(pattern) for pattern in patterns}
        unknown = [pattern for pattern, names in expanded.items() if not names]
        if unknown:
            raise UnknownComponent(
                f"Composant(s) inconnu(s) : {', '.join(unknown)}. "
                f"Composants disponibles : {', '.join(COMPONENTS)}."
            )
        asked = [name for pattern in patterns for name in expanded[pattern]]
    else:
        asked = list(COMPONENTS)
    chosen = tuple(COMPONENTS[name] for name in dict.fromkeys(asked))
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
