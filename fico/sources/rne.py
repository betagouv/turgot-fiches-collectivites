"""Répertoire national des élus, publié par le ministère de l'Intérieur : les
maires et les présidents de conseil communautaire, avec leur date de prise de
fonction.

Un exécutif est rangé sous le code qui désigne sa collectivité dans le fichier :
le code INSEE pour un maire, le SIREN pour un président d'EPCI.

https://www.data.gouv.fr/datasets/repertoire-national-des-elus-1
"""

import csv
import io
from dataclasses import dataclass
from datetime import date
from enum import StrEnum

import httpx

from . import base
from .registry import Schedule, source

DATASET_URL = "https://www.data.gouv.fr/api/1/datasets/5c34c4d1634f4173183a64f1/"

SCHEMA = """
CREATE TABLE IF NOT EXISTS executif (
    fonction TEXT NOT NULL,
    code     TEXT NOT NULL,
    nom      TEXT NOT NULL,
    prenom   TEXT NOT NULL,
    depuis   DATE,
    PRIMARY KEY (fonction, code)
);
"""

COLUMNS = ("fonction", "code", "nom", "prenom", "depuis")

# Upstream files two EPCI under one SIREN: the latest president wins.
INSERT = f"""
INSERT INTO executif ({", ".join(COLUMNS)})
VALUES ({", ".join(f"%({c})s" for c in COLUMNS)})
ON CONFLICT (fonction, code) DO UPDATE SET
nom = excluded.nom, prenom = excluded.prenom, depuis = excluded.depuis
WHERE excluded.depuis > executif.depuis
"""


class Fonction(StrEnum):
    MAIRE = "maire"
    PRESIDENT = "president"


@dataclass(frozen=True)
class Fichier:
    fonction: Fonction
    titre: str
    colonne_code: str
    libelle_fonction: str | None = None


FICHIERS = (
    Fichier(Fonction.MAIRE, "elus-maires-mai.csv", "Code de la commune"),
    Fichier(
        Fonction.PRESIDENT,
        "elus-conseillers-communautaires-epci.csv",
        "N° SIREN",
        libelle_fonction="Président du conseil communautaire",
    ),
)


@dataclass
class Executif:
    fonction: Fonction
    nom: str
    prenom: str
    depuis: date | None


def _url(resources: list[dict], fichier: Fichier) -> str:
    for resource in resources:
        if resource["title"] == fichier.titre:
            return resource["url"]
    raise ValueError(f"Ressource {fichier.titre} absente du jeu de données")


def _depuis(text: str) -> date | None:
    return date.fromisoformat(text) if text else None


def rows(client: httpx.Client, url: str, fichier: Fichier):
    response = client.get(url, follow_redirects=True)
    response.raise_for_status()
    text = response.content.decode("utf-8-sig")
    for row in csv.DictReader(io.StringIO(text), delimiter=";"):
        libelle = fichier.libelle_fonction
        if libelle and row["Libellé de la fonction"] != libelle:
            continue
        yield {
            "fonction": fichier.fonction,
            "code": row[fichier.colonne_code],
            "nom": row["Nom de l'élu"],
            "prenom": row["Prénom de l'élu"],
            "depuis": _depuis(row["Date de début de la fonction"]),
        }


@source(
    name="rne",
    label="data.gouv.fr, Répertoire national des élus (ministère de l'Intérieur) "
    ": maires et présidents d'EPCI",
    schedule=Schedule.MONTHLY,
    schema=SCHEMA,
)
def fetch(client: httpx.Client, connection: base.Connection) -> str:
    response = client.get(DATASET_URL)
    response.raise_for_status()
    resources = response.json()["resources"]
    urls = {fichier: _url(resources, fichier) for fichier in FICHIERS}
    counts = []
    with connection.transaction():
        connection.execute("DELETE FROM executif")
        for fichier, url in urls.items():
            written = base.upsert(connection, INSERT, rows(client, url, fichier))
            counts.append(f"{written} {fichier.fonction}(s)")
    return ", ".join(counts)


def de_collectivite(
    connection: base.Connection, fonction: Fonction, code: str
) -> Executif | None:
    row = connection.execute(
        "SELECT fonction, nom, prenom, depuis FROM executif "
        "WHERE fonction = %s AND code = %s",
        (fonction, code),
    ).fetchone()
    return Executif(**row) if row else None
