def test_commune(client, reference):
    response = client.get("/fiches/35238/programmes.json")

    assert response.status_code == 200
    reference("commune", response.json())


def test_no_programme(client, reference):
    response = client.get("/fiches/35001/programmes.json")

    assert response.status_code == 200
    reference("empty", response.json())


def test_groupement_has_none(client):
    response = client.get("/fiches/243500139/programmes.json")

    assert response.status_code == 404
