from pathlib import Path

from ...contexte import Contexte, Resultat
from ...sources import base

NOM = "chiffres"
PLACEMENT = "section"
DOSSIER = Path(__file__).parent

DISPOSITIFS_PRINCIPAUX = ("DETR", "DSIL")


def euros(montant) -> str:
    return f"{round(montant):,}".replace(",", " ") + " €"


async def collecte(contexte: Contexte) -> Resultat | None:
    if contexte.connection is None:
        return None
    siren = contexte.fiche.siren
    par_dispositif = [
        (ligne["dispositif"], ligne["montant"] or 0, ligne["projets"])
        for ligne in base.totaux_par_dispositif(contexte.connection, siren)
    ]
    if not par_dispositif:
        return None

    cumul = {}
    for ligne in base.totaux_par_annee(contexte.connection, siren):
        cumul[ligne["annee"]] = cumul.get(ligne["annee"], 0) + (ligne["montant"] or 0)
    annees = sorted(cumul)

    cofinancement = base.cofinancement(contexte.connection, siren)
    cout = cofinancement["cout"] or 0
    taux = cofinancement["montant"] / cout if cout else None

    montants = {nom: montant for nom, montant, _ in par_dispositif}
    total = sum(montants.values())
    principaux = sum(montants.get(d, 0) for d in DISPOSITIFS_PRINCIPAUX)
    fonds_vert = montants.get("FONDS VERT", 0)

    return Resultat(
        donnees={
            "periode": f"{annees[0]} – {annees[-1]}",
            "tuiles": [
                (
                    euros(total),
                    "accordés, tous dispositifs",
                    str(sum(p for _, _, p in par_dispositif)),
                    "projets subventionnés",
                ),
                (
                    euros(montants.get("DETR", 0)),
                    "de DETR",
                    euros(montants.get("DSIL", 0)),
                    "de DSIL",
                ),
                (
                    euros(fonds_vert),
                    "de Fonds vert",
                    euros(total - principaux - fonds_vert),
                    "autres dotations",
                ),
                (
                    euros(cout),
                    "de coût de projet",
                    f"{taux:.0%}".replace("%", " %") if taux else "—",
                    "de taux de financement",
                ),
            ],
            "annees": annees,
            "montants": [cumul[annee] for annee in annees],
            "dispositifs": [
                {"nom": nom, "montant": montant} for nom, montant, _ in par_dispositif
            ],
        }
    )
