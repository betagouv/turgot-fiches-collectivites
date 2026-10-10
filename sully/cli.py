import argparse
import asyncio
import sys
from inspect import signature
from pathlib import Path

import httpx

from . import components, sources
from .fiche import IdentifiantInvalide, collect, render
from .sources import base
from .sources.referentiel import NotFound
from .sources.registry import Interrupted


async def build(identifiant: str, output_path: Path, chosen) -> Path:
    async with httpx.AsyncClient(timeout=120) as client:
        header, results = await collect(client, identifiant, chosen)
    output_path.write_bytes(render(header, results))
    return output_path


def command_fiche(args) -> None:
    try:
        chosen = components.selected(args.component, authenticated=True)
    except components.UnknownComponent as erreur:
        sys.exit(str(erreur))

    output_path = args.output or Path(f"{args.identifiant}.pdf")
    try:
        written = asyncio.run(build(args.identifiant, output_path, chosen))
    except IdentifiantInvalide as erreur:
        sys.exit(str(erreur))
    except NotFound:
        sys.exit(f"Aucune collectivité connue pour {args.identifiant}.")
    print(written)


def command_fetch(args) -> None:
    try:
        chosen = sources.selected(args.sources)
    except sources.UnknownSource as erreur:
        sys.exit(str(erreur))

    connection = base.connect()
    with httpx.Client(timeout=300, follow_redirects=True) as client:
        for source in chosen:
            if not args.force and not base.is_due(connection, source):
                previous = base.last_fetch(connection, source.name)
                print(f"  {source.name:12} à jour ({previous:%d/%m/%Y})")
                continue
            print(f"  {source.name:12} récupération…", flush=True)
            options = {}
            if args.max_pages and "max_pages" in signature(source.fetch).parameters:
                options["max_pages"] = args.max_pages
            try:
                report = source.fetch(client, connection, **options)
            except Interrupted as interruption:
                print(f"  {source.name:12} {interruption}")
                continue
            base.record_fetch(connection, source.name, report)
            print(f"  {source.name:12} {report}")
    print(base.DB_PATH)


def main(argv=None):
    parser = argparse.ArgumentParser(
        prog="sully",
        description="Fiches de collectivité et données qui les nourrissent.",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    fiche = sub.add_parser("fiche", help="Génère la fiche PDF d'une collectivité.")
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
        "-c",
        "--component",
        help="Composants à afficher, séparés par des virgules (défaut : tous). "
        f"Disponibles : {', '.join(components.COMPONENTS)}",
    )
    fiche.set_defaults(run=command_fiche)

    fetch = sub.add_parser("fetch", help="Récupère les données dont le rythme est dû.")
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
    fetch.add_argument(
        "--max-pages",
        type=int,
        help="Pour les sources paginées : s'arrête après N pages, "
        "et reprend là au prochain appel",
    )
    fetch.set_defaults(run=command_fetch)

    args = parser.parse_args(argv)
    args.run(args)


if __name__ == "__main__":
    main()
