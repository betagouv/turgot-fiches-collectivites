"""Projets subventionnés par le Fonds vert.

https://www.data.gouv.fr/datasets/fonds-vert-liste-des-projets-subventionnes
"""

import csv
import io
import re
import sqlite3
from collections import Counter
from hashlib import md5

import httpx

from . import base, datagouv, subventions
from .registry import Schedule, source

DATASET = "fonds-vert-liste-des-projets-subventionnes"
DISPOSITIF = "FONDS VERT"

SIREN_COLUMNS = ("siret_beneficiaire", "siren")
NOM_COLUMNS = ("raison_sociale_beneficiaire", "nom_beneficiaire_principal")
DOSSIER_COLUMNS = ("numero_dossier_ds", "numero_ds")


def _first(row: dict, names) -> str:
    for name in names:
        value = (row.get(name) or "").strip()
        if value:
            return value
    return ""


def _decimal(value) -> float | None:
    text = (value or "").strip().replace(",", ".").replace(" ", "")
    text = text.replace(" ", "").replace("\xa0", "")
    if not text:
        return None
    try:
        return float(text)
    except ValueError:
        return None


def rows(text: str, annee: int, skipped: Counter):
    seen = Counter()
    for row in csv.DictReader(io.StringIO(text)):
        siren = _first(row, SIREN_COLUMNS)[:9]
        if not siren:
            skipped["sans SIREN"] += 1
            continue

        libelle = (row.get("nom_du_projet") or "").strip()
        identity = (str(annee), _first(row, DOSSIER_COLUMNS), siren, libelle)
        seen[identity] += 1

        yield {
            "source": subventions.SOURCE_FONDS_VERT,
            "source_id": md5(
                "|".join((*identity, str(seen[identity]))).encode()
            ).hexdigest(),
            "dispositif": DISPOSITIF,
            "annee": annee,
            "siren": siren,
            "beneficiaire_nom": _first(row, NOM_COLUMNS),
            "code_insee": (row.get("code_commune") or "").strip(),
            "code_departement": (row.get("code_departement") or "").strip(),
            "libelle": libelle,
            # L'opendata Fonds vert ne publie que le montant engagé.
            "cout_total": None,
            "montant_accorde": _decimal(row.get("montant_engage")),
        }


def _year_of(title: str) -> int | None:
    found = re.search(r"20\d{2}", title)
    return int(found.group()) if found else None


def _carries_siren(text: str) -> bool:
    header = text.split("\n", 1)[0]
    return any(column in header for column in SIREN_COLUMNS)


@source(
    name="fonds-vert",
    label="Subventions Fonds vert",
    schedule=Schedule.MONTHLY,
    schema=subventions.SCHEMA,
)
def fetch(client: httpx.Client, connection: sqlite3.Connection) -> str:
    written = 0
    ignored = 0
    skipped = Counter()
    for resource in datagouv.resources(client, DATASET):
        annee = _year_of(resource["title"])
        if annee is None:
            ignored += 1
            continue
        text = datagouv.download(client, resource["url"])
        if not _carries_siren(text):
            ignored += 1
            continue
        written += base.upsert(
            connection, subventions.UPSERT, rows(text, annee, skipped)
        )
    return (
        f"{written} ligne(s), {sum(skipped.values())} écartée(s), "
        f"{ignored} fichier(s) ignoré(s)"
    )
