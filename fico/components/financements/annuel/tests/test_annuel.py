def test_last_completed_years(client, reference):
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
