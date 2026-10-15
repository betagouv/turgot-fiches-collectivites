from contextlib import contextmanager
from pathlib import Path

from fastapi import FastAPI, HTTPException, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import FileResponse, HTMLResponse

from . import components
from .fiche import IdentifiantInvalide, collect, describe, render
from .render import html
from .sources.collectivites import NotFound

ASSETS = Path(components.__file__).parent
SHARED_ASSETS = {"common.js", "component.js", "fiche.js", "fico.css"}


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


def _fiche_arguments(request: Request) -> dict:
    """A whole fiche takes each component's parameters prefixed by its name."""
    query = {k: v for k, v in request.query_params.items() if k != "component"}
    try:
        return components.arguments(query)
    except components.InvalidParameter as erreur:
        raise HTTPException(400, str(erreur))


def _component_arguments(request: Request, name: str) -> dict:
    """A single component takes its parameters unprefixed."""
    component = components.COMPONENTS.get(name)
    if component is None:
        raise HTTPException(400, f"Composant inconnu : {name}.")
    try:
        return {name: component.arguments(request.query_params)}
    except components.InvalidParameter as erreur:
        raise HTTPException(400, str(erreur))


def _collect(identifiant: str, chosen, arguments: dict):
    with _resolving(identifiant):
        return collect(identifiant, chosen, arguments)


def _page(identifiant: str, chosen, arguments: dict) -> HTMLResponse:
    with _resolving(identifiant):
        header = describe(identifiant)
    return HTMLResponse(html.page(header, identifiant, chosen, arguments))


def _result(identifiant: str, name: str, arguments: dict):
    _, results = _collect(identifiant, _chosen(name), arguments)
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
            "parameters": {
                name: kind.__name__ for name, kind in component.parameters.items()
            },
        }
        for component in components.COMPONENTS.values()
    ]


@app.get("/fiches/{identifiant}.pdf")
def fiche_pdf(identifiant: str, request: Request, component: str | None = None):
    chosen, arguments = _chosen(component), _fiche_arguments(request)
    header, results = _collect(identifiant, chosen, arguments)
    return Response(
        content=render(header, results),
        media_type="application/pdf",
        headers={"Content-Disposition": f'inline; filename="{identifiant}.pdf"'},
    )


@app.get("/fiches/{identifiant}.json")
def fiche_json(identifiant: str, request: Request, component: str | None = None):
    chosen, arguments = _chosen(component), _fiche_arguments(request)
    header, results = _collect(identifiant, chosen, arguments)
    lines = components.rows(components.COMPONENTS[name] for name in results)
    return {
        **header,
        "components": {name: r.data for name, r in results.items()},
        "lines": [
            [{"name": c.name, "width": str(c.width)} for c in line] for line in lines
        ],
    }


@app.get("/fiches/{identifiant}/{name}.json")
def component_json(identifiant: str, name: str, request: Request):
    return _result(identifiant, name, _component_arguments(request, name)).data


@app.get("/fiches/{identifiant}.html", response_class=HTMLResponse)
def fiche_html(identifiant: str, request: Request, component: str | None = None):
    return _page(identifiant, _chosen(component), _fiche_arguments(request))


@app.get("/fiches/{identifiant}/{name}.html", response_class=HTMLResponse)
def component_html(identifiant: str, name: str, request: Request):
    arguments = _component_arguments(request, name)
    return _page(identifiant, _chosen(name), arguments)


@app.get("/assets/components/{name}.js")
async def component_script(name: str):
    script = components.template(name, "js")
    if name not in components.modules() or not script.exists():
        raise HTTPException(404, f"Module inconnu : {name}.")
    return FileResponse(script, media_type="text/javascript")


@app.get("/assets/{filename}")
async def shared_asset(filename: str):
    if filename not in SHARED_ASSETS:
        raise HTTPException(404, f"Fichier inconnu : {filename}.")
    return FileResponse(ASSETS / filename)
