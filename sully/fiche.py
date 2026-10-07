import json
import shutil
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from tempfile import TemporaryDirectory

import httpx
import typst

from . import geo, programmes, subventions
from .referentiel import COMMUNE, Fiche, NotFound, Referentiel

TEMPLATE_PATH = Path(__file__).parent / "templates" / "fiche.typ"
SOURCE = "Sources : API Référentiel Collectivités (alpha) et geo.api.gouv.fr"

PALETTE = ("#ececfe", "#cacafb", "#9a9af8", "#6a6af4", "#000091")
SEUILS_TAUX = (0.15, 0.25, 0.35, 0.50)
COULEUR_FOCUS = "#e1000f"
COULEUR_SANS_DONNEE = "#e5e5e5"
DISPOSITIFS_PRINCIPAUX = ("DETR", "DSIL")

BLOCS = (
    "identite",
    "programmes",
    "carto",
    "chiffres",
    "subventions",
    "competences",
)


class BlocInconnu(Exception):
    pass


def normalise_blocs(demande: str | None) -> tuple[str, ...]:
    if not demande:
        return BLOCS
    choisis = tuple(b.strip() for b in demande.split(",") if b.strip())
    inconnus = [b for b in choisis if b not in BLOCS]
    if inconnus:
        raise BlocInconnu(
            f"Bloc(s) inconnu(s) : {', '.join(inconnus)}. "
            f"Blocs disponibles : {', '.join(BLOCS)}."
        )
    return choisis or BLOCS


@dataclass
class Carte:
    titre: str
    fichier: str
    geojson: dict
    communes: int


@dataclass
class Finances:
    periode: str
    total: float
    cout: float
    taux: float | None
    projets: int
    par_dispositif: list[tuple[str, float]]
    annees: list[int]
    montants: list[float]


@dataclass
class Contexte:
    fiche: Fiche
    surface_km2: float | None = None
    cartes: list[Carte] = field(default_factory=list)
    finances: Finances | None = None
    programmes: list[tuple[str, str]] = field(default_factory=list)
    lignes: list[dict] = field(default_factory=list)
    blocs: tuple[str, ...] = BLOCS


def _teinte(taux: float) -> str:
    for rang, seuil in enumerate(SEUILS_TAUX):
        if taux < seuil:
            return PALETTE[rang]
    return PALETTE[-1]


def _colorise(geojson: dict, code_focus: str, taux: dict[str, float]) -> dict:
    for feature in geojson["features"]:
        proprietes = feature["properties"]
        code = proprietes.get("code")
        connu = taux.get(code)
        focus = code == code_focus
        feature["properties"] = {
            "nom": proprietes.get("nom", ""),
            "couleur": COULEUR_SANS_DONNEE if connu is None else _teinte(connu),
            "contour": COULEUR_FOCUS if focus else "#ffffff",
        }
        feature["_focus"] = focus
    # La bordure de la commune serait recouverte par ses voisines : elle est
    # peinte en dernier.
    geojson["features"].sort(key=lambda f: f.pop("_focus"))
    return geojson


async def resolve(client: httpx.AsyncClient, siren: str) -> Fiche:
    """Find the collectivité behind a SIREN.

    Groupements are addressed by SIREN upstream, communes are not: trying the
    groupement first keeps the index lookup for the communes only.
    """
    referentiel = Referentiel(client)
    try:
        return await referentiel.groupement(siren)
    except NotFound:
        pass
    index = await geo.siren_index(client)
    code_insee = index.get(siren)
    if code_insee is None:
        raise NotFound(siren)
    return await referentiel.commune(code_insee)


def _finances(connection, siren: str) -> Finances | None:
    par_dispositif = [
        (ligne["dispositif"], ligne["montant"] or 0)
        for ligne in subventions.totaux_par_dispositif(connection, siren)
    ]
    if not par_dispositif:
        return None

    cumul = {}
    for ligne in subventions.totaux_par_annee(connection, siren):
        cumul[ligne["annee"]] = cumul.get(ligne["annee"], 0) + (ligne["montant"] or 0)
    annees = sorted(cumul)
    cofinancement = subventions.cofinancement(connection, siren)
    cout = cofinancement["cout"] or 0

    return Finances(
        periode=f"{annees[0]} – {annees[-1]}",
        total=sum(montant for _, montant in par_dispositif),
        cout=cout,
        taux=cofinancement["montant"] / cout if cout else None,
        projets=sum(
            ligne["projets"]
            for ligne in subventions.totaux_par_dispositif(connection, siren)
        ),
        par_dispositif=par_dispositif,
        annees=annees,
        montants=[cumul[annee] for annee in annees],
    )


def _lignes(connection, siren: str) -> list[dict]:
    detail = []
    for ligne in subventions.par_siren(connection, siren):
        cout = ligne["cout_total"]
        montant = ligne["montant_accorde"]
        detail.append(
            {
                "annee": ligne["annee"],
                "dispositif": ligne["dispositif"],
                "libelle": ligne["libelle"] or "—",
                "cout": _euros(cout) if cout else "—",
                "montant": _euros(montant) if montant else "—",
                "taux": f"{montant / cout:.0%}".replace("%", " %")
                if cout and montant
                else "—",
            }
        )
    return detail


async def collect(
    client: httpx.AsyncClient, siren: str, blocs: tuple[str, ...] = BLOCS
) -> Contexte:
    fiche = await resolve(client, siren)
    connection = subventions.connect() if subventions.DB_PATH.exists() else None
    finances = (
        _finances(connection, siren) if connection and "chiffres" in blocs else None
    )
    lignes = _lignes(connection, siren) if connection and "subventions" in blocs else []

    if fiche.famille != COMMUNE:
        return Contexte(fiche=fiche, finances=finances, lignes=lignes, blocs=blocs)

    code_insee = fiche.code_insee
    details = await geo.commune(client, code_insee) if "identite" in blocs else {}

    cartes = []
    if "carto" in blocs:
        cartes.append(
            Carte(
                titre="Département",
                fichier="departement.geojson",
                geojson=await geo.contours_departement(client, fiche.code_departement),
                communes=0,
            )
        )
        if fiche.code_epci:
            cartes.append(
                Carte(
                    titre="Intercommunalité",
                    fichier="intercommunalite.geojson",
                    geojson=await geo.contours_epci(client, fiche.code_epci),
                    communes=0,
                )
            )
    for carte in cartes:
        carte.communes = len(carte.geojson["features"])
        codes = [f["properties"].get("code") for f in carte.geojson["features"]]
        taux = subventions.taux_par_commune(connection, codes) if connection else {}
        _colorise(carte.geojson, code_insee, taux)

    noms = {p.code: p.nom for p in programmes.PROGRAMMES}
    rattachements = (
        [
            (noms.get(ligne["programme"], ligne["programme"]), ligne["depuis"] or "")
            for ligne in subventions.programmes_de(connection, code_insee)
        ]
        if connection and "programmes" in blocs
        else []
    )

    return Contexte(
        fiche=fiche,
        surface_km2=details["surface"] / 100 if details.get("surface") else None,
        cartes=cartes,
        finances=finances,
        programmes=rattachements,
        lignes=lignes,
        blocs=blocs,
    )


def _nombre(valeur) -> str:
    return f"{valeur:,}".replace(",", " ")


def _euros(montant) -> str:
    return f"{_nombre(round(montant))} €"


def _tuiles(finances: Finances) -> list[tuple[str, str, str, str]]:
    montants = dict(finances.par_dispositif)
    principaux = sum(montants.get(d, 0) for d in DISPOSITIFS_PRINCIPAUX)
    fonds_vert = montants.get("FONDS VERT", 0)
    autres = finances.total - principaux - fonds_vert
    taux = f"{finances.taux:.0%}".replace("%", " %") if finances.taux else "—"
    return [
        (
            _euros(finances.total),
            "accordés, tous dispositifs",
            str(finances.projets),
            "projets subventionnés",
        ),
        (
            _euros(montants.get("DETR", 0)),
            "de DETR",
            _euros(montants.get("DSIL", 0)),
            "de DSIL",
        ),
        (_euros(fonds_vert), "de Fonds vert", _euros(autres), "autres dotations"),
        (_euros(finances.cout), "de coût de projet", taux, "de taux de financement"),
    ]


def to_template_data(contexte: Contexte) -> dict:
    fiche = contexte.fiche
    identite = [("SIREN", fiche.siren)]
    if fiche.famille == COMMUNE:
        identite += [("Code INSEE", fiche.code_insee)]
        if fiche.population is not None:
            identite.append(("Population", f"{_nombre(fiche.population)} habitants"))
        if contexte.surface_km2:
            surface = f"{contexte.surface_km2:.1f}".replace(".", ",")
            identite.append(("Superficie", f"{surface} km²"))
            if fiche.population is not None:
                densite = round(fiche.population / contexte.surface_km2)
                identite.append(("Densité", f"{_nombre(densite)} hab./km²"))
        identite += [
            ("Codes postaux", ", ".join(fiche.codes_postaux)),
            ("Département", fiche.code_departement),
            ("Région", fiche.code_region),
        ]
    else:
        identite += [
            ("Type", fiche.type),
            ("Mode de financement", fiche.mode_financement),
            ("Date de création", fiche.date_creation),
            ("Départements", ", ".join(fiche.departements)),
        ]

    finances = contexte.finances
    return {
        "blocs": list(contexte.blocs),
        "nom": fiche.nom,
        "libelle_type": "Commune" if fiche.famille == COMMUNE else fiche.type,
        "identite": [(cle, valeur) for cle, valeur in identite if valeur],
        "programmes": contexte.programmes,
        "cartes": [
            {"titre": c.titre, "fichier": c.fichier, "communes": c.communes}
            for c in contexte.cartes
        ],
        "finances": None
        if finances is None
        else {
            "periode": finances.periode,
            "tuiles": _tuiles(finances),
            "annees": finances.annees,
            "montants": finances.montants,
            "dispositifs": [
                {"nom": nom, "montant": montant}
                for nom, montant in finances.par_dispositif
            ],
        },
        "lignes": contexte.lignes,
        "competences": [{"nom": c.nom} for c in fiche.competences],
        "source": f"{SOURCE} — généré le {datetime.now(UTC):%d/%m/%Y}",
    }


def render(contexte: Contexte) -> bytes:
    """Compile the fiche to PDF.

    Typst reads its data with paths relative to the document, so the payload and
    the maps land in the same temporary directory.
    """
    with TemporaryDirectory() as tmp:
        build_dir = Path(tmp)
        (build_dir / "data.json").write_text(
            json.dumps(to_template_data(contexte), ensure_ascii=False)
        )
        for carte in contexte.cartes:
            (build_dir / carte.fichier).write_text(json.dumps(carte.geojson))
        document = build_dir / "fiche.typ"
        shutil.copy(TEMPLATE_PATH, document)
        return typst.compile(document)
