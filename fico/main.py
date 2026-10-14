from contextlib import contextmanager
from pathlib import Path

from fastapi import FastAPI, HTTPException, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import FileResponse, HTMLResponse

from . import components
from .fiche import IdentifiantInvalide, collect, describe, render
from .render import html
from .sources.collectivites import NotFound

ASSETS = Path(components.__file__).parent
SHARED_ASSETS = {"common.js", "fiche.js", "fico.css"}


app = FastAPI(title="Fico")
# Consumers embed the components from their own origin: module scripts and the
# JSON they fetch are cross-origin requests. Every response is a public,
# cookie-free read, so any origin may make them.
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["GET"])
app.add_middleware(GZipMiddleware)


def _chosen(requested: str | None):
    try:
        return components.selected(requested)
    except components.UnknownComponent as erreur:
        raise HTTPException(400, str(erreur))


@contextmanager
def _resolving(identifiant: str):
    try:
        yield
    except IdentifiantInvalide as erreur:
        raise HTTPException(400, str(erreur))
    except NotFound:
        raise HTTPException(404, f"Aucune collectivité connue pour {identifiant}.")


def _collect(identifiant: str, requested: str | None):
    chosen = _chosen(requested)
    with _resolving(identifiant):
        return collect(identifiant, chosen)


def _page(identifiant: str, requested: str | None) -> HTMLResponse:
    chosen = _chosen(requested)
    with _resolving(identifiant):
        header = describe(identifiant)
    return HTMLResponse(html.page(header, identifiant, chosen))


def _result(identifiant: str, name: str):
    _, results = _collect(identifiant, name)
    if name not in results:
        raise HTTPException(
            404, f"Le composant {name} n'a rien à montrer pour {identifiant}."
        )
    return results[name]


@app.get("/", response_class=HTMLResponse, include_in_schema=False)
async def home():
    return html.home(components.COMPONENTS.values())


@app.get("/components")
async def list_components():
    return [
        {
            "name": component.name,
            "description": component.description,
            "access": component.access,
            "width": str(component.width),
        }
        for component in components.COMPONENTS.values()
    ]


@app.get("/fiches/{identifiant}.pdf")
def fiche_pdf(identifiant: str, component: str | None = None):
    header, results = _collect(identifiant, component)
    return Response(
        content=render(header, results),
        media_type="application/pdf",
        headers={"Content-Disposition": f'inline; filename="{identifiant}.pdf"'},
    )


@app.get("/fiches/{identifiant}.json")
def fiche_json(identifiant: str, component: str | None = None):
    header, results = _collect(identifiant, component)
    lines = components.rows(components.COMPONENTS[name] for name in results)
    return {
        **header,
        "components": {name: r.data for name, r in results.items()},
        "lines": [
            [{"name": c.name, "width": str(c.width)} for c in line] for line in lines
        ],
    }


@app.get("/fiches/{identifiant}/{name}.json")
def component_json(identifiant: str, name: str):
    return _result(identifiant, name).data


@app.get("/fiches/{identifiant}.html", response_class=HTMLResponse)
def fiche_html(identifiant: str, component: str | None = None):
    return _page(identifiant, component)


@app.get("/fiches/{identifiant}/{name}.html", response_class=HTMLResponse)
def component_html(identifiant: str, name: str):
    return _page(identifiant, name)


@app.get("/assets/components/{name}.js")
async def component_script(name: str):
    if name not in components.COMPONENTS:
        raise HTTPException(404, f"Composant inconnu : {name}.")
    return FileResponse(
        components.COMPONENTS[name].template("js"), media_type="text/javascript"
    )


@app.get("/assets/{filename}")
async def shared_asset(filename: str):
    if filename not in SHARED_ASSETS:
        raise HTTPException(404, f"Fichier inconnu : {filename}.")
    return FileResponse(ASSETS / filename)
