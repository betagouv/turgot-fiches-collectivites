"""Les composants d'une fiche.

Chaque composant est un paquet qui porte sa collecte, décorée par `@component`,
et un gabarit par cible de rendu nommé d'après le dernier segment de son nom :
`identite/identite.typ`, `financements/carte/carte.js`. Les gabarits partagés
sont à la racine : `common.typ` et `common.js`, `carto.typ` et `carto.js`.
"""

from .competences import competences
from .financements.annuel import annuel
from .financements.carte import carte
from .financements.financeurs import financeurs
from .financements.historique import historique
from .financements.par_habitant import par_habitant
from .financements.synthese import synthese
from .identite import identite
from .programmes import programmes
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
from .table import Table

order(
    identite,
    programmes,
    carte.new(perimeter="departement"),
    carte.new(perimeter="interco"),
    synthese,
    synthese.new(financeur="DSIL"),
    synthese.new(financeur="DETR"),
    synthese.new(financeur="Fonds Vert"),
    annuel,
    financeurs,
    par_habitant,
    historique,
    competences,
)

__all__ = [
    "COMPONENTS",
    "Access",
    "Component",
    "Download",
    "Instance",
    "InvalidParameter",
    "Table",
    "UnknownComponent",
    "component",
    "order",
    "rows",
    "selected",
    "template",
]
