"""The HTML pages: the home page, and the page of a fiche, a shell around one
<fico-fiche> element that loads and lays out the components itself."""

from html import escape
from pathlib import Path
from string import Template

from ..sources.registry import Schedule

DSFR = "https://cdn.jsdelivr.net/npm/@gouvfr/dsfr@1.15.3/dist/dsfr.min.css"

HOME = Template((Path(__file__).parent / "home.html").read_text(encoding="utf-8"))
LOGO = (Path(__file__).parent / "logo.svg").read_text(encoding="utf-8")

SCHEDULE_LABELS = {
    Schedule.ONESHOT: "ponctuelle",
    Schedule.DAILY: "quotidienne",
    Schedule.WEEKLY: "hebdomadaire",
    Schedule.MONTHLY: "mensuelle",
}

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
    <fico-fiche collectivite="{collectivite}" components="{components}"></fico-fiche>
  </main>
</body>
</html>
"""


def home(base: str, components, sources) -> str:
    """`base` is this server's address, so the integration examples work as is."""
    rows = "".join(
        f"<tr><td><code>{c.name}</code></td><td>{escape(c.description)}</td>"
        f"<td>{c.width}</td></tr>"
        for c in components
    )
    source_rows = "".join(
        f"<tr><td>{escape(source.label)}</td>"
        f"<td>{SCHEDULE_LABELS[source.schedule]}</td></tr>"
        for source in sources
    )
    return HOME.substitute(
        base=base, dsfr=DSFR, components=rows, sources=source_rows, logo=LOGO
    )


def page(header: dict, identifiant: str, chosen) -> str:
    return PAGE.format(
        nom=escape(header["nom"]),
        dsfr=DSFR,
        collectivite=escape(identifiant),
        components=escape(",".join(instance.spec for instance in chosen)),
    )
