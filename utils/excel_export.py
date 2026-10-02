from openpyxl import Workbook
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter

from questions import OPEN_QUESTIONS, SECTION_TITLES
from utils.export_common import unpack_survey


DARK = "263238"
WHITE = "FFFFFF"
THIN = Side(style="thin", color="D9D9D9")
BORDER = Border(left=THIN, right=THIN, top=THIN, bottom=THIN)


def _header(sheet):
    for cell in sheet[1]:
        cell.fill = PatternFill("solid", fgColor=DARK)
        cell.font = Font(bold=True, color=WHITE)
        cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
        cell.border = BORDER
    sheet.freeze_panes = "A2"
    sheet.auto_filter.ref = f"A1:{get_column_letter(sheet.max_column)}{sheet.max_row}"


def _body(sheet, centered_columns=()):
    for row in sheet.iter_rows(min_row=2):
        for cell in row:
            cell.border = BORDER
            cell.alignment = Alignment(vertical="top", wrap_text=True)
            if cell.column in centered_columns:
                cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)


def _set_widths(sheet, widths):
    for index, width in enumerate(widths, 1):
        sheet.column_dimensions[get_column_letter(index)].width = width


def export_surveys_to_excel(data):
    surveys = [unpack_survey(item) for item in data]
    workbook = Workbook()

    summary = workbook.active
    summary.title = "Сводка"
    summary.append([
        "№", "Дата", "Студент", "Специальность", "Курс", "Предприятие",
        "Наставник", "Тип анкеты", "Количество критериев", "Общий балл",
        "Hard skills", "Soft skills", "Профпригодность",
    ])
    for survey in surveys:
        summary.append([
            survey["id"], survey["date"], survey["student"], survey["speciality"],
            survey["course"], survey["enterprise"], survey["mentor"],
            survey["questionnaire_title"], len(survey["responses"]), survey["average"],
            survey["hard_average"], survey["soft_average"], survey["suitability_score"],
        ])
    _header(summary)
    _body(summary, centered_columns=(1, 5, 9, 10, 11, 12, 13))
    _set_widths(summary, [9, 20, 32, 30, 10, 22, 30, 20, 17, 14, 14, 14, 17])

    scores = workbook.create_sheet("Оценки")
    scores.append([
        "№ анкеты", "Дата", "Студент", "Предприятие", "Наставник",
        "Тип анкеты", "Код компетенции", "Тип навыка", "Критерий", "Оценка",
    ])
    for survey in surveys:
        for response in survey["responses"]:
            scores.append([
                survey["id"], survey["date"], survey["student"], survey["enterprise"],
                survey["mentor"], survey["questionnaire_title"], response.get("code", "-"),
                SECTION_TITLES.get(response.get("section"), response.get("section", "-")),
                response.get("text", ""), response["score"] if response["score"] is not None else "Не оценивалось",
            ])
    _header(scores)
    _body(scores, centered_columns=(1, 7, 8, 10))
    _set_widths(scores, [12, 20, 32, 22, 30, 20, 18, 18, 82, 12])

    comments = workbook.create_sheet("Комментарии")
    comments.append(["№ анкеты", "Дата", "Студент", "Предприятие", "Наставник", "Вопрос", "Ответ"])
    for survey in surveys:
        for title, value in survey["comments"]:
            comments.append([survey["id"],survey["date"],survey["student"],survey["enterprise"],survey["mentor"],title,value])
    _header(comments)
    _body(comments, centered_columns=(1,))
    _set_widths(comments, [12, 20, 32, 22, 30, 55, 55, 55])

    for sheet in workbook.worksheets:
        sheet.sheet_view.showGridLines = False
        sheet.page_setup.orientation = sheet.ORIENTATION_LANDSCAPE
        sheet.page_setup.fitToWidth = 1
        sheet.page_setup.fitToHeight = 0

    filename = "surveys.xlsx"
    workbook.save(filename)
    return filename
