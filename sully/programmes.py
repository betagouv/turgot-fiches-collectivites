"""Programmes d'accompagnement de l'État dont une commune peut relever.

Les listes sont publiées par commune, chacune avec son propre en-tête. Pour ACV
la source retenue est la Caisse des Dépôts : la liste ANCT ne couvre que la
seconde vague, 50 communes contre 244.
"""

import csv
import io
from dataclasses import dataclass

import httpx

DATA_GOUV_URL = "https://www.data.gouv.fr/api/1/datasets"


@dataclass(frozen=True)
class Programme:
    code: str
    nom: str
    dataset: str
    colonne_libelle: str
    ressource: str | None = None
    colonne_date: str | None = None


PROGRAMMES = (
    Programme(
        code="ACV",
        nom="Action cœur de ville",
        dataset="5fa9901c66cff095591963e8",
        colonne_libelle="lib_acv",
        colonne_date="date_signature",
    ),
    Programme(
        code="PVD",
        nom="Petites villes de demain",
        dataset="5fc1259b703620ed60a49d97",
        colonne_libelle="lib_com",
        colonne_date="date_signature",
    ),
    Programme(
        code="TI",
        nom="Territoires d'industrie",
        dataset="5fc1472f114718d419e42f8a",
        colonne_libelle="lib_ti",
        ressource="communes couvertes",
    ),
    Programme(
        code="VA",
        nom="Villages d'avenir",
        dataset="65a11234a86f08c56f0c47b0",
        colonne_libelle="lib_com",
    ),
)


def _resource(client: httpx.Client, programme: Programme) -> dict:
    response = client.get(f"{DATA_GOUV_URL}/{programme.dataset}/")
    response.raise_for_status()
    fichiers = [
        r
        for r in response.json().get("resources", [])
        if r.get("format", "").lower() == "csv"
    ]
    if programme.ressource:
        fichiers = [
            r for r in fichiers if programme.ressource in r.get("title", "").lower()
        ]
    if not fichiers:
        raise ValueError(f"Aucune ressource CSV pour {programme.code}")
    return fichiers[0]


def lignes(client: httpx.Client, programme: Programme):
    ressource = _resource(client, programme)
    response = client.get(ressource["url"], follow_redirects=True)
    response.raise_for_status()
    texte = response.content.decode("utf-8-sig", errors="replace")
    entete = texte.split("\n", 1)[0]
    delimiteur = ";" if entete.count(";") > entete.count(",") else ","

    for row in csv.DictReader(io.StringIO(texte), delimiter=delimiteur):
        code_insee = (row.get("insee_com") or "").strip()
        if not code_insee:
            continue
        yield {
            "code_insee": code_insee,
            "programme": programme.code,
            "libelle": (row.get(programme.colonne_libelle) or "").strip(),
            "depuis": (row.get(programme.colonne_date) or "").strip()
            if programme.colonne_date
            else "",
        }
