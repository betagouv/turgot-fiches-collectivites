"""Client for the Référentiel Collectivités API (alpha, no authentication).

https://api.collectivites.beta.gouv.fr/referentiel
"""

from dataclasses import dataclass, field

import httpx

BASE_URL = "https://api.collectivites.beta.gouv.fr/referentiel/v1"

COMMUNE = "commune"
GROUPEMENT = "groupement"


class NotFound(Exception):
    pass


@dataclass
class Competence:
    code: str
    nom: str


@dataclass
class Groupement:
    siren: str
    nom: str
    type: str
    competences: list[Competence] = field(default_factory=list)


@dataclass
class Fiche:
    """Communes and groupements share one shape so the front decodes one type."""

    famille: str
    id: str
    nom: str
    type: str
    siren: str | None = None
    code_insee: str | None = None
    code_epci: str | None = None
    code_departement: str | None = None
    code_region: str | None = None
    population: int | None = None
    codes_postaux: list[str] = field(default_factory=list)
    departements: list[str] = field(default_factory=list)
    regions: list[str] = field(default_factory=list)
    mode_financement: str | None = None
    date_creation: str | None = None
    groupements: list[Groupement] = field(default_factory=list)
    competences: list[Competence] = field(default_factory=list)


def _competences(payload: list[dict] | None) -> list[Competence]:
    return [
        Competence(code=str(c.get("code", "")), nom=c.get("nom", ""))
        for c in payload or []
    ]


def _groupements(payload: list[dict] | None) -> list[Groupement]:
    return [
        Groupement(
            siren=g.get("siren", ""),
            nom=g.get("nom", ""),
            type=g.get("type", ""),
            competences=_competences(g.get("competences")),
        )
        for g in payload or []
    ]


class Referentiel:
    def __init__(self, client: httpx.AsyncClient):
        self.client = client

    async def _get(self, path: str):
        response = await self.client.get(f"{BASE_URL}{path}")
        if response.status_code == 404:
            raise NotFound(path)
        response.raise_for_status()
        return response.json()

    async def commune(self, code_insee: str) -> Fiche:
        payload = await self._get(f"/communes/{code_insee}")
        return Fiche(
            famille=COMMUNE,
            id=payload.get("code", code_insee),
            nom=payload.get("nom", ""),
            type="COM",
            siren=payload.get("siren"),
            code_insee=payload.get("code"),
            code_epci=payload.get("codeEpci"),
            code_departement=payload.get("codeDepartement"),
            code_region=payload.get("codeRegion"),
            population=payload.get("population"),
            codes_postaux=payload.get("codesPostaux") or [],
            groupements=_groupements(payload.get("groupements")),
        )

    async def groupement(self, siren: str) -> Fiche:
        payload = await self._get(f"/groupements/{siren}")
        return Fiche(
            famille=GROUPEMENT,
            id=payload.get("siren", siren),
            nom=payload.get("nom", ""),
            type=payload.get("type", ""),
            siren=payload.get("siren"),
            # Upstream population and nbCommunes are wrong for groupements, so
            # they are dropped rather than displayed.
            departements=payload.get("departements") or [],
            regions=payload.get("regions") or [],
            mode_financement=payload.get("modeFinancement"),
            date_creation=payload.get("dateCreation"),
            competences=_competences(payload.get("competences")),
        )
