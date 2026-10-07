"""Readers for the DGCL and Fonds vert opendata files published on data.gouv.fr."""

import csv
import io
import re
from collections import Counter
from hashlib import md5

import httpx

from .subventions import SOURCE_DGCL, SOURCE_FONDS_VERT

DATA_GOUV_URL = "https://www.data.gouv.fr/api/1/datasets"
DGCL_DATASET = "6176785207139a929a2776fe"
FONDS_VERT_DATASET = "fonds-vert-liste-des-projets-subventionnes"

DGCL_HEADER = (
    "exercice;dispositif;programme;beneficiaire_type;beneficiaire_siren;"
    "beneficiaire_dep;beneficiaire_nom;beneficiaire_code_insee;intitule;"
    "cout_ht;subvention;taux"
)

FONDS_VERT_DISPOSITIF = "FONDS VERT"
SIREN_COLUMNS = ("siret_beneficiaire", "siren")
NOM_COLUMNS = ("raison_sociale_beneficiaire", "nom_beneficiaire_principal")
DOSSIER_COLUMNS = ("numero_dossier_ds", "numero_ds")


def resources(client: httpx.Client, dataset: str) -> list[dict]:
    response = client.get(f"{DATA_GOUV_URL}/{dataset}/")
    response.raise_for_status()
    return [
        r
        for r in response.json().get("resources", [])
        if r.get("format", "").lower() == "csv"
    ]


def download(client: httpx.Client, url: str) -> str:
    response = client.get(url, follow_redirects=True)
    response.raise_for_status()
    return response.content.decode("utf-8-sig", errors="replace")


def _first(row: dict, names) -> str:
    for name in names:
        value = (row.get(name) or "").strip()
        if value:
            return value
    return ""


def _decimal(value) -> float | None:
    texte = (value or "").strip().replace(",", ".").replace(" ", "")
    texte = texte.replace(" ", "").replace("\xa0", "")
    if not texte:
        return None
    try:
        return float(texte)
    except ValueError:
        return None


def _identifiant(parts) -> str:
    return md5("|".join(parts).encode()).hexdigest()


def lignes_dgcl(text: str, rejets: Counter):
    entete = text.split("\n", 1)[0].strip()
    if entete != DGCL_HEADER:
        raise ValueError(f"En-tête DGCL inattendu : {entete}")

    vus = Counter()
    for row in csv.DictReader(io.StringIO(text), delimiter=";"):
        siren = row["beneficiaire_siren"].strip()
        dispositif = row["dispositif"].strip().upper()
        annee = row["exercice"].strip()
        if not siren:
            # La DGCL ne publie pas le SIREN des départements : la DSID sort
            # intégralement de l'assiette.
            rejets[dispositif or "?"] += 1
            continue
        if not (dispositif and annee.isdigit()):
            rejets["exercice ou dispositif manquant"] += 1
            continue

        libelle = (row["intitule"] or "").strip()
        # La DGCL ne publie aucun identifiant de ligne, et un même intitulé peut
        # revenir pour un même bénéficiaire la même année : le rang d'occurrence
        # distingue ces doublons sans les perdre.
        identite = (annee, dispositif, siren, libelle)
        vus[identite] += 1

        yield {
            "source": SOURCE_DGCL,
            "source_id": _identifiant((*identite, str(vus[identite]))),
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


def lignes_fonds_vert(text: str, annee: int, rejets: Counter):
    vus = Counter()
    for row in csv.DictReader(io.StringIO(text)):
        siren = _first(row, SIREN_COLUMNS)[:9]
        if not siren:
            rejets["sans SIREN"] += 1
            continue

        libelle = (row.get("nom_du_projet") or "").strip()
        identite = (str(annee), _first(row, DOSSIER_COLUMNS), siren, libelle)
        vus[identite] += 1

        yield {
            "source": SOURCE_FONDS_VERT,
            "source_id": _identifiant((*identite, str(vus[identite]))),
            "dispositif": FONDS_VERT_DISPOSITIF,
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


def annee_de(titre: str) -> int | None:
    trouve = re.search(r"20\d{2}", titre)
    return int(trouve.group()) if trouve else None


def porte_un_siren(text: str) -> bool:
    entete = text.split("\n", 1)[0]
    return any(colonne in entete for colonne in SIREN_COLUMNS)
