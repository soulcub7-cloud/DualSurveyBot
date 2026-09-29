from openpyxl import Workbook
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side

from questions import OPEN_QUESTIONS, SECTION_TITLES
from utils.export_common import unpack_survey


RED = "C62828"
DARK = "263238"
LIGHT = "F3F5F6"
PALE_RED = "FDECEC"
PALE_BLUE = "EAF2FD"
WHITE = "FFFFFF"
THIN = Side(style="thin", color="D9D9D9")
BORDER = Border(left=THIN, right=THIN, top=THIN, bottom=THIN)


def _style_header(row):
    for cell in row:
        cell.fill = PatternFill("solid", fgColor=DARK)
        cell.font = Font(bold=True, color=WHITE)
        cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
        cell.border = BORDER


def _score_fill(score):
    if score <= 2:
        return "F8D7DA"
    if score == 3:
        return "FFF3CD"
    if score == 4:
        return "DFF1D8"
    return "C6E8C6"


def export_one_survey(data):
    survey = unpack_survey(data)
    workbook = Workbook()
    sheet = workbook.active
    sheet.title = "Анкета"
    sheet.sheet_view.showGridLines = False

    sheet.merge_cells("A1:E1")
    sheet["A1"] = f"{survey['enterprise']} · Анкета наставника о студенте"
    sheet["A1"].font = Font(bold=True, size=16, color=DARK)
    sheet["A1"].alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
    sheet.row_dimensions[1].height = 34

    sheet.append([])
    sheet.append(["Поле", "Значение", "Поле", "Значение"])
    _style_header(sheet[sheet.max_row])
    info_rows = [
        ("№ анкеты", survey["id"], "Дата", survey["date"]),
        ("Студент", survey["student"], "Наставник", survey["mentor"]),
        ("Специальность", survey["speciality"], "Курс", survey["course"]),
        ("Предприятие", survey["enterprise"], "Тип анкеты", survey["questionnaire_title"]),
    ]
    for values in info_rows:
        sheet.append(values)
        row = sheet[sheet.max_row]
        for index, cell in enumerate(row):
            cell.border = BORDER
            cell.alignment = Alignment(vertical="center", wrap_text=True)
            if index in (0, 2):
                cell.fill = PatternFill("solid", fgColor=PALE_BLUE)
                cell.font = Font(bold=True, color=DARK)

    sheet.append([])
    sheet.append(["Итог", "Общий балл", "Hard skills", "Soft skills", "Профессиональная пригодность"])
    _style_header(sheet[sheet.max_row])
    sheet.append([
        "Результат",
        survey["average"],
        survey["hard_average"] if survey["hard_average"] is not None else "-",
        survey["soft_average"] if survey["soft_average"] is not None else "-",
        survey["suitability_score"] if survey["suitability_score"] is not None else "-",
    ])
    for cell in sheet[sheet.max_row]:
        cell.border = BORDER
        cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
        cell.font = Font(bold=True, size=12)

    sheet.append([])
    sheet.append(["№", "Код", "Тип", "Критерий оценки", "Оценка"])
    criteria_header = sheet.max_row
    _style_header(sheet[criteria_header])

    for number, response in enumerate(survey["responses"], 1):
        section = response.get("section", "soft")
        sheet.append([
            number,
            response.get("code", "-"),
            SECTION_TITLES.get(section, section),
            response.get("text", ""),
            response["score"],
        ])
        row = sheet[sheet.max_row]
        for cell in row:
            cell.border = BORDER
            cell.alignment = Alignment(vertical="center", wrap_text=True)
        row[0].alignment = Alignment(horizontal="center", vertical="center")
        row[1].alignment = Alignment(horizontal="center", vertical="center")
        row[2].alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
        row[4].alignment = Alignment(horizontal="center", vertical="center")
        row[4].font = Font(bold=True)
        row[4].fill = PatternFill("solid", fgColor=_score_fill(int(response["score"])))
        sheet.row_dimensions[sheet.max_row].height = 34

    last_criteria_row = sheet.max_row
    comments = [
        (OPEN_QUESTIONS[0], survey["best"]),
        (OPEN_QUESTIONS[1], survey["improve"]),
        (OPEN_QUESTIONS[2], survey["recommendation"]),
    ]
    for title, text in comments:
        sheet.append([])
        sheet.append([title])
        sheet.merge_cells(start_row=sheet.max_row, start_column=1, end_row=sheet.max_row, end_column=5)
        heading = sheet.cell(sheet.max_row, 1)
        heading.fill = PatternFill("solid", fgColor=DARK)
        heading.font = Font(bold=True, color=WHITE)
        heading.alignment = Alignment(vertical="center", wrap_text=True)
        heading.border = BORDER
        sheet.append([text or "-"])
        sheet.merge_cells(start_row=sheet.max_row, start_column=1, end_row=sheet.max_row, end_column=5)
        body = sheet.cell(sheet.max_row, 1)
        body.alignment = Alignment(vertical="top", wrap_text=True)
        body.border = BORDER
        sheet.row_dimensions[sheet.max_row].height = 48

    widths = {"A": 10, "B": 18, "C": 24, "D": 82, "E": 16}
    for column, width in widths.items():
        sheet.column_dimensions[column].width = width

    sheet.freeze_panes = f"A{criteria_header + 1}"
    sheet.auto_filter.ref = f"A{criteria_header}:E{last_criteria_row}"
    sheet.page_setup.paperSize = sheet.PAPERSIZE_A4
    sheet.page_setup.orientation = sheet.ORIENTATION_LANDSCAPE
    sheet.page_setup.fitToWidth = 1
    sheet.page_setup.fitToHeight = 0
    sheet.print_area = f"A1:E{sheet.max_row}"
    sheet.print_title_rows = f"{criteria_header}:{criteria_header}"

    filename = f"survey_{survey['id']}.xlsx"
    workbook.save(filename)
    return filename
