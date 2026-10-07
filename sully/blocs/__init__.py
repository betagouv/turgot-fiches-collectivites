"""Les blocs d'une fiche.

Chaque bloc est un paquet qui porte sa collecte (`collecte`), sa place dans la
page (`PLACEMENT`) et un gabarit par cible de rendu, nommé d'après lui :
`identite.typ` aujourd'hui, `identite.html` le jour venu.
"""

from . import carto, chiffres, competences, identite, programmes, subventions

ORDRE = (identite, programmes, carto, chiffres, subventions, competences)
PAR_NOM = {bloc.NOM: bloc for bloc in ORDRE}
NOMS = tuple(bloc.NOM for bloc in ORDRE)


class BlocInconnu(Exception):
    pass


def normalise(demande: str | None) -> tuple[str, ...]:
    if not demande:
        return NOMS
    choisis = tuple(nom.strip() for nom in demande.split(",") if nom.strip())
    inconnus = [nom for nom in choisis if nom not in PAR_NOM]
    if inconnus:
        raise BlocInconnu(
            f"Bloc(s) inconnu(s) : {', '.join(inconnus)}. "
            f"Blocs disponibles : {', '.join(NOMS)}."
        )
    return choisis or NOMS
