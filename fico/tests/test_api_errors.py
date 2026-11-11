from datetime import UTC, datetime

from fico.components import financements


def test_invalid_identifier(client):
    response = client.get("/fiches/abc.json")

    assert response.status_code == 400
    assert response.json()["detail"] == (
        "abc n'est ni un code INSEE de commune (5 caractères) ni un SIREN (9 chiffres)."
    )


def test_unknown_collectivite(client):
    response = client.get("/fiches/99999.json")

    assert response.status_code == 404
    assert response.json()["detail"] == "Aucune collectivité connue pour 99999."


def test_unknown_component(client):
    response = client.get("/fiches/35238.json?component=identite,nope")

    assert response.status_code == 400
    assert response.json()["detail"].startswith("Composant(s) inconnu(s) : nope. ")


def test_unreadable_components(client):
    response = client.get(
        "/fiches/35238.json?component=identite,financements.annuel(since=2020"
    )

    assert response.status_code == 400
    assert response.json()["detail"].startswith(
        "Composant(s) inconnu(s) : financements.annuel(since=2020. "
    )


def test_unexpected_parameter(client):
    response = client.get("/fiches/35238/financements.annuel.json?foo=1")

    assert response.status_code == 400
    assert response.json()["detail"] == (
        "financements.annuel n'accepte pas le paramètre foo. "
        "Paramètres acceptés : since."
    )


def test_invalid_value(client):
    response = client.get("/fiches/35238/financements.annuel.json?since=abc")

    assert response.status_code == 400
    assert response.json()["detail"] == (
        "financements.annuel : since=abc invalide, "
        "attendu : {'type': 'int', 'required': False}."
    )


def test_missing_parameter(client):
    response = client.get("/fiches/35238/financements.carte.json")

    assert response.status_code == 400
    assert response.json()["detail"] == (
        "financements.carte : paramètre(s) requis : {'perimetre': "
        "{'type': 'Perimetre', 'required': True, "
        "'choices': ['departement', 'interco']}}."
    )


def test_since_the_current_year(client, freeze):
    freeze(financements, datetime(2026, 6, 1, tzinfo=UTC))

    response = client.get("/fiches/35238/financements.annuel.json?since=2026")

    assert response.status_code == 400
    assert response.json()["detail"] == (
        "since=2026 invalide, attendu : une année révolue, au plus 2025."
    )
