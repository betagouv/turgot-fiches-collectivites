"""Les composants d'une fiche.

Chaque composant est un paquet qui porte sa collecte, décorée par `@component`,
et un gabarit par cible de rendu nommé d'après le dernier segment de son nom :
`identite/identite.typ`, `carto/financements/financements.js`. Un paquet
englobant peut porter des gabarits partagés par ses composants, comme
`carto/carto.typ`.
"""

from . import (  # noqa: F401
    chiffres,
    competences,
    historique,
    identite,
    programmes,
)
from .carto import financements  # noqa: F401
from .registry import (
    COMPONENTS,
    Access,
    Component,
    Download,
    Instance,
    InvalidParameter,
    UnknownComponent,
    ancestors,
    component,
    modules,
    order,
    rows,
    selected,
    template,
)

order(
    "identite",
    "programmes",
    "carto.financements(perimeter=departement)",
    "carto.financements(perimeter=interco)",
    "chiffres",
    "historique",
    "competences",
)

__all__ = [
    "COMPONENTS",
    "Access",
    "Component",
    "Download",
    "Instance",
    "InvalidParameter",
    "UnknownComponent",
    "ancestors",
    "component",
    "modules",
    "order",
    "rows",
    "selected",
    "template",
]
