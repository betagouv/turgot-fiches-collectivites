from pathlib import Path

from ...contexte import Contexte, Resultat
from ...sources import geo
from ...sources.referentiel import COMMUNE

NOM = "identite"
PLACEMENT = "cartouche"
DOSSIER = Path(__file__).parent


def _nombre(valeur) -> str:
    return f"{valeur:,}".replace(",", " ")


async def collecte(contexte: Contexte) -> Resultat | None:
    fiche = contexte.fiche
    lignes = [("SIREN", fiche.siren)]

    if fiche.famille != COMMUNE:
        lignes += [
            ("Type", fiche.type),
            ("Mode de financement", fiche.mode_financement),
            ("Date de création", fiche.date_creation),
            ("Départements", ", ".join(fiche.departements)),
        ]
        return Resultat(donnees=[p for p in lignes if p[1]])

    details = await geo.commune(contexte.client, fiche.code_insee)
    surface = details["surface"] / 100 if details.get("surface") else None

    lignes.append(("Code INSEE", fiche.code_insee))
    if fiche.population is not None:
        lignes.append(("Population", f"{_nombre(fiche.population)} habitants"))
    if surface:
        lignes.append(("Superficie", f"{surface:.1f}".replace(".", ",") + " km²"))
        if fiche.population is not None:
            densite = round(fiche.population / surface)
            lignes.append(("Densité", f"{_nombre(densite)} hab./km²"))
    lignes += [
        ("Codes postaux", ", ".join(fiche.codes_postaux)),
        ("Département", fiche.code_departement),
        ("Région", fiche.code_region),
    ]
    return Resultat(donnees=[p for p in lignes if p[1]])
