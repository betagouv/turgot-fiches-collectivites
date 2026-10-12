"""The HTML pages: the home page, and the page of a fiche, a shell placing one
<sully-*> element per component.

Each element fetches its component's JSON itself; this module only lays out
the page.
"""

from html import escape
from pathlib import Path
from string import Template

from ..components import rows

DSFR = "https://cdn.jsdelivr.net/npm/@gouvfr/dsfr@1.14.2/dist/dsfr.min.css"

HOME = Template((Path(__file__).parent / "home.html").read_text(encoding="utf-8"))

PAGE = """<!doctype html>
<html lang="fr" data-fr-scheme="system">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{nom}</title>
  <link rel="stylesheet" href="{dsfr}">
  <link rel="stylesheet" href="/assets/sully.css">
{scripts}
</head>
<body>
  <main class="fr-container fr-my-4w">
    <header class="sully-header">
      <h1 class="fr-mb-1w">{nom}</h1>
      <p class="fr-badge fr-badge--info fr-badge--no-icon">{libelle_type}</p>
    </header>
    <div class="sully-lines">{lines}</div>
    <footer class="sully-muted">{source}</footer>
  </main>
</body>
</html>
"""


def home(components) -> str:
    rows = "".join(
        f"<tr><td><code>{c.name}</code></td><td>{escape(c.description)}</td>"
        f"<td>{escape(c.width)}</td></tr>"
        for c in components
    )
    return HOME.substitute(dsfr=DSFR, components=rows)


def _element(identifiant: str, name: str) -> str:
    src = f"/fiches/{escape(identifiant)}/{name}.json"
    return f'<sully-{name} src="{src}"></sully-{name}>'


def _line(identifiant: str, line) -> str:
    elements = "".join(_element(identifiant, c.name) for c in line)
    if len(line) == 1:
        return elements
    return f'<div class="sully-pair">{elements}</div>'


def page(header: dict, identifiant: str, chosen) -> str:
    scripts = "\n".join(
        f'  <script type="module" src="/assets/components/{c.name}.js"></script>'
        for c in chosen
    )
    lines = "".join(_line(identifiant, line) for line in rows(chosen))
    return PAGE.format(
        nom=escape(header["nom"]),
        libelle_type=escape(header["libelle_type"]),
        source=escape(header["source"]),
        dsfr=DSFR,
        scripts=scripts,
        lines=lines,
    )
