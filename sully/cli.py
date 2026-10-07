import argparse
import asyncio
import sys
from pathlib import Path

import httpx

from . import sources
from .blocs import NOMS, BlocInconnu, normalise
from .fiche import IdentifiantInvalide, collect, render
from .sources import base
from .sources.referentiel import NotFound


async def construit(identifiant: str, output_path: Path, blocs) -> Path:
    async with httpx.AsyncClient(timeout=120) as client:
        entete, resultats = await collect(client, identifiant, blocs)
    output_path.write_bytes(render(entete, resultats))
    return output_path


def commande_fiche(args) -> None:
    try:
        blocs = normalise(args.blocs)
    except BlocInconnu as erreur:
        sys.exit(str(erreur))

    output_path = args.output or Path(f"{args.identifiant}.pdf")
    try:
        written = asyncio.run(construit(args.identifiant, output_path, blocs))
    except IdentifiantInvalide as erreur:
        sys.exit(str(erreur))
    except NotFound:
        sys.exit(f"Aucune collectivité connue pour {args.identifiant}.")
    print(written)


def commande_fetch(args) -> None:
    try:
        choisies = sources.selected(args.sources)
    except sources.UnknownSource as erreur:
        sys.exit(str(erreur))

    connection = base.connect()
    with httpx.Client(timeout=300, follow_redirects=True) as client:
        for source in choisies:
            if not args.force and not base.is_due(connection, source):
                precedent = base.last_fetch(connection, source.name)
                print(f"  {source.name:12} à jour ({precedent:%d/%m/%Y})")
                continue
            print(f"  {source.name:12} récupération…", flush=True)
            rapport = source.fetch(client, connection)
            base.record_fetch(connection, source.name, rapport)
            print(f"  {source.name:12} {rapport}")
    print(base.DB_PATH)


def main(argv=None):
    parser = argparse.ArgumentParser(
        prog="sully",
        description="Fiches de collectivité et données qui les nourrissent.",
    )
    sous = parser.add_subparsers(dest="commande", required=True)

    fiche = sous.add_parser("fiche", help="Génère la fiche PDF d'une collectivité.")
    fiche.add_argument(
        "identifiant",
        help="Code INSEE d'une commune (5 caractères) "
        "ou SIREN d'une commune ou d'un groupement (9 chiffres)",
    )
    fiche.add_argument(
        "-o",
        "--output",
        type=Path,
        help="Fichier de sortie (défaut : <identifiant>.pdf)",
    )
    fiche.add_argument(
        "-b",
        "--blocs",
        help="Blocs à afficher, séparés par des virgules (défaut : tous). "
        f"Disponibles : {', '.join(NOMS)}",
    )
    fiche.set_defaults(fonction=commande_fiche)

    fetch = sous.add_parser("fetch", help="Récupère les données dont le rythme est dû.")
    fetch.add_argument(
        "sources",
        nargs="?",
        help="Sources à récupérer, séparées par des virgules (défaut : toutes). "
        f"Disponibles : {', '.join(sources.SOURCES)}",
    )
    fetch.add_argument(
        "-f",
        "--force",
        action="store_true",
        help="Récupère même si le rythme n'est pas échu",
    )
    fetch.set_defaults(fonction=commande_fetch)

    args = parser.parse_args(argv)
    args.fonction(args)


if __name__ == "__main__":
    main()
