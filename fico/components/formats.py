"""A value as computed and as displayed, so that every renderer shows the same
label and a third party still gets the raw value."""

from dataclasses import dataclass
from datetime import date

NBSP = " "
NARROW_NBSP = " "
# A symbol takes a narrow no-break space, a unit in words a full one.
SYMBOLS = {"€", "k€", "M€", "%", "km²"}
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


def _suffix(unit: str) -> str:
    if not unit:
        return ""
    space = NARROW_NBSP if unit in SYMBOLS else NBSP
    return f"{space}{unit}"


def number(value: float | None, unit: str = "") -> Display:
    if value is None:
        return Display(None, "—")
    return Display(value, f"{_grouped(value)}{_suffix(unit)}")


def decimal(value: float | None, unit: str = "", digits: int = 1) -> Display:
    if value is None:
        return Display(None, "—")
    return Display(value, f"{value:.{digits}f}".replace(".", ",") + _suffix(unit))


def euros(value: float | None) -> Display:
    return number(value, "€")


def compact_euros(value: float) -> Display:
    if value >= 1_000_000:
        amount = f"{value / 1_000_000:.1f}".rstrip("0").rstrip(".").replace(".", ",")
        return Display(value, f"{amount}{_suffix('M€')}")
    if value >= 1_000:
        return Display(value, f"{_grouped(value / 1_000)}{_suffix('k€')}")
    return Display(value, f"{_grouped(value)}{_suffix('€')}")


def percent(value: float | None) -> Display:
    if value is None:
        return Display(None, "—")
    return Display(value, f"{value * 100:.0f}{_suffix('%')}")


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
