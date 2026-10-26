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

from . import database
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
{database.insert_statement("executif", COLUMNS)}
ON CONFLICT (fonction, code) DO UPDATE SET
nom = excluded.nom, prenom = excluded.prenom, depuis = excluded.depuis
WHERE excluded.depuis > executif.depuis
"""


class Fonction(StrEnum):
    MAIRE = "maire"
    PRESIDENT = "president"


@dataclass(frozen=True)
class File:
    fonction: Fonction
    title: str
    code_column: str
    function_label: str | None = None


FILES = (
    File(Fonction.MAIRE, "elus-maires-mai.csv", "Code de la commune"),
    File(
        Fonction.PRESIDENT,
        "elus-conseillers-communautaires-epci.csv",
        "N° SIREN",
        function_label="Président du conseil communautaire",
    ),
)


@dataclass
class Executif:
    fonction: Fonction
    nom: str
    prenom: str
    depuis: date | None


def _url(resources: list[dict], file: File) -> str:
    for resource in resources:
        if resource["title"] == file.title:
            return resource["url"]
    raise ValueError(f"Ressource {file.title} absente du jeu de données")


def _depuis(text: str) -> date | None:
    return date.fromisoformat(text) if text else None


def rows(client: httpx.Client, url: str, file: File):
    response = client.get(url, follow_redirects=True)
    response.raise_for_status()
    text = response.content.decode("utf-8-sig")
    for row in csv.DictReader(io.StringIO(text), delimiter=";"):
        label = file.function_label
        if label and row["Libellé de la fonction"] != label:
            continue
        yield {
            "fonction": file.fonction,
            "code": row[file.code_column],
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
def fetch(client: httpx.Client, connection: database.Connection) -> str:
    response = client.get(DATASET_URL)
    response.raise_for_status()
    resources = response.json()["resources"]
    urls = {file: _url(resources, file) for file in FILES}
    counts = []
    for file, url in urls.items():
        written = database.write(connection, INSERT, rows(client, url, file))
        counts.append(f"{written} {file.fonction}(s)")
    return ", ".join(counts)


def for_collectivite(
    connection: database.Connection, fonction: Fonction, code: str
) -> Executif | None:
    row = connection.execute(
        "SELECT fonction, nom, prenom, depuis FROM executif "
        "WHERE fonction = %s AND code = %s",
        (fonction, code),
    ).fetchone()
    return Executif(**row) if row else None
