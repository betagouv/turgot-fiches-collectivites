"""Les composants d'une fiche.

Chaque composant est un paquet qui porte sa collecte, décorée par `@component`,
et un gabarit par cible de rendu nommé d'après lui : `identite.typ` aujourd'hui,
`identite.html` le jour venu.
"""

from . import (  # noqa: F401
    carto,
    chiffres,
    competences,
    identite,
    programmes,
    subventions,
)
from .registry import (
    COMPONENTS,
    Access,
    Component,
    Placement,
    UnknownComponent,
    component,
    names,
    order,
    selected,
)

order(
    "identite",
    "programmes",
    "carto",
    "chiffres",
    "subventions",
    "competences",
)

__all__ = [
    "COMPONENTS",
    "Access",
    "Component",
    "Placement",
    "UnknownComponent",
    "component",
    "names",
    "order",
    "selected",
]
