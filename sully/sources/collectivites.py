"""Les collectivités : communes et groupements dans une même table, indexée par
SIREN, alimentée par `geoapi` et `banatic`."""

from dataclasses import dataclass, field
from datetime import date

from . import base

COMMUNE = "commune"
GROUPEMENT = "groupement"

SCHEMA = """
CREATE TABLE IF NOT EXISTS collectivite (
    siren            TEXT PRIMARY KEY,
    famille          TEXT NOT NULL,
    nom              TEXT NOT NULL,
    type             TEXT NOT NULL,
    code_insee       TEXT UNIQUE,
    population       INTEGER,
    superficie       DOUBLE PRECISION,
    codes_postaux    TEXT[] NOT NULL DEFAULT '{}',
    code_epci        TEXT,
    nom_epci         TEXT,
    code_departement TEXT,
    nom_departement  TEXT,
    code_region      TEXT,
    nom_region       TEXT,
    mode_financement TEXT,
    date_creation    DATE
);
CREATE INDEX IF NOT EXISTS collectivite_famille ON collectivite (famille);

CREATE TABLE IF NOT EXISTS competence (
    siren TEXT NOT NULL REFERENCES collectivite (siren) ON DELETE CASCADE,
    rang  INTEGER NOT NULL,
    nom   TEXT NOT NULL,
    PRIMARY KEY (siren, rang)
);
"""


class NotFound(Exception):
    pass


@dataclass
class Fiche:
    """A row of `collectivite`: communes and groupements share one shape."""

    siren: str
    famille: str
    nom: str
    type: str
    code_insee: str | None = None
    population: int | None = None
    superficie: float | None = None
    codes_postaux: list[str] = field(default_factory=list)
    code_epci: str | None = None
    nom_epci: str | None = None
    code_departement: str | None = None
    nom_departement: str | None = None
    code_region: str | None = None
    nom_region: str | None = None
    mode_financement: str | None = None
    date_creation: date | None = None


def _fiche(row: dict | None, identifiant: str) -> Fiche:
    if row is None:
        raise NotFound(identifiant)
    return Fiche(**row)


def par_code_insee(connection: base.Connection, code_insee: str) -> Fiche:
    row = connection.execute(
        "SELECT * FROM collectivite WHERE code_insee = %s", (code_insee,)
    ).fetchone()
    return _fiche(row, code_insee)


def par_siren(connection: base.Connection, siren: str) -> Fiche:
    row = connection.execute(
        "SELECT * FROM collectivite WHERE siren = %s", (siren,)
    ).fetchone()
    return _fiche(row, siren)


def competences(connection: base.Connection, siren: str) -> list[str]:
    rows = connection.execute(
        "SELECT nom FROM competence WHERE siren = %s ORDER BY rang", (siren,)
    ).fetchall()
    return [row["nom"] for row in rows]
