def test_commune_in_its_departement(client, reference):
    response = client.get("/fiches/35238/financements.carte.json?perimetre=departement")

    assert response.status_code == 200
    reference("commune_departement", response.json())


def test_commune_in_its_interco(client, reference):
    response = client.get("/fiches/35238/financements.carte.json?perimetre=interco")

    assert response.status_code == 200
    reference("commune_interco", response.json())


def test_epci_in_its_departement(client, reference):
    response = client.get(
        "/fiches/243500139/financements.carte.json?perimetre=departement"
    )

    assert response.status_code == 200
    reference("epci_departement", response.json())


def test_epci_has_no_interco_map(client):
    response = client.get("/fiches/243500139/financements.carte.json?perimetre=interco")

    assert response.status_code == 404


def test_syndicat_has_no_map(client):
    response = client.get(
        "/fiches/253500000/financements.carte.json?perimetre=departement"
    )

    assert response.status_code == 404
