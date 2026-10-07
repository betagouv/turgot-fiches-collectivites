import sqlite3
from dataclasses import dataclass, field

import httpx

from .sources.referentiel import Fiche


@dataclass
class Context:
    """Ce dont un composant dispose pour collecter ce qu'il affiche."""

    client: httpx.AsyncClient
    fiche: Fiche
    connection: sqlite3.Connection | None
    components: tuple[str, ...]


@dataclass
class Result:
    """Ce qu'un composant produit : ses données, et les fichiers que son rendu
    lit.

    `files` sert aux composants dont le gabarit charge autre chose que `data`,
    la cartographie lisant ses contours en GeoJSON.
    """

    data: object
    files: dict[str, str] = field(default_factory=dict)
