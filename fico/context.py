from dataclasses import dataclass

from .sources.collectivites import Fiche
from .sources.database import Connection


@dataclass
class Context:
    """What a component has at hand to collect what it displays."""

    fiche: Fiche
    connection: Connection
