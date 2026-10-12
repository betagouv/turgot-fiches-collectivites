"""Les composants d'une fiche.

Chaque composant est un paquet qui porte sa collecte, décorée par `@component`,
et un gabarit par cible de rendu nommé d'après lui : `identite.typ` aujourd'hui,
`identite.html` le jour venu.
"""

from . import (  # noqa: F401
    carto,
    chiffres,
    competences,
    historique,
    identite,
    programmes,
)
from .registry import (
    COMPONENTS,
    Access,
    Component,
    UnknownComponent,
    Width,
    component,
    names,
    order,
    rows,
    selected,
)

order(
    "identite",
    "programmes",
    "carto",
    "chiffres",
    "historique",
    "competences",
)

__all__ = [
    "COMPONENTS",
    "Access",
    "Component",
    "UnknownComponent",
    "Width",
    "component",
    "names",
    "order",
    "rows",
    "selected",
]
