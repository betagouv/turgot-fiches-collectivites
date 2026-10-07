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

    @property
    def interval(self) -> timedelta | None:
        return INTERVALS.get(self.schedule)


SOURCES: dict[str, Source] = {}


class UnknownSource(Exception):
    pass


def source(name: str, label: str, schedule: Schedule, schema: str = ""):
    def decorate(fetch: Callable) -> Callable:
        SOURCES[name] = Source(
            name=name, label=label, schedule=schedule, schema=schema, fetch=fetch
        )
        return fetch

    return decorate


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
