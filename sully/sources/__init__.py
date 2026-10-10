"""Les données consommées par les fiches : d'où elles viennent, où elles sont
stockées, comment elles se relisent.

Importer ce paquet enregistre les sources auprès du registre.
"""

from . import (
    api_collectivites,
    contours,
    dgcl,
    fonds_vert,
    geo,
    programmes,
    subventions,
)
from .registry import SOURCES, Source, UnknownSource, schemas, selected, source

__all__ = [
    "SOURCES",
    "Source",
    "UnknownSource",
    "api_collectivites",
    "contours",
    "dgcl",
    "fonds_vert",
    "geo",
    "programmes",
    "schemas",
    "selected",
    "source",
    "subventions",
]
