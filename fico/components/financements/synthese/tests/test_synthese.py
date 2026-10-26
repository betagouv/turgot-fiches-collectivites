def test_every_financeur(client, reference):
    response = client.get("/fiches/35238/financements.synthese.json")

    assert response.status_code == 200
    reference("synthese", response.json())


def test_one_financeur(client, reference):
    response = client.get("/fiches/35238/financements.synthese.json?financeur=DSIL")

    assert response.status_code == 200
    reference("dsil", response.json())


def test_financeur_without_financement(client, reference):
    response = client.get("/fiches/35238/financements.synthese.json?financeur=DETR")

    assert response.status_code == 200
    reference("detr", response.json())


def test_since(client, reference):
    response = client.get("/fiches/35238/financements.synthese.json?since=2023")

    assert response.status_code == 200
    reference("since", response.json())


def test_png(client):
    response = client.get("/fiches/35238/financements.synthese.png")

    assert response.status_code == 200
    assert response.headers["content-type"] == "image/png"
    assert response.content.startswith(b"\x89PNG")


def test_svg(client, reference):
    response = client.get("/fiches/35238/financements.synthese.svg")

    assert response.status_code == 200
    assert response.headers["content-type"] == "image/svg+xml"
    reference("synthese.svg", response.text)
