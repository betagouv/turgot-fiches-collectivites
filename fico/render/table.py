"""A table as a file: CSV and XLSX of raw values, GeoJSON when a column holds
geometries."""

import csv
import io
import json

from openpyxl import Workbook

from ..components.table import Table


def _cell(value):
    return json.dumps(value) if isinstance(value, (dict, list)) else value


def _rows(table: Table) -> list[list]:
    return [[_cell(cell.value) for cell in row] for row in table.rows]


def to_csv(table: Table) -> bytes:
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(table.columns)
    writer.writerows(_rows(table))
    return output.getvalue().encode()


def to_xlsx(table: Table) -> bytes:
    workbook = Workbook(write_only=True)
    sheet = workbook.create_sheet()
    sheet.append(table.columns)
    for row in _rows(table):
        sheet.append(row)
    output = io.BytesIO()
    workbook.save(output)
    return output.getvalue()


def _is_geometry(value) -> bool:
    return isinstance(value, dict) and "coordinates" in value


def geometry_column(table: Table) -> int | None:
    for x in range(len(table.columns)):
        if any(_is_geometry(row[x].value) for row in table.rows):
            return x
    return None


def to_geojson(table: Table) -> dict:
    """One feature per row, the other columns as its properties."""
    x = geometry_column(table)
    return {
        "type": "FeatureCollection",
        "features": [
            {
                "type": "Feature",
                "properties": {
                    column: cell.value
                    for i, (column, cell) in enumerate(zip(table.columns, row))
                    if i != x
                },
                "geometry": row[x].value,
            }
            for row in table.rows
        ],
    }
