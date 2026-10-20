"""Les composants d'une fiche.

Chaque composant est un paquet qui porte sa collecte, décorée par `@component`,
et un gabarit par cible de rendu nommé d'après le dernier segment de son nom :
`identite/identite.typ`, `financements/carte/carte.js`. Les gabarits partagés
sont à la racine : `common.typ` et `common.js`, `carto.typ` et `carto.js`.
"""

from . import (  # noqa: F401
    competences,
    identite,
    programmes,
)
from .financements import (  # noqa: F401
    annuel,
    carte,
    financeurs,
    historique,
    par_habitant,
    synthese,
)
from .registry import (
    COMPONENTS,
    Access,
    Component,
    Download,
    Instance,
    InvalidParameter,
    UnknownComponent,
    component,
    order,
    rows,
    selected,
    template,
)

order(
    "identite",
    "programmes",
    "financements.carte(perimeter=departement)",
    "financements.carte(perimeter=interco)",
    "financements.synthese",
    "financements.synthese(financeur=DSIL)",
    "financements.synthese(financeur=DETR)",
    "financements.synthese(financeur=Fonds Vert)",
    "financements.annuel",
    "financements.financeurs",
    "financements.par_habitant",
    "financements.historique",
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
    "component",
    "order",
    "rows",
    "selected",
    "template",
]
