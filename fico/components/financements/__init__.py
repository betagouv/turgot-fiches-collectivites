"""Les financements reçus par la collectivité, d'après API Collectivités."""

from datetime import UTC, datetime

from ..registry import InvalidParameter

YEARS = 6


def years(since: int | None = None) -> range:
    current_year = datetime.now(UTC).year
    if since is not None and since >= current_year:
        raise InvalidParameter(
            f"since={since} invalide, attendu : une année révolue, "
            f"au plus {current_year - 1}."
        )
    # The current year is still running: it would look like a drop.
    return range(since or current_year - YEARS, current_year)
