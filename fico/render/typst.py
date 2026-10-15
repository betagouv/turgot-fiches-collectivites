"""Assemble les composants demandés en un document Typst, puis le compile.

Les imports Typst sont statiques : le gabarit racine est donc écrit à la
compilation, avec les seuls composants retenus.
"""

import json
import shutil
from dataclasses import asdict
from fractions import Fraction
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


def _call(entry: dict, row: int, column: int) -> str:
    return f"{_alias(entry['name'])}.render(data.lines.at({row}).at({column}).data)"


def _line(row: int, line: list[dict]) -> str:
    # A component alone stays outside any grid: grid cells never break across
    # pages, and a long table must.
    if len(line) == 1:
        return f"#{_call(line[0], row, 0)}"
    widths = ", ".join(str(float(Fraction(entry["width"]))) for entry in line)
    calls = ", ".join(_call(entry, row, column) for column, entry in enumerate(line))
    return f"#row(({widths},), ({calls},))"


def _document(names: list[str], lines: list[list[dict]]) -> str:
    imports = "\n".join(
        f'#import "{name}.{EXTENSION}" as {_alias(name)}' for name in names
    )
    body = "\n".join(_line(row, line) for row, line in enumerate(lines))
    return TEMPLATE.format(imports=imports, body=body)


def compile_fiche(header: dict, lines: list[list[dict]]) -> bytes:
    names = list(dict.fromkeys(entry["name"] for line in lines for entry in line))
    with TemporaryDirectory() as tmp:
        build = Path(tmp)
        shutil.copy(COMMON, build / "common.typ")
        for name in names:
            for module in (*components.ancestors(name), name):
                source = components.template(module, EXTENSION)
                if source.exists():
                    shutil.copy(source, build / f"{module}.{EXTENSION}")

        (build / "data.json").write_text(
            json.dumps({**header, "lines": lines}, default=asdict, ensure_ascii=False)
        )
        (build / ROOT).write_text(_document(names, lines))
        return typst.compile(build / ROOT, font_paths=[FONTS])
