import io
from decimal import Decimal

from odfdo import Document
from openpyxl import load_workbook

URL = "/fiches/35238/financements.historique"


def test_csv(client):
    response = client.get(f"{URL}.csv")

    assert response.status_code == 200
    assert response.headers["content-type"] == "text/csv; charset=utf-8"
    assert response.text == (
        "Année,Financeur,Référence,Projet,Coût,Subvention,Taux\r\n"
        "2024,Fonds Vert,,Rénovation du gymnase,200000.0,20000.0,0.1\r\n"
        "2023,DSIL,,Rénovation du gymnase,200000.0,60000.0,0.3\r\n"
    )


def test_xlsx(client):
    response = client.get(f"{URL}.xlsx")

    assert response.status_code == 200
    sheet = load_workbook(io.BytesIO(response.content)).active
    assert list(sheet.values) == [
        ("Année", "Financeur", "Référence", "Projet", "Coût", "Subvention", "Taux"),
        (2024, "Fonds Vert", None, "Rénovation du gymnase", 200000, 20000, 0.1),
        (2023, "DSIL", None, "Rénovation du gymnase", 200000, 60000, 0.3),
    ]


def test_ods(client):
    response = client.get(f"{URL}.ods")

    assert response.status_code == 200
    sheet = Document(io.BytesIO(response.content)).body.get_table(0)
    # odfdo reads decimal numbers back as Decimal.
    assert sheet.get_values() == [
        ["Année", "Financeur", "Référence", "Projet", "Coût", "Subvention", "Taux"],
        [
            2024,
            "Fonds Vert",
            None,
            "Rénovation du gymnase",
            200000,
            20000,
            Decimal("0.1"),
        ],
        [2023, "DSIL", None, "Rénovation du gymnase", 200000, 60000, Decimal("0.3")],
    ]
