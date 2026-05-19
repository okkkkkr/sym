from io import BytesIO
from typing import Iterable

from openpyxl import Workbook


def build_xlsx_content(sheet_title: str, headers: list[str], rows: Iterable[Iterable[object]]) -> bytes:
    workbook = Workbook()
    worksheet = workbook.active
    worksheet.title = sheet_title
    worksheet.append(headers)

    for row in rows:
        worksheet.append(list(row))

    buffer = BytesIO()
    workbook.save(buffer)
    return buffer.getvalue()