import json
from contextlib import contextmanager
from pathlib import Path

from fastapi import FastAPI, HTTPException, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import FileResponse, HTMLResponse

from . import components, sources
from .fiche import IdentifiantInvalide, collect, collect_one, describe, render
from .render import html, table
from .sources.collectivites import NotFound

ASSETS = Path(components.__file__).parent
SHARED_ASSETS = {"common.js", "component.js", "fiche.js", "fico.css"}
# Embedding pages reference unversioned URLs: a short lifetime bounds how long
# they run the previous code after a deployment.
ASSET_CACHE = {"Cache-Control": "public, max-age=300"}
MEDIA_TYPES = {
    components.Download.CSV: "text/csv; charset=utf-8",
    components.Download.XLSX: (
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    ),
    components.Download.GEOJSON: "application/geo+json",
}


app = FastAPI(title="Fico")
# Consumers embed the components from their own origin: module scripts and the
# JSON they fetch are cross-origin requests. Every response is a public,
# cookie-free read, so any origin may make them.
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["GET"])
app.add_middleware(GZipMiddleware)


def _chosen(requested: str | None):
    try:
        return components.selected(requested)
    except (components.UnknownComponent, components.InvalidParameter) as erreur:
        raise HTTPException(400, str(erreur))


def _instance(name: str, request: Request) -> components.Instance:
    """A single component takes its parameters from the query string."""
    component = components.COMPONENTS.get(name)
    if component is None or component.access is not components.Access.PUBLIC:
        raise HTTPException(404, f"Composant inconnu : {name}.")
    try:
        return component.instance(request.query_params)
    except components.InvalidParameter as erreur:
        raise HTTPException(400, str(erreur))


@contextmanager
def _resolving(identifiant: str):
    try:
        yield
    except IdentifiantInvalide as erreur:
        raise HTTPException(400, str(erreur))
    except NotFound:
        raise HTTPException(404, f"Aucune collectivité connue pour {identifiant}.")


def _collect(identifiant: str, chosen):
    with _resolving(identifiant):
        return collect(identifiant, chosen)


def _page(identifiant: str, chosen) -> HTMLResponse:
    with _resolving(identifiant):
        header = describe(identifiant)
    return HTMLResponse(html.page(header, identifiant, chosen))


@app.get("/", response_class=HTMLResponse, include_in_schema=False)
async def home(request: Request):
    base = str(request.base_url).rstrip("/")
    return html.home(base, components.COMPONENTS.values(), sources.SOURCES.values())


@app.get("/components")
async def list_components():
    return [
        {
            "name": component.name,
            "description": component.description,
            "access": component.access,
            "width": str(component.width),
            "parameters": {
                name: parameter.describe()
                for name, parameter in component.parameters.items()
            },
            "downloads": component.downloads,
        }
        for component in components.COMPONENTS.values()
    ]


@app.get("/fiches/{identifiant}.pdf")
def fiche_pdf(identifiant: str, component: str | None = None):
    header, lines = _collect(identifiant, _chosen(component))
    return Response(
        content=render(header, lines),
        media_type="application/pdf",
        headers={"Content-Disposition": f'inline; filename="{identifiant}.pdf"'},
    )


@app.get("/fiches/{identifiant}.json")
def fiche_json(identifiant: str, component: str | None = None):
    header, lines = _collect(identifiant, _chosen(component))
    return {**header, "lines": lines}


def _data(identifiant: str, instance: components.Instance):
    with _resolving(identifiant):
        result = collect_one(identifiant, instance)
    if result is None:
        raise HTTPException(
            404, f"Le composant {instance.name} n'a rien à montrer pour {identifiant}."
        )
    return result.data


@app.get("/fiches/{identifiant}/{name}.json")
def component_json(identifiant: str, name: str, request: Request):
    return _data(identifiant, _instance(name, request))


@app.get("/fiches/{identifiant}.html", response_class=HTMLResponse)
def fiche_html(identifiant: str, component: str | None = None):
    return _page(identifiant, _chosen(component))


@app.get("/fiches/{identifiant}/{name}.html", response_class=HTMLResponse)
def component_html(identifiant: str, name: str, request: Request):
    return _page(identifiant, (_instance(name, request),))


# Declared after `.json` and `.html`, which this route would capture otherwise.
@app.get("/fiches/{identifiant}/{name}.{extension}")
def component_download(
    identifiant: str, name: str, extension: components.Download, request: Request
):
    instance = _instance(name, request)
    component = instance.component
    if extension not in component.downloads:
        raise HTTPException(404, f"{name} ne se télécharge pas en {extension}.")
    data = _data(identifiant, instance)
    match extension:
        case components.Download.CSV:
            content = table.to_csv(component.table(data))
        case components.Download.XLSX:
            content = table.to_xlsx(component.table(data))
        case components.Download.GEOJSON:
            content = json.dumps(component.geojson(data)).encode()
    filename = f"{identifiant}-{name}.{extension}"
    return Response(
        content=content,
        media_type=MEDIA_TYPES[extension],
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@app.get("/assets/components/{name}.js")
async def component_script(name: str):
    script = components.template(name, "js")
    if name not in components.modules() or not script.exists():
        raise HTTPException(404, f"Module inconnu : {name}.")
    return FileResponse(script, media_type="text/javascript", headers=ASSET_CACHE)


@app.get("/assets/{filename}")
async def shared_asset(filename: str):
    if filename not in SHARED_ASSETS:
        raise HTTPException(404, f"Fichier inconnu : {filename}.")
    return FileResponse(ASSETS / filename, headers=ASSET_CACHE)
