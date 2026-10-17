from collections.abc import Callable
from dataclasses import dataclass
from datetime import timedelta
from enum import StrEnum


class Schedule(StrEnum):
    ONESHOT = "oneshot"
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"


INTERVALS = {
    Schedule.DAILY: timedelta(days=1),
    Schedule.WEEKLY: timedelta(weeks=1),
    Schedule.MONTHLY: timedelta(days=30),
}


@dataclass(frozen=True)
class Source:
    name: str
    label: str
    schedule: Schedule
    schema: str
    fetch: Callable
    paginated: bool

    @property
    def interval(self) -> timedelta | None:
        return INTERVALS.get(self.schedule)


SOURCES: dict[str, Source] = {}


class UnknownSource(Exception):
    pass


class Interrupted(Exception):
    """Raised by a fetch stopped before its end: it does not count as a fetch,
    so the source stays due."""


def source(
    name: str,
    label: str,
    schedule: Schedule,
    schema: str = "",
    paginated: bool = False,
):
    """A `paginated` source's fetch takes `max_pages`, and resumes where the
    previous call stopped."""

    def decorate(fetch: Callable) -> Callable:
        SOURCES[name] = Source(
            name=name,
            label=label,
            schedule=schedule,
            schema=schema,
            fetch=fetch,
            paginated=paginated,
        )
        return fetch

    return decorate


VIEWS: list[str] = []


def view(definition: str) -> None:
    """A view over several sources' tables, created once they all exist."""
    VIEWS.append(definition)


def schemas() -> list[str]:
    return [source.schema for source in SOURCES.values() if source.schema]


def selected(requested: str | None) -> tuple[Source, ...]:
    if not requested:
        return tuple(SOURCES.values())
    names = tuple(name.strip() for name in requested.split(",") if name.strip())
    unknown = [name for name in names if name not in SOURCES]
    if unknown:
        raise UnknownSource(
            f"Source(s) inconnue(s) : {', '.join(unknown)}. "
            f"Sources disponibles : {', '.join(SOURCES)}."
        )
    return tuple(SOURCES[name] for name in names)
