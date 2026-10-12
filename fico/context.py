from dataclasses import dataclass, field

from .sources.base import Connection
from .sources.collectivites import Fiche


@dataclass
class Context:
    """What a component has at hand to collect what it displays."""

    fiche: Fiche
    connection: Connection
    components: tuple[str, ...]


@dataclass
class Result:
    """What a component produces: its data, and the files its templates read.

    `data` is the component's contract with every renderer: values are computed
    here, templates only lay them out.
    """

    data: object
    files: dict[str, str] = field(default_factory=dict)
