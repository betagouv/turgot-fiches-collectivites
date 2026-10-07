import argparse
import asyncio
import sys
from pathlib import Path

import httpx

from .fiche import BLOCS, BlocInconnu, collect, normalise_blocs, render
from .referentiel import NotFound


async def build(siren: str, output_path: Path, blocs) -> Path:
    async with httpx.AsyncClient(timeout=120) as client:
        contexte = await collect(client, siren, blocs)
    output_path.write_bytes(render(contexte))
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
        help=f"Blocs à afficher, séparés par des virgules (défaut : tous). "
        f"Disponibles : {', '.join(BLOCS)}",
    )
    args = parser.parse_args(argv)

    try:
        blocs = normalise_blocs(args.blocs)
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
