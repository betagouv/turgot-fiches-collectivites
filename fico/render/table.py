"""A component's raw values as a spreadsheet: one header row, then one row per
record."""

import csv
import io
from dataclasses import dataclass

from openpyxl import Workbook


@dataclass
class Table:
    columns: list[str]
    rows: list[list]


def to_csv(table: Table) -> bytes:
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(table.columns)
    writer.writerows(table.rows)
    return output.getvalue().encode()


def to_xlsx(table: Table) -> bytes:
    workbook = Workbook(write_only=True)
    sheet = workbook.create_sheet()
    sheet.append(table.columns)
    for row in table.rows:
        sheet.append(row)
    output = io.BytesIO()
    workbook.save(output)
    return output.getvalue()
