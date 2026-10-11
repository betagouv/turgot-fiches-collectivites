import mimetypes
from contextlib import asynccontextmanager
from dataclasses import asdict

import httpx
from fastapi import FastAPI, HTTPException, Response

from . import components
from .fiche import IdentifiantInvalide, collect, render
from .sources.referentiel import NotFound, Referentiel

mimetypes.add_type("application/geo+json", ".geojson")


@asynccontextmanager
async def lifespan(app: FastAPI):
    async with httpx.AsyncClient(timeout=120) as client:
        app.state.client = client
        app.state.referentiel = Referentiel(client)
        yield


app = FastAPI(title="Sully", lifespan=lifespan)


async def _collect(identifiant: str, requested: str | None):
    try:
        chosen = components.selected(requested)
    except components.UnknownComponent as erreur:
        raise HTTPException(400, str(erreur))
    try:
        return await collect(app.state.client, identifiant, chosen)
    except IdentifiantInvalide as erreur:
        raise HTTPException(400, str(erreur))
    except NotFound:
        raise HTTPException(404, f"Aucune collectivité connue pour {identifiant}.")


async def _result(identifiant: str, name: str):
    _, results = await _collect(identifiant, name)
    if name not in results:
        raise HTTPException(
            404, f"Le composant {name} n'a rien à montrer pour {identifiant}."
        )
    return results[name]


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


@app.get("/components")
async def list_components():
    return [
        {
            "name": component.name,
            "description": component.description,
            "access": component.access,
            "placement": component.placement,
        }
        for component in components.COMPONENTS.values()
    ]


@app.get("/fiches/{identifiant}.pdf")
async def fiche_pdf(identifiant: str, component: str | None = None):
    header, results = await _collect(identifiant, component)
    return Response(
        content=render(header, results),
        media_type="application/pdf",
        headers={"Content-Disposition": f'inline; filename="{identifiant}.pdf"'},
    )


@app.get("/fiches/{identifiant}.json")
async def fiche_json(identifiant: str, component: str | None = None):
    header, results = await _collect(identifiant, component)
    return {**header, "components": {name: r.data for name, r in results.items()}}


@app.get("/fiches/{identifiant}/{name}.json")
async def component_json(identifiant: str, name: str):
    return (await _result(identifiant, name)).data


@app.get("/fiches/{identifiant}/{name}/{filename}")
async def component_file(identifiant: str, name: str, filename: str):
    result = await _result(identifiant, name)
    if filename not in result.files:
        raise HTTPException(404, f"Le composant {name} ne produit pas {filename}.")
    media_type = mimetypes.guess_type(filename)[0] or "application/octet-stream"
    return Response(content=result.files[filename], media_type=media_type)
