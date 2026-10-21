def test_every_financement_received(client, reference):
    response = client.get("/fiches/35238/financements.historique.json")

    assert response.status_code == 200
    reference("historique", response.json())


def test_since_keeps_the_financements_without_a_year(client, reference):
    response = client.get("/fiches/35238/financements.historique.json?since=2023")

    assert response.status_code == 200
    reference("since", response.json())


def test_no_financement(client, reference):
    response = client.get("/fiches/35001/financements.historique.json")

    assert response.status_code == 200
    reference("empty", response.json())
