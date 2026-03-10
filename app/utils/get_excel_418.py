from io import BytesIO
from openpyxl import Workbook
from openpyxl.styles import Alignment, Border, Side, Font


def rows_to_excel(rows=None, date=None, fio=None):
    wb = Workbook()
    ws = wb.active
    ws.title = "Report"

    offset = 10

    def r(row):
        return row + offset

    def cell(col, row):
        return f"{col}{r(row)}"

    center = Alignment(horizontal="center", vertical="center", wrap_text=True)
    left = Alignment(horizontal="left", vertical="center", wrap_text=True)
    right = Alignment(horizontal="right", vertical="center", wrap_text=True)

    bold = Font(bold=True)

    border = Border(
        left=Side(style="thin"),
        right=Side(style="thin"),
        top=Side(style="thin"),
        bottom=Side(style="thin"),
    )

    # -------- TOP TEXT (HEADER OF DOCUMENT) --------

    ws.merge_cells("A6:I6")
    ws.merge_cells("B8:H8")

    ws["I1"] = f"{date}"

    ws["I1"].alignment = right
    ws["I1"].font = Font(italic=True)

    ws["A6"] = "Поручение № ______ от __________ 20___ г."
    ws["A6"].alignment = center
    ws["A6"].font = Font(bold=True, size=14)

    ws["B8"] = (
        "Департаменту бухгалтерского учета, отчетности и инвестиционного анализа "
        "акционерного общества «Государственный фонд социального страхования» "
        "перевести на счет Государственной корпорации следующие суммы излишне "
        "(ошибочно) уплаченных социальных отчислений и (или) пени:"
    )
    ws["B8"].alignment = center
    ws.row_dimensions[8].height = 60

    # -------- TABLE MERGES --------

    merges = [
        ("A",1,"A",4), ("B",1,"C",1), ("D",1,"I",1),
        ("B",2,"B",4), ("C",2,"C",4),
        ("D",2,"E",2), ("F",2,"G",2), ("H",2,"I",2),
        ("D",3,"D",4), ("E",3,"E",4), ("F",3,"F",4),
        ("G",3,"G",4), ("H",3,"H",4), ("I",3,"I",4)
    ]

    for c1, r1, c2, r2 in merges:
        ws.merge_cells(f"{c1}{r(r1)}:{c2}{r(r2)}")

    # -------- TABLE HEADER TEXT --------

    header = {
        ("A",1): "КНП",
        ("B",1): "Всего",
        ("B",2): "Количество участников (чел.)",
        ("C",2): "Сумма (тенге)",
        ("D",1): "в том числе",
        ("D",2): "СО (КНП 026)",
        ("F",2): "Пени (КНП 094)",
        ("H",2): "ЕП",
        ("D",3): "Количество участников (чел.)",
        ("E",3): "Сумма (тенге)",
        ("F",3): "Количество участников (чел.)",
        ("G",3): "Сумма (тенге)",
        ("H",3): "Количество участников (чел.)",
        ("I",3): "Сумма (тенге)",
    }

    for (col, row), text in header.items():
        ws[cell(col, row)] = text

    ws[cell("A",5)] = "026"
    ws[cell("A",6)] = "094"

    # -------- STYLES --------

    for row in ws[f"A{r(1)}:I{r(4)}"]:
        for c in row:
            c.alignment = center
            c.font = bold
            c.border = border

    for row in ws[f"A{r(5)}:I{r(7)}"]:
        for c in row:
            c.alignment = center
            c.border = border

    # -------- NUMBER FORMAT --------

    for col, row in [
        ("E",5), ("G",5), ("I",5),
        ("E",6), ("G",6), ("I",6),
        ("C",5), ("C",6), ("C",7)
    ]:
        ws[cell(col, row)].number_format = '# ### ### ##0.00'

    # -------- DATA --------

    if rows:
        for amount, count, knp, typ in rows:

            if knp == "026":
                ws[cell("D",5)] = count
                ws[cell("E",5)] = amount

            elif knp == "094" and typ is None:
                ws[cell("F",6)] = count
                ws[cell("G",6)] = amount

            elif knp == "094" and typ == "О":
                ws[cell("H",6)] = count
                ws[cell("I",6)] = amount

    # -------- SUM FUNCTION --------

    def s(coords):
        return sum(ws[cell(c, r)].value or 0 for c, r in coords)

    ws[cell("C",5)] = s([("E",5), ("G",5), ("I",5)])
    ws[cell("C",6)] = s([("E",6), ("G",6), ("I",6)])

    ws[cell("B",5)] = s([("D",5), ("F",5), ("H",5)])
    ws[cell("B",6)] = s([("D",6), ("F",6), ("H",6)])

    ws[cell("C",7)] = s([
        ("E",5), ("G",5), ("I",5),
        ("E",6), ("G",6), ("I",6)
    ])

    ws[cell("B",7)] = s([
        ("D",5), ("F",5), ("H",5),
        ("D",6), ("F",6), ("H",6)
    ])

    ws.merge_cells(f"{cell('A',10)}:{cell('I',10)}")
    ws[cell("A",10)] = "Курирующий руководитель ДРП__________________________________________"
    ws[cell("A",10)].alignment = center
    ws[cell("A",10)].font = Font(bold=True, size=14)

    ws.merge_cells(f"{cell('A', 15)}:{cell('I', 15)}")
    ws[cell("A", 15)] = f"Исп. {fio}"
    ws[cell("A", 15)].alignment = left
    ws[cell("A", 15)].font = Font(italic=True)

    # -------- COLUMN WIDTH --------

    widths = [10, 20, 15, 20, 15, 20, 15, 20, 15]

    for i, w in enumerate(widths, 1):
        ws.column_dimensions[chr(64 + i)].width = w

    stream = BytesIO()
    wb.save(stream)
    stream.seek(0)

    return stream