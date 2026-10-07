import sqlite3
from dataclasses import dataclass, field

import httpx

from .sources.referentiel import Fiche


@dataclass
class Contexte:
    """Ce dont un bloc dispose pour collecter ce qu'il affiche."""

    client: httpx.AsyncClient
    fiche: Fiche
    connection: sqlite3.Connection | None
    blocs: tuple[str, ...]


@dataclass
class Resultat:
    """Ce qu'un bloc produit : ses données, et les fichiers que son rendu lit.

    `fichiers` sert aux blocs dont le gabarit charge autre chose que `donnees`,
    la cartographie lisant ses contours en GeoJSON.
    """

    donnees: object
    fichiers: dict[str, str] = field(default_factory=dict)
