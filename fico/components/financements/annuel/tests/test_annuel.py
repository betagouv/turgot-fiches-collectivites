from datetime import UTC, datetime

import pytest

from fico.components.financements import annuel


@pytest.fixture(autouse=True)
def mid_2026(freeze):
    freeze(annuel, datetime(2026, 6, 1, tzinfo=UTC))


def test_last_five_completed_years(client, reference):
    response = client.get("/fiches/35238/financements.annuel.json")

    assert response.status_code == 200
    reference("annuel", response.json())


def test_since(client, reference):
    response = client.get("/fiches/35238/financements.annuel.json?since=2019")

    assert response.status_code == 200
    reference("since", response.json())


def test_no_financement(client, reference):
    response = client.get("/fiches/35001/financements.annuel.json")

    assert response.status_code == 200
    reference("empty", response.json())
