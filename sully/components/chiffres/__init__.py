from ...context import Context, Result
from ...sources import subventions
from ..registry import component

DISPOSITIFS_PRINCIPAUX = ("DETR", "DSIL")


def euros(montant) -> str:
    return f"{round(montant):,}".replace(",", " ") + " €"


@component(name="chiffres")
async def collect(context: Context) -> Result | None:
    if context.connection is None:
        return None
    siren = context.fiche.siren
    par_dispositif = [
        (ligne["dispositif"], ligne["montant"] or 0, ligne["projets"])
        for ligne in subventions.totaux_par_dispositif(context.connection, siren)
    ]
    if not par_dispositif:
        return None

    cumul = {}
    for ligne in subventions.totaux_par_annee(context.connection, siren):
        cumul[ligne["annee"]] = cumul.get(ligne["annee"], 0) + (ligne["montant"] or 0)
    annees = sorted(cumul)

    cofinancement = subventions.cofinancement(context.connection, siren)
    cout = cofinancement["cout"] or 0
    taux = cofinancement["montant"] / cout if cout else None

    montants = {nom: montant for nom, montant, _ in par_dispositif}
    total = sum(montants.values())
    principaux = sum(montants.get(d, 0) for d in DISPOSITIFS_PRINCIPAUX)
    fonds_vert = montants.get("FONDS VERT", 0)

    return Result(
        data={
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
