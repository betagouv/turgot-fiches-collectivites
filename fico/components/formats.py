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


def long_date(value: date | None) -> Display:
    if value is None:
        return Display(None, "—")
    day = "1er" if value.day == 1 else str(value.day)
    return Display(value.isoformat(), f"{day} {MONTHS[value.month - 1]} {value.year}")
