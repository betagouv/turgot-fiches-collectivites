from datetime import UTC, datetime

import pytest

from fico import fiche
from fico.components import financements


@pytest.fixture(autouse=True)
def mid_2026(freeze):
    for module in (fiche, financements):
        freeze(module, datetime(2026, 6, 1, tzinfo=UTC))


def test_default_fiche(client, reference):
    response = client.get("/fiches/35238.json")

    assert response.status_code == 200
    reference("fiche", response.json())
