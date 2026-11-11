from dataclasses import dataclass

from .sources.collectivites import Fiche


@dataclass
class Context:
    """What a component has at hand to collect what it displays."""

    fiche: Fiche
