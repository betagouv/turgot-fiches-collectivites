from datetime import UTC, datetime

import pytest

from fico.components import financements


@pytest.fixture(autouse=True)
def mid_2026(freeze):
    freeze(financements, datetime(2026, 6, 1, tzinfo=UTC))
