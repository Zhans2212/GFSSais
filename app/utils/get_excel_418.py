from fastapi.responses import StreamingResponse
from io import BytesIO
from openpyxl import Workbook


def rows_to_excel(rows, headers=None):
    """
    Converts a list of lists to an Excel file in memory.

    :param rows: list of lists, e.g. [[1,2,3],[4,5,6]]
    :param headers: optional column headers
    :return: BytesIO object with Excel file
    """

    wb = Workbook()
    ws = wb.active
    ws.title = "Orders"

    if headers:
        ws.append(headers)

    for row in rows:
        ws.append([cell if cell is not None else "" for cell in row])

    stream = BytesIO()
    wb.save(stream)
    stream.seek(0)
    return stream