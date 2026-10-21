from datetime import UTC, datetime

import pytest

from fico.components.financements import par_habitant


@pytest.fixture(autouse=True)
def mid_2026(freeze):
    freeze(par_habitant, datetime(2026, 6, 1, tzinfo=UTC))


def test_commune_among_its_interco(client, reference):
    response = client.get("/fiches/35238/financements.par_habitant.json")

    assert response.status_code == 200
    reference("commune", response.json())


def test_one_financeur(client, reference):
    response = client.get(
        "/fiches/35238/financements.par_habitant.json?financeur=Fonds Vert"
    )

    assert response.status_code == 200
    reference("fonds_vert", response.json())


def test_since(client, reference):
    response = client.get("/fiches/35238/financements.par_habitant.json?since=2019")

    assert response.status_code == 200
    reference("since", response.json())


def test_epci_among_its_departement(client, reference):
    response = client.get("/fiches/243500139/financements.par_habitant.json")

    assert response.status_code == 200
    reference("epci", response.json())


def test_syndicat_is_not_compared(client):
    response = client.get("/fiches/253500000/financements.par_habitant.json")

    assert response.status_code == 404
