import argparse
import asyncio
import sys
from pathlib import Path

import httpx

from .blocs import NOMS, BlocInconnu, normalise
from .fiche import IdentifiantInvalide, collect, render
from .sources.referentiel import NotFound


async def build(identifiant: str, output_path: Path, blocs) -> Path:
    async with httpx.AsyncClient(timeout=120) as client:
        entete, resultats = await collect(client, identifiant, blocs)
    output_path.write_bytes(render(entete, resultats))
    return output_path


def main(argv=None):
    parser = argparse.ArgumentParser(
        prog="sully",
        description="Génère la fiche PDF d'une collectivité, "
        "par code INSEE de commune ou par SIREN.",
    )
    parser.add_argument(
        "identifiant",
        help="Code INSEE d'une commune (5 caractères) "
        "ou SIREN d'une commune ou d'un groupement (9 chiffres)",
    )
    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        help="Fichier de sortie (défaut : <identifiant>.pdf)",
    )
    parser.add_argument(
        "-b",
        "--blocs",
        help="Blocs à afficher, séparés par des virgules (défaut : tous). "
        f"Disponibles : {', '.join(NOMS)}",
    )
    args = parser.parse_args(argv)

    try:
        blocs = normalise(args.blocs)
    except BlocInconnu as erreur:
        sys.exit(str(erreur))

    output_path = args.output or Path(f"{args.identifiant}.pdf")
    try:
        written = asyncio.run(build(args.identifiant, output_path, blocs))
    except IdentifiantInvalide as erreur:
        sys.exit(str(erreur))
    except NotFound:
        sys.exit(f"Aucune collectivité connue pour {args.identifiant}.")
    print(written)


if __name__ == "__main__":
    main()
