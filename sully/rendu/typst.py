"""Assemble les blocs demandés en un document Typst, puis le compile.

Les imports Typst sont statiques : le gabarit racine est donc écrit à la
compilation, avec les seuls blocs retenus.
"""

import json
import shutil
from pathlib import Path
from tempfile import TemporaryDirectory

import typst

from .. import blocs as registre

COMMUN = Path(registre.__file__).parent / "commun.typ"
RACINE = "fiche.typ"

GABARIT = """#import "commun.typ": cartouches, entete, theme
{imports}

#let data = json("data.json")

#show: theme.with(source: data.source)

#entete(data.nom, data.libelle_type)

#cartouches(({cartouches}))
{sections}
"""


def _document(noms_cartouches: list[str], noms_sections: list[str]) -> str:
    imports = "\n".join(
        f'#import "{nom}.typ" as {nom}' for nom in noms_cartouches + noms_sections
    )
    cartouches = "".join(f"{nom}.rendu(data.blocs.{nom}), " for nom in noms_cartouches)
    sections = "\n".join(f"#{nom}.rendu(data.blocs.{nom})" for nom in noms_sections)
    return GABARIT.format(imports=imports, cartouches=cartouches, sections=sections)


def compile_fiche(entete: dict, resultats: dict) -> bytes:
    """`resultats` associe un nom de bloc à son `Resultat`, dans l'ordre voulu."""
    cartouches, sections = [], []
    for nom in resultats:
        place = registre.PAR_NOM[nom].PLACEMENT
        (cartouches if place == "cartouche" else sections).append(nom)

    with TemporaryDirectory() as tmp:
        build = Path(tmp)
        shutil.copy(COMMUN, build / "commun.typ")
        for nom, resultat in resultats.items():
            bloc = registre.PAR_NOM[nom]
            shutil.copy(bloc.DOSSIER / f"{nom}.typ", build / f"{nom}.typ")
            for fichier, contenu in resultat.fichiers.items():
                (build / fichier).write_text(contenu)

        donnees = {nom: resultat.donnees for nom, resultat in resultats.items()}
        (build / "data.json").write_text(
            json.dumps({**entete, "blocs": donnees}, ensure_ascii=False)
        )
        (build / RACINE).write_text(_document(cartouches, sections))
        return typst.compile(build / RACINE)
