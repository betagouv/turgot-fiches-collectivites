import argparse
import asyncio
import sys
from pathlib import Path

import httpx

from .blocs import NOMS, BlocInconnu, normalise
from .fiche import collect, render
from .sources.referentiel import NotFound


async def build(siren: str, output_path: Path, blocs) -> Path:
    async with httpx.AsyncClient(timeout=120) as client:
        entete, resultats = await collect(client, siren, blocs)
    output_path.write_bytes(render(entete, resultats))
    return output_path


def main(argv=None):
    parser = argparse.ArgumentParser(
        prog="sully", description="Génère la fiche PDF d'une collectivité, par SIREN."
    )
    parser.add_argument("siren", help="SIREN d'une commune ou d'un groupement")
    parser.add_argument(
        "-o", "--output", type=Path, help="Fichier de sortie (défaut : <siren>.pdf)"
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

    output_path = args.output or Path(f"{args.siren}.pdf")
    try:
        written = asyncio.run(build(args.siren, output_path, blocs))
    except NotFound:
        sys.exit(f"Aucune collectivité connue pour le SIREN {args.siren}.")
    print(written)


if __name__ == "__main__":
    main()
