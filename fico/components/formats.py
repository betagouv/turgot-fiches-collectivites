"""A value as computed and as displayed, so that every renderer shows the same
label and a third party still gets the raw value."""

from dataclasses import dataclass
from datetime import date

NARROW_NBSP = " "
MONTHS = (
    "janvier",
    "février",
    "mars",
    "avril",
    "mai",
    "juin",
    "juillet",
    "août",
    "septembre",
    "octobre",
    "novembre",
    "décembre",
)


@dataclass
class Display:
    value: float | int | str | None
    label: str


def _grouped(value: float) -> str:
    return f"{round(value):,}".replace(",", NARROW_NBSP)


def number(value: float | None, unit: str = "") -> Display:
    if value is None:
        return Display(None, "—")
    suffix = f" {unit}" if unit else ""
    return Display(value, f"{_grouped(value)}{suffix}")


def decimal(value: float | None, unit: str = "", digits: int = 1) -> Display:
    if value is None:
        return Display(None, "—")
    suffix = f" {unit}" if unit else ""
    return Display(value, f"{value:.{digits}f}".replace(".", ",") + suffix)


def euros(value: float | None) -> Display:
    return number(value, "€")


def compact_euros(value: float) -> Display:
    if value >= 1_000_000:
        amount = f"{value / 1_000_000:.1f}".rstrip("0").rstrip(".").replace(".", ",")
        return Display(value, f"{amount} M€")
    if value >= 1_000:
        return Display(value, f"{_grouped(value / 1_000)} k€")
    return Display(value, f"{_grouped(value)} €")


def percent(value: float | None) -> Display:
    if value is None:
        return Display(None, "—")
    return Display(value, f"{value:.0%}".replace("%", f"{NARROW_NBSP}%"))


def text(value: str | None) -> Display:
    return Display(value, value or "—")


def plain(value: float | None) -> Display:
    """Shown as is, without grouping: years, codes."""
    if value is None:
        return Display(None, "—")
    return Display(value, str(value))


def _parse_date(value: str) -> date | None:
    try:
        return date.fromisoformat(value[:10])
    except ValueError:
        pass
    parts = value.split("/")
    if len(parts) != 3 or not all(part.isdigit() for part in parts):
        return None
    day, month, year = (int(part) for part in parts)
    try:
        return date(year, month, day)
    except ValueError:
        return None


def long_date(value: str | None) -> Display:
    """Accepts ISO (`2024-09-01`) and French (`01/09/2024`) dates; the value is
    normalised to ISO, anything unparsable is shown as is."""
    if not value:
        return Display(None, "—")
    parsed = _parse_date(value.strip())
    if parsed is None:
        return Display(value, value)
    day = "1er" if parsed.day == 1 else str(parsed.day)
    return Display(
        parsed.isoformat(), f"{day} {MONTHS[parsed.month - 1]} {parsed.year}"
    )
