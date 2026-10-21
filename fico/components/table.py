"""What a component returns: a table. Every cell is a `Display`, so the table
downloads as raw values and reads as labels, whatever its rendering."""

from dataclasses import dataclass

from .formats import Display


@dataclass
class Table:
    """`header` goes above the title, `vide` replaces the body when there is no
    row, `note` follows it. `focus` is the index of the row about the fiche's
    own collectivité, when the rows compare it to others."""

    titre: str
    columns: list[str]
    rows: list[list[Display]]
    header: str = ""
    vide: str = ""
    note: str = ""
    focus: int | None = None
