"""The HTML page of a fiche: a shell placing one <sully-*> element per component.

Each element fetches its component's JSON itself; this module only lays out
the page.
"""

from html import escape

from ..components import Placement

DSFR = "https://cdn.jsdelivr.net/npm/@gouvfr/dsfr@1.14.2/dist/dsfr.min.css"

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
    <div class="sully-cards">{cards}</div>
    <div class="sully-sections">{sections}</div>
    <footer class="sully-muted">{source}</footer>
  </main>
</body>
</html>
"""


def _element(identifiant: str, name: str) -> str:
    src = f"/fiches/{escape(identifiant)}/{name}.json"
    return f'<sully-{name} src="{src}"></sully-{name}>'


def page(header: dict, identifiant: str, chosen) -> str:
    scripts = "\n".join(
        f'  <script type="module" src="/assets/components/{c.name}.js"></script>'
        for c in chosen
    )
    cards = "".join(
        _element(identifiant, c.name) for c in chosen if c.placement is Placement.CARD
    )
    sections = "".join(
        _element(identifiant, c.name)
        for c in chosen
        if c.placement is not Placement.CARD
    )
    return PAGE.format(
        nom=escape(header["nom"]),
        libelle_type=escape(header["libelle_type"]),
        source=escape(header["source"]),
        dsfr=DSFR,
        scripts=scripts,
        cards=cards,
        sections=sections,
    )
