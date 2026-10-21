import inspect
import re
import typing
from collections.abc import Callable, Iterator
from dataclasses import dataclass
from enum import Enum, StrEnum
from fractions import Fraction
from pathlib import Path

from ..context import Context
from .table import Table

ROOT = Path(__file__).parent

# One item of `identite,financements.historique(since=2020),financements.*`,
# up to the comma that follows it: values hold neither commas nor parentheses.
SPEC = re.compile(r"\s*(?P<name>[\w.*]+)\s*(?:\((?P<arguments>[^()]*)\))?\s*(?:,|$)")


class Access(StrEnum):
    PUBLIC = "public"
    RESTRICTED = "restricted"


class Download(StrEnum):
    CSV = "csv"
    XLSX = "xlsx"
    GEOJSON = "geojson"


class UnknownComponent(Exception):
    pass


class InvalidParameter(Exception):
    pass


def template(name: str, extension: str) -> Path:
    """A component's template sits in its package, named after its last segment:
    `financements.carte` → `financements/carte/carte.js`."""
    parts = name.split(".")
    return ROOT.joinpath(*parts, f"{parts[-1]}.{extension}")


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
    fonction: Callable
    parameters: dict[str, Parameter]

    def __call__(self, context: Context, **arguments) -> Table | None:
        return self.fonction(context, **arguments)

    def new(self, **values) -> Instance:
        """The component with its keyword arguments, each converted to its
        parameter's type: `since="2020"` and `since=2020` both hold an `int`."""
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

    def __call__(self, context: Context) -> Table | None:
        return self.component(context, **self.arguments)

    @property
    def name(self) -> str:
        return self.component.name

    @property
    def spec(self) -> str:
        """`financements.historique(since=2020)`, as `selected` reads it back."""
        if not self.arguments:
            return self.name
        arguments = ",".join(f"{key}={value}" for key, value in self.arguments.items())
        return f"{self.name}({arguments})"


COMPONENTS: dict[str, Component] = {}
DEFAULT: list[Instance] = []


def _parameters(fonction: Callable) -> dict[str, Parameter]:
    """The parameters `fonction` takes after its context, each with the type its
    text value converts to: `since: int | None = None` is an optional `int`."""
    _, *parameters = inspect.signature(fonction).parameters.values()
    found = {}
    for parameter in parameters:
        annotation = parameter.annotation
        types = [t for t in typing.get_args(annotation) if t is not type(None)]
        found[parameter.name] = Parameter(
            kind=types[0] if types else annotation,
            required=parameter.default is inspect.Parameter.empty,
        )
    return found


def component(description: str, width: str = "1", access: Access = Access.PUBLIC):
    """The decorated function becomes the `Component`, called the same way, and
    named after its package: `components/financements/carte/` is
    `financements.carte`.

    `width` is the share of a line the content needs, as "1/3", "1/2" or "1"."""
    share = Fraction(width)

    def decorate(fonction: Callable) -> Component:
        name = fonction.__module__.removeprefix(f"{__package__}.")
        if not 0 < share <= 1:
            raise ValueError(f"{name} : largeur {width} hors de ]0, 1].")
        return Component(
            name=name,
            description=description,
            width=share,
            access=access,
            fonction=fonction,
            parameters=_parameters(fonction),
        )

    return decorate


def _specs(requested: str) -> Iterator[re.Match]:
    position = 0
    while position < len(requested):
        match = SPEC.match(requested, position)
        if match is None:
            raise UnknownComponent(
                f"Composants illisibles : {requested}. "
                "Attendu par exemple : "
                "identite,financements.historique(since=2020),financements.*"
            )
        yield match
        position = match.end()


def _instances(name: str, arguments: str | None) -> list[Instance]:
    """`financements.*` stands for every default instance under `financements`,
    in page order."""
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
    return [COMPONENTS[name].new(**values)]


def _parse(requested: str) -> list[Instance]:
    expanded = {
        match.group(0).strip(" ,"): _instances(match["name"], match["arguments"])
        for match in _specs(requested)
    }
    unknown = [spec for spec, instances in expanded.items() if not instances]
    if unknown:
        raise UnknownComponent(
            f"Composant(s) inconnu(s) : {', '.join(unknown)}. "
            f"Composants disponibles : {', '.join(COMPONENTS)}."
        )
    return [instance for instances in expanded.values() for instance in instances]


def order(*items: Component | Instance) -> None:
    """The default fiche, in page order: a bare component stands for its
    instance without arguments. The components known to the registry are the
    ones listed here."""
    DEFAULT[:] = [item if isinstance(item, Instance) else item.new() for item in items]
    COMPONENTS.clear()
    COMPONENTS.update({instance.name: instance.component for instance in DEFAULT})


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
