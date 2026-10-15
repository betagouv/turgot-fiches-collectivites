"""Les composants d'une fiche.

Chaque composant est un paquet qui porte sa collecte, décorée par `@component`,
et un gabarit par cible de rendu nommé d'après le dernier segment de son nom :
`identite/identite.typ`, `carto/financements/departement/departement.js`. Un
paquet englobant peut porter des gabarits partagés par ses composants, comme
`carto/financements/financements.typ`.
"""

from . import (  # noqa: F401
    chiffres,
    competences,
    historique,
    identite,
    programmes,
)
from .carto.financements import departement, interco  # noqa: F401
from .registry import (
    COMPONENTS,
    Access,
    Component,
    InvalidParameter,
    UnknownComponent,
    ancestors,
    arguments,
    component,
    modules,
    names,
    order,
    rows,
    selected,
    template,
)

order(
    "identite",
    "programmes",
    "carto.financements.departement",
    "carto.financements.interco",
    "chiffres",
    "historique",
    "competences",
)

__all__ = [
    "COMPONENTS",
    "Access",
    "Component",
    "InvalidParameter",
    "UnknownComponent",
    "ancestors",
    "arguments",
    "component",
    "modules",
    "names",
    "order",
    "rows",
    "selected",
    "template",
]
