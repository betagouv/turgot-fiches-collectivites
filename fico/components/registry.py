import inspect
import re
import typing
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from enum import Enum, StrEnum
from fractions import Fraction
from pathlib import Path

ROOT = Path(__file__).parent

# `identite,historique(since=2020),carto.*`: values hold neither commas nor
# parentheses.
ITEM = r"[\w.*]+\s*(?:\([^()]*\))?"
SPECS = re.compile(rf"\s*{ITEM}\s*(?:,\s*{ITEM}\s*)*")
SPEC = re.compile(r"(?P<name>[\w.*]+)\s*(?:\((?P<arguments>[^()]*)\))?")


class Access(StrEnum):
    PUBLIC = "public"
    RESTRICTED = "restricted"


class UnknownComponent(Exception):
    pass


class InvalidParameter(Exception):
    pass


def template(module: str, extension: str) -> Path:
    """A module's template sits in its package, named after its last segment:
    `carto.financements` → `carto/financements/financements.js`."""
    parts = module.split(".")
    return ROOT.joinpath(*parts, f"{parts[-1]}.{extension}")


def ancestors(module: str) -> list[str]:
    """The enclosing modules, outermost first, whose templates the module's own
    may import: `carto.financements` → `carto`."""
    parts = module.split(".")
    return [".".join(parts[:end]) for end in range(1, len(parts))]


@dataclass(frozen=True)
class Parameter:
    kind: type
    required: bool

    def describe(self) -> dict:
        description = {"type": self.kind.__name__, "required": self.required}
        if issubclass(self.kind, Enum):
            description["choices"] = [choice.value for choice in self.kind]
        return description


@dataclass(frozen=True)
class Component:
    name: str
    description: str
    width: Fraction
    access: Access
    collect: Callable
    parameters: dict[str, Parameter]

    def template(self, extension: str) -> Path:
        return template(self.name, extension)

    def instance(self, values: Mapping[str, str]) -> Instance:
        """The component with its `collect` keyword arguments, from their text
        values."""
        arguments = {}
        for key, value in values.items():
            parameter = self.parameters.get(key)
            if parameter is None:
                accepted = ", ".join(self.parameters) or "aucun"
                raise InvalidParameter(
                    f"{self.name} n'accepte pas le paramètre {key}. "
                    f"Paramètres acceptés : {accepted}."
                )
            try:
                arguments[key] = parameter.kind(value)
            except ValueError:
                raise InvalidParameter(
                    f"{self.name} : {key}={value} invalide, "
                    f"attendu : {parameter.describe()}."
                ) from None
        missing = [
            key
            for key, parameter in self.parameters.items()
            if parameter.required and key not in arguments
        ]
        if missing:
            expected = {key: self.parameters[key].describe() for key in missing}
            raise InvalidParameter(f"{self.name} : paramètre(s) requis : {expected}.")
        ordered = {key: arguments[key] for key in self.parameters if key in arguments}
        return Instance(self, ordered)


@dataclass(frozen=True)
class Instance:
    """A component and the arguments it is collected with: a page may hold the
    same component twice, with different arguments."""

    component: Component
    arguments: dict[str, object]

    @property
    def name(self) -> str:
        return self.component.name

    @property
    def spec(self) -> str:
        """`historique(since=2020)`, as `selected` reads it back."""
        if not self.arguments:
            return self.name
        arguments = ",".join(f"{key}={value}" for key, value in self.arguments.items())
        return f"{self.name}({arguments})"


COMPONENTS: dict[str, Component] = {}
DEFAULT: list[Instance] = []


def _parameters(collect: Callable) -> dict[str, Parameter]:
    """The parameters `collect` takes after its context, each with the type its
    text value converts to: `since: int | None = None` is an optional `int`."""
    _, *parameters = inspect.signature(collect).parameters.values()
    found = {}
    for parameter in parameters:
        annotation = parameter.annotation
        types = [t for t in typing.get_args(annotation) if t is not type(None)]
        found[parameter.name] = Parameter(
            kind=types[0] if types else annotation,
            required=parameter.default is inspect.Parameter.empty,
        )
    return found


def component(
    description: str,
    width: str = "1",
    access: Access = Access.PUBLIC,
):
    """The component is named after its package: `components/carto/financements/`
    is `carto.financements`.

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
            parameters=_parameters(collect),
        )
        return collect

    return decorate


def modules() -> set[str]:
    """Every component and enclosing module, the ones whose templates may exist."""
    return {module for name in COMPONENTS for module in (*ancestors(name), name)}


def _instances(spec: str) -> list[Instance]:
    """`carto.*` stands for every default instance under `carto`, in page order."""
    match = SPEC.fullmatch(spec)
    name, arguments = match["name"], match["arguments"]
    if name.endswith(".*"):
        prefix = name.removesuffix("*")
        return [instance for instance in DEFAULT if instance.name.startswith(prefix)]
    if name not in COMPONENTS:
        return []
    values = {}
    for argument in (arguments or "").split(","):
        if argument.strip():
            key, _, value = argument.partition("=")
            values[key.strip()] = value.strip()
    return [COMPONENTS[name].instance(values)]


def _parse(requested: str) -> list[Instance]:
    if not SPECS.fullmatch(requested):
        raise UnknownComponent(
            f"Composants illisibles : {requested}. "
            f"Attendu par exemple : identite,historique(since=2020),carto.*"
        )
    specs = [match.group(0) for match in re.finditer(ITEM, requested)]
    expanded = {spec: _instances(spec) for spec in specs}
    unknown = [spec for spec, instances in expanded.items() if not instances]
    if unknown:
        raise UnknownComponent(
            f"Composant(s) inconnu(s) : {', '.join(unknown)}. "
            f"Composants disponibles : {', '.join(COMPONENTS)}."
        )
    return [instance for spec in specs for instance in expanded[spec]]


def order(*specs: str) -> None:
    """Fixe les composants d'une fiche par défaut et leur ordre d'apparition."""
    DEFAULT[:] = _parse(",".join(specs))
    declared = set(COMPONENTS)
    wanted = {instance.name for instance in DEFAULT}
    if declared != wanted:
        raise UnknownComponent(
            f"L'ordre ne couvre pas les composants déclarés : "
            f"manquants {sorted(declared - wanted)}."
        )
    names = dict.fromkeys(instance.name for instance in DEFAULT)
    ordered = {name: COMPONENTS[name] for name in names}
    COMPONENTS.clear()
    COMPONENTS.update(ordered)


def selected(
    requested: str | None, authenticated: bool = False
) -> tuple[Instance, ...]:
    instances = _parse(requested) if requested else DEFAULT
    unique = {instance.spec: instance for instance in instances}
    if authenticated:
        return tuple(unique.values())
    return tuple(i for i in unique.values() if i.component.access is Access.PUBLIC)


def rows(instances) -> list[tuple[Instance, ...]]:
    """The lines of a page, in the given order: each instance joins the current
    line while their widths add up to one at most, otherwise starts the next."""
    lines, used = [], Fraction(0)
    for instance in instances:
        width = instance.component.width
        if lines and used + width <= 1:
            lines[-1] = (*lines[-1], instance)
            used += width
        else:
            lines.append((instance,))
            used = width
    return lines
