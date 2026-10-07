"""Projets financés par la DETR, la DSIL et la DPV, publiés par la DGCL.

https://www.data.gouv.fr/datasets/6176785207139a929a2776fe
"""

import csv
import io
import sqlite3
from collections import Counter
from hashlib import md5

import httpx

from . import base, datagouv, subventions
from .registry import source

DATASET = "6176785207139a929a2776fe"

HEADER = (
    "exercice;dispositif;programme;beneficiaire_type;beneficiaire_siren;"
    "beneficiaire_dep;beneficiaire_nom;beneficiaire_code_insee;intitule;"
    "cout_ht;subvention;taux"
)


def _decimal(value) -> float | None:
    text = (value or "").strip().replace(",", ".").replace(" ", "")
    text = text.replace(" ", "").replace("\xa0", "")
    if not text:
        return None
    try:
        return float(text)
    except ValueError:
        return None


def rows(text: str, skipped: Counter):
    header = text.split("\n", 1)[0].strip()
    if header != HEADER:
        raise ValueError(f"En-tête DGCL inattendu : {header}")

    seen = Counter()
    for row in csv.DictReader(io.StringIO(text), delimiter=";"):
        siren = row["beneficiaire_siren"].strip()
        dispositif = row["dispositif"].strip().upper()
        annee = row["exercice"].strip()
        if not siren:
            # La DGCL ne publie pas le SIREN des départements : la DSID sort
            # intégralement de l'assiette.
            skipped[dispositif or "?"] += 1
            continue
        if not (dispositif and annee.isdigit()):
            skipped["exercice ou dispositif manquant"] += 1
            continue

        libelle = (row["intitule"] or "").strip()
        # La DGCL ne publie aucun identifiant de ligne, et un même intitulé peut
        # revenir pour un même bénéficiaire la même année : le rang d'occurrence
        # distingue ces doublons sans les perdre.
        identity = (annee, dispositif, siren, libelle)
        seen[identity] += 1

        yield {
            "source": subventions.SOURCE_DGCL,
            "source_id": md5(
                "|".join((*identity, str(seen[identity]))).encode()
            ).hexdigest(),
            "dispositif": dispositif,
            "annee": int(annee),
            "siren": siren,
            "beneficiaire_nom": (row["beneficiaire_nom"] or "").strip(),
            "code_insee": (row["beneficiaire_code_insee"] or "").strip(),
            "code_departement": (row["beneficiaire_dep"] or "").strip(),
            "libelle": libelle,
            "cout_total": _decimal(row["cout_ht"]),
            "montant_accorde": _decimal(row["subvention"]),
        }


@source(
    name="dgcl",
    label="Subventions DETR, DSIL et DPV",
    schedule=source.MONTHLY,
    schema=subventions.SCHEMA,
)
def fetch(client: httpx.Client, connection: sqlite3.Connection) -> str:
    written = 0
    skipped = Counter()
    for resource in datagouv.resources(client, DATASET):
        text = datagouv.download(client, resource["url"])
        written += base.upsert(connection, subventions.UPSERT, rows(text, skipped))
    detail = ", ".join(f"{motif} {n}" for motif, n in skipped.most_common(3))
    return f"{written} ligne(s), {sum(skipped.values())} écartée(s) ({detail}…)"
