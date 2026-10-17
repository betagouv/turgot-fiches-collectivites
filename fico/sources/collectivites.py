"""Les collectivités : les communes de `geoapi` et les groupements de `banatic`,
lus ensemble à travers la vue `collectivite`, une ligne par SIREN."""

from dataclasses import dataclass, field
from datetime import date

from . import base
from .registry import view

COMMUNE = "commune"
GROUPEMENT = "groupement"

view(f"""
CREATE OR REPLACE VIEW collectivite AS
SELECT siren, '{COMMUNE}' AS famille, nom, 'COM' AS type, code_insee, population,
       superficie, codes_postaux, code_epci, nom_epci, code_departement,
       nom_departement, code_region, nom_region,
       NULL::text AS mode_financement, NULL::date AS date_creation
FROM commune
UNION ALL
SELECT siren, '{GROUPEMENT}', nom, type, NULL, population,
       NULL, '{{}}', NULL, NULL, code_departement,
       nom_departement, NULL, NULL,
       mode_financement, date_creation
FROM groupement
""")


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
