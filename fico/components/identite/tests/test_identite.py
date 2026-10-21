def test_commune(client, reference):
    response = client.get("/fiches/35238/identite.json")

    assert response.status_code == 200
    reference("commune", response.json())


def test_commune_without_maire_nor_figures(client, reference):
    response = client.get("/fiches/35001/identite.json")

    assert response.status_code == 200
    reference("commune_sparse", response.json())


def test_epci(client, reference):
    response = client.get("/fiches/243500139/identite.json")

    assert response.status_code == 200
    reference("epci", response.json())


def test_syndicat_without_president(client, reference):
    response = client.get("/fiches/253500000/identite.json")

    assert response.status_code == 200
    reference("syndicat", response.json())
