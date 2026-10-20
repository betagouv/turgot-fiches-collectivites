"""Les collectivités : les communes de `geoapi` et les groupements de `banatic`,
lus sous une même forme, une ligne par SIREN."""

from dataclasses import dataclass, field
from datetime import date

from . import base

COMMUNE = "commune"
GROUPEMENT = "groupement"
EPCI_A_FISCALITE_PROPRE = ["CC", "CA", "CU", "METRO", "MET69"]


class NotFound(Exception):
    pass


@dataclass
class Fiche:
    """A commune or a groupement: both share one shape, the fields the other
    kind lacks left to their default."""

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


def _commune(connection: base.Connection, column: str, value: str) -> Fiche | None:
    row = connection.execute(
        f"SELECT * FROM commune WHERE {column} = %s", (value,)
    ).fetchone()
    return Fiche(famille=COMMUNE, type="COM", **row) if row else None


def _groupement(connection: base.Connection, siren: str) -> Fiche | None:
    row = connection.execute(
        "SELECT * FROM groupement WHERE siren = %s", (siren,)
    ).fetchone()
    return Fiche(famille=GROUPEMENT, **row) if row else None


def par_code_insee(connection: base.Connection, code_insee: str) -> Fiche:
    fiche = _commune(connection, "code_insee", code_insee)
    if fiche is None:
        raise NotFound(code_insee)
    return fiche


def par_siren(connection: base.Connection, siren: str) -> Fiche:
    fiche = _commune(connection, "siren", siren) or _groupement(connection, siren)
    if fiche is None:
        raise NotFound(siren)
    return fiche


def communes_de_epci(connection: base.Connection, code_epci: str) -> list[dict]:
    """The communes `code_epci` gathers: siren, code_insee, nom, population."""
    return connection.execute(
        "SELECT siren, code_insee, nom, population FROM commune WHERE code_epci = %s",
        (code_epci,),
    ).fetchall()


def epci_du_departement(
    connection: base.Connection, code_departement: str
) -> list[dict]:
    """The EPCI à fiscalité propre seated in `code_departement`: siren, nom,
    population."""
    return connection.execute(
        "SELECT siren, nom, population FROM groupement "
        "WHERE code_departement = %s AND type = ANY(%s)",
        (code_departement, EPCI_A_FISCALITE_PROPRE),
    ).fetchall()


def competences(connection: base.Connection, siren: str) -> list[str]:
    rows = connection.execute(
        "SELECT nom FROM competence WHERE siren = %s ORDER BY rang", (siren,)
    ).fetchall()
    return [row["nom"] for row in rows]
