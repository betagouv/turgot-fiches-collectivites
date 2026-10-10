"""Assemble les composants demandés en un document Typst, puis le compile.

Les imports Typst sont statiques : le gabarit racine est donc écrit à la
compilation, avec les seuls composants retenus.
"""

import json
import shutil
from dataclasses import asdict
from pathlib import Path
from tempfile import TemporaryDirectory

import typst

from ..components import Placement
from ..components import registry as components

EXTENSION = "typ"
COMMON = Path(components.__file__).parent / "common.typ"
ROOT = "fiche.typ"

TEMPLATE = """#import "common.typ": cards, header, theme
{imports}

#let data = json("data.json")

#show: theme.with(source: data.source)

#header(data.nom, data.libelle_type)

#cards(({cards}))
{sections}
"""


def _document(cards: list[str], sections: list[str]) -> str:
    imports = "\n".join(
        f'#import "{name}.{EXTENSION}" as {name}' for name in cards + sections
    )
    calls = "".join(f"{name}.render(data.components.{name}), " for name in cards)
    body = "\n".join(f"#{name}.render(data.components.{name})" for name in sections)
    return TEMPLATE.format(imports=imports, cards=calls, sections=body)


def compile_fiche(header: dict, results: dict) -> bytes:
    """`results` associe un nom de composant à son `Result`, dans l'ordre voulu."""
    cards, sections = [], []
    for name in results:
        placement = components.COMPONENTS[name].placement
        (cards if placement is Placement.CARD else sections).append(name)

    with TemporaryDirectory() as tmp:
        build = Path(tmp)
        shutil.copy(COMMON, build / "common.typ")
        for name, result in results.items():
            component = components.COMPONENTS[name]
            shutil.copy(component.template(EXTENSION), build / f"{name}.{EXTENSION}")
            for filename, content in result.files.items():
                (build / filename).write_text(content)

        data = {name: result.data for name, result in results.items()}
        (build / "data.json").write_text(
            json.dumps(
                {**header, "components": data}, default=asdict, ensure_ascii=False
            )
        )
        (build / ROOT).write_text(_document(cards, sections))
        return typst.compile(build / ROOT)
