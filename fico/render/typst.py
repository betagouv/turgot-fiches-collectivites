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

from ..components import registry as components

EXTENSION = "typ"
COMMON = Path(components.__file__).parent / "common.typ"
ROOT = "fiche.typ"
FONTS = Path(__file__).parent.parent.parent / "fonts"

TEMPLATE = """#import "common.typ": header, row, theme
{imports}

#let data = json("data.json")

#show: theme.with(source: data.source)

#header(data.nom, data.libelle_type)

{body}
"""


def _alias(name: str) -> str:
    # A Typst identifier takes hyphens, not dots.
    return name.replace(".", "-")


def _call(name: str) -> str:
    return f'{_alias(name)}.render(data.components.at("{name}"))'


def _line(line: tuple[components.Component, ...]) -> str:
    # A component alone stays outside any grid: grid cells never break across
    # pages, and a long table must.
    if len(line) == 1:
        return f"#{_call(line[0].name)}"
    widths = ", ".join(str(float(c.width)) for c in line)
    calls = ", ".join(_call(c.name) for c in line)
    return f"#row(({widths},), ({calls},))"


def _document(names: list[str]) -> str:
    imports = "\n".join(
        f'#import "{name}.{EXTENSION}" as {_alias(name)}' for name in names
    )
    lines = components.rows(components.COMPONENTS[name] for name in names)
    body = "\n".join(_line(line) for line in lines)
    return TEMPLATE.format(imports=imports, body=body)


def compile_fiche(header: dict, results: dict) -> bytes:
    """`results` associe un nom de composant à son `Result`, dans l'ordre voulu."""
    with TemporaryDirectory() as tmp:
        build = Path(tmp)
        shutil.copy(COMMON, build / "common.typ")
        for name in results:
            target = build / f"{name}.{EXTENSION}"
            shutil.copy(components.template(name, EXTENSION), target)
            for module in components.ancestors(name):
                shared = components.template(module, EXTENSION)
                if shared.exists():
                    shutil.copy(shared, build / f"{module}.{EXTENSION}")

        data = {name: result.data for name, result in results.items()}
        (build / "data.json").write_text(
            json.dumps(
                {**header, "components": data}, default=asdict, ensure_ascii=False
            )
        )
        (build / ROOT).write_text(_document(list(results)))
        return typst.compile(build / ROOT, font_paths=[FONTS])
