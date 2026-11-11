import argparse
import sys
from pathlib import Path

import httpx

from . import components, sources
from .errors import FicoError
from .fiche import collect, render
from .sources import database
from .sources.database import connection


def build(identifiant: str, output_path: Path, chosen) -> Path:
    header, lines = collect(identifiant, chosen)
    output_path.write_bytes(render(header, lines))
    return output_path


def command_fiche(args) -> None:
    chosen = components.selected(args.component, components.DEFAULT, authenticated=True)
    output_path = args.output or Path(f"{args.identifiant}.pdf")
    print(build(args.identifiant, output_path, chosen))


def command_fetch(args) -> None:
    chosen = sources.selected(args.sources)
    with (
        connection.connect(),
        httpx.Client(timeout=300, follow_redirects=True) as client,
    ):
        database.migrate()
        for source in chosen:
            if not args.force and not database.is_due(source):
                previous = database.last_fetch(source.name)
                print(f"  {source.name:12} à jour ({previous:%d/%m/%Y})")
                continue
            print(f"  {source.name:12} récupération…", flush=True)
            with database.staged(source):
                report = source.fetch(client)
            database.publish(source)
            database.record_fetch(source.name, report)
            print(f"  {source.name:12} {report}")


def main(argv=None):
    parser = argparse.ArgumentParser(
        prog="fico",
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
        help="Composants à afficher, séparés par des virgules, avec leurs "
        "paramètres entre parenthèses : "
        "identite,financements.historique(since=2020),financements.* "
        f"(défaut : la fiche par défaut). "
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
    fetch.set_defaults(run=command_fetch)

    args = parser.parse_args(argv)
    try:
        args.run(args)
    except FicoError as error:
        sys.exit(str(error))


if __name__ == "__main__":
    main()
