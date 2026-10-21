def test_every_financeur(client, reference):
    response = client.get("/fiches/35238/financements.financeurs.json")

    assert response.status_code == 200
    reference("financeurs", response.json())


def test_since(client, reference):
    response = client.get("/fiches/35238/financements.financeurs.json?since=2024")

    assert response.status_code == 200
    reference("since", response.json())


def test_no_financement(client, reference):
    response = client.get("/fiches/35001/financements.financeurs.json")

    assert response.status_code == 200
    reference("empty", response.json())
