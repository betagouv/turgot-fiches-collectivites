"""The HTML pages: the home page, and the page of a fiche, a shell around one
<fico-fiche> element that loads and lays out the components itself."""

from html import escape
from pathlib import Path
from string import Template

DSFR = "https://cdn.jsdelivr.net/npm/@gouvfr/dsfr@1.14.2/dist/dsfr.min.css"

HOME = Template((Path(__file__).parent / "home.html").read_text(encoding="utf-8"))

PAGE = """<!doctype html>
<html lang="fr" data-fr-scheme="system">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{nom}</title>
  <link rel="stylesheet" href="{dsfr}">
  <link rel="stylesheet" href="/assets/fico.css">
  <script type="module" src="/assets/fiche.js"></script>
</head>
<body>
  <main class="fr-container fr-my-4w">
    <header class="fico-header">
      <h1 class="fr-mb-1w">{nom}</h1>
      <p class="fr-badge fr-badge--info fr-badge--no-icon">{libelle_type}</p>
    </header>
    <fico-fiche src="{src}"></fico-fiche>
    <footer class="fico-muted">{source}</footer>
  </main>
</body>
</html>
"""


def home(components) -> str:
    rows = "".join(
        f"<tr><td><code>{c.name}</code></td><td>{escape(c.description)}</td>"
        f"<td>{c.width}</td></tr>"
        for c in components
    )
    return HOME.substitute(dsfr=DSFR, components=rows)


def page(header: dict, identifiant: str, chosen) -> str:
    names = ",".join(c.name for c in chosen)
    return PAGE.format(
        nom=escape(header["nom"]),
        libelle_type=escape(header["libelle_type"]),
        source=escape(header["source"]),
        dsfr=DSFR,
        src=escape(f"/fiches/{identifiant}.json?component={names}"),
    )
