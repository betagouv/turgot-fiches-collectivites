import argparse
from collections import Counter

import httpx

from . import opendata, programmes, subventions


def importe_programmes(client, connection) -> int:
    print(f"Programmes : {len(programmes.PROGRAMMES)} liste(s)")
    total = 0
    for programme in programmes.PROGRAMMES:
        ecrites = subventions.upsert_programmes(
            connection, programmes.lignes(client, programme)
        )
        print(f"  {programme.nom} : {ecrites} commune(s)")
        total += ecrites
    return total


def importe_dgcl(client, connection) -> int:
    ressources = opendata.resources(client, opendata.DGCL_DATASET)
    print(f"DGCL : {len(ressources)} fichier(s)")
    total = 0
    rejets = Counter()
    for ressource in ressources:
        texte = opendata.download(client, ressource["url"])
        ecrites = subventions.upsert(connection, opendata.lignes_dgcl(texte, rejets))
        print(f"  {ressource['title']} : {ecrites} ligne(s)")
        total += ecrites
    if rejets:
        detail = ", ".join(
            f"{motif} {nombre}" for motif, nombre in rejets.most_common()
        )
        print(f"  écartées faute de SIREN : {sum(rejets.values())} ({detail})")
    return total


def importe_fonds_vert(client, connection) -> int:
    ressources = opendata.resources(client, opendata.FONDS_VERT_DATASET)
    print(f"Fonds vert : {len(ressources)} fichier(s)")
    total = 0
    rejets = Counter()
    for ressource in ressources:
        titre = ressource["title"]
        annee = opendata.annee_de(titre)
        if annee is None:
            print(f"  {titre} : ignoré, millésime introuvable dans le titre")
            continue
        texte = opendata.download(client, ressource["url"])
        if not opendata.porte_un_siren(texte):
            print(f"  {titre} : ignoré, ni SIREN ni SIRET de bénéficiaire")
            continue
        ecrites = subventions.upsert(
            connection, opendata.lignes_fonds_vert(texte, annee, rejets)
        )
        print(f"  {titre} : {ecrites} ligne(s)")
        total += ecrites
    if rejets:
        print(f"  écartées faute de SIREN : {sum(rejets.values())}")
    return total


def main(argv=None):
    parser = argparse.ArgumentParser(
        prog="sully-import",
        description="Importe les subventions DGCL et Fonds vert dans SQLite.",
    )
    parser.add_argument(
        "--source",
        choices=("dgcl", "fonds-vert", "programmes", "tout"),
        default="tout",
    )
    args = parser.parse_args(argv)

    connection = subventions.connect()
    with httpx.Client(timeout=300, follow_redirects=True) as client:
        if args.source in ("dgcl", "tout"):
            importe_dgcl(client, connection)
        if args.source in ("fonds-vert", "tout"):
            importe_fonds_vert(client, connection)
        if args.source in ("programmes", "tout"):
            importe_programmes(client, connection)

    print(
        f"\nEn base : {subventions.compte(connection)} subvention(s), "
        f"{subventions.compte_programmes(connection)} rattachement(s) à un programme"
    )
    print(subventions.DB_PATH)


if __name__ == "__main__":
    main()
