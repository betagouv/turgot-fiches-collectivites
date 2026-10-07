from contextlib import asynccontextmanager
from dataclasses import asdict

import httpx
from fastapi import FastAPI, HTTPException, Response

from . import components
from .fiche import IdentifiantInvalide, collect, render
from .sources.referentiel import NotFound, Referentiel


@asynccontextmanager
async def lifespan(app: FastAPI):
    async with httpx.AsyncClient(timeout=120) as client:
        app.state.client = client
        app.state.referentiel = Referentiel(client)
        yield


app = FastAPI(title="Sully", lifespan=lifespan)


@app.get("/api/recherche")
async def recherche(q: str):
    if not q.strip():
        return {"communes": [], "groupements": []}
    found = await app.state.referentiel.search(q)
    return {famille: [asdict(hit) for hit in hits] for famille, hits in found.items()}


@app.get("/api/communes/{code_insee}")
async def commune(code_insee: str):
    try:
        return asdict(await app.state.referentiel.commune(code_insee))
    except NotFound:
        raise HTTPException(404, f"Commune {code_insee} inconnue du référentiel.")


@app.get("/api/groupements/{siren}")
async def groupement(siren: str):
    try:
        return asdict(await app.state.referentiel.groupement(siren))
    except NotFound:
        raise HTTPException(404, f"Groupement {siren} inconnu du référentiel.")


@app.get("/fiches/{identifiant}.pdf")
async def fiche_pdf(identifiant: str, component: str | None = None):
    try:
        chosen = components.selected(component)
    except components.UnknownComponent as erreur:
        raise HTTPException(400, str(erreur))
    try:
        header, results = await collect(app.state.client, identifiant, chosen)
    except IdentifiantInvalide as erreur:
        raise HTTPException(400, str(erreur))
    except NotFound:
        raise HTTPException(404, f"Aucune collectivité connue pour {identifiant}.")
    return Response(
        content=render(header, results),
        media_type="application/pdf",
        headers={"Content-Disposition": f'inline; filename="{identifiant}.pdf"'},
    )
