import html
import os

from reportlab.lib import colors
from reportlab.lib.colors import HexColor
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    LongTable,
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

from questions import OPEN_QUESTIONS, SECTION_TITLES
from utils.export_common import unpack_survey


BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FONT_DIR = os.path.join(BASE_DIR, "assets", "fonts")
pdfmetrics.registerFont(TTFont("DejaVu", os.path.join(FONT_DIR, "DejaVuSans.ttf")))
pdfmetrics.registerFont(TTFont("DejaVu-Bold", os.path.join(FONT_DIR, "DejaVuSans-Bold.ttf")))

NORMAL_FONT = "DejaVu"
BOLD_FONT = "DejaVu-Bold"
DARK = HexColor("#263238")
PALE = HexColor("#F3F5F6")
GRID = HexColor("#D9D9D9")

styles = getSampleStyleSheet()
TITLE = ParagraphStyle(
    "SurveyTitle", parent=styles["Heading1"], fontName=BOLD_FONT,
    fontSize=16, leading=20, alignment=TA_CENTER, textColor=DARK, spaceAfter=10,
)
HEADING = ParagraphStyle(
    "SurveyHeading", parent=styles["Heading2"], fontName=BOLD_FONT,
    fontSize=11, leading=14, textColor=DARK, spaceBefore=8, spaceAfter=5,
)
BODY = ParagraphStyle(
    "SurveyBody", parent=styles["Normal"], fontName=NORMAL_FONT,
    fontSize=8.5, leading=12, alignment=TA_LEFT,
)
BODY_CENTER = ParagraphStyle("SurveyCenter", parent=BODY, alignment=TA_CENTER)
HEADER = ParagraphStyle(
    "SurveyHeader", parent=BODY_CENTER, fontName=BOLD_FONT, textColor=colors.white,
)
SMALL = ParagraphStyle("SurveySmall", parent=BODY, fontSize=7.5, leading=10)


def _p(value, style=BODY):
    return Paragraph(html.escape(str(value if value not in (None, "") else "-")), style)


def _score_label(score):
    if score is None: return "Не оценивалось"
    labels = {1: "1 · не проявляется", 2: "2 · слабо", 3: "3 · удовлетворительно", 4: "4 · хорошо", 5: "5 · отлично"}
    return labels.get(int(score), str(score))


def _comment_block(title, text):
    table = Table(
        [[_p(title, HEADING)], [_p(text)]],
        colWidths=[170 * mm],
    )
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), PALE),
        ("BOX", (0, 0), (-1, -1), 0.5, GRID),
        ("INNERGRID", (0, 0), (-1, -1), 0.35, GRID),
        ("LEFTPADDING", (0, 0), (-1, -1), 7),
        ("RIGHTPADDING", (0, 0), (-1, -1), 7),
        ("TOPPADDING", (0, 0), (-1, -1), 7),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
    ]))
    return table


def export_one_pdf(data):
    survey = unpack_survey(data)
    filename = f"survey_{survey['id']}.pdf"
    document = SimpleDocTemplate(
        filename, pagesize=A4,
        leftMargin=18 * mm, rightMargin=18 * mm,
        topMargin=16 * mm, bottomMargin=16 * mm,
        title=f"Анкета №{survey['id']} · {survey['student']}",
    )

    story = [
        Paragraph(f"{html.escape(survey['enterprise'])}<br/>Анкета наставника о студенте", TITLE),
    ]

    info = [
        [_p("№ анкеты", SMALL), _p(survey["id"]), _p("Дата", SMALL), _p(survey["date"])],
        [_p("Студент", SMALL), _p(survey["student"]), _p("Наставник", SMALL), _p(survey["mentor"])],
        [_p("Специальность", SMALL), _p(survey["speciality"]), _p("Курс", SMALL), _p(survey["course"])],
        [_p("Предприятие", SMALL), _p(survey["enterprise"]), _p("Тип анкеты", SMALL), _p(survey["questionnaire_title"])],
    ]
    info_table = Table(info, colWidths=[28 * mm, 57 * mm, 28 * mm, 57 * mm])
    info_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (0, -1), PALE),
        ("BACKGROUND", (2, 0), (2, -1), PALE),
        ("FONTNAME", (0, 0), (0, -1), BOLD_FONT),
        ("FONTNAME", (2, 0), (2, -1), BOLD_FONT),
        ("GRID", (0, 0), (-1, -1), 0.4, GRID),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
    ]))
    story.extend([info_table, Spacer(1, 10)])

    summary_rows = [
        [_p("Общий балл", HEADER), _p("Hard skills", HEADER), _p("Soft skills", HEADER), _p("Профпригодность", HEADER)],
        [_p((f"{survey['average']:.2f}" if survey["average"] is not None else "Не оценивалось"), BODY_CENTER), _p(survey["hard_average"], BODY_CENTER), _p(survey["soft_average"], BODY_CENTER), _p(survey["suitability_score"], BODY_CENTER)],
    ]
    summary = Table(summary_rows, colWidths=[42.5 * mm] * 4)
    summary.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), DARK),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, -1), BOLD_FONT),
        ("GRID", (0, 0), (-1, -1), 0.4, GRID),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 7),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
    ]))
    story.extend([summary, Spacer(1, 10), Paragraph("Оценка компетенций", HEADING)])

    rows = [[_p("Код", HEADER), _p("Тип", HEADER), _p("Критерий оценки", HEADER), _p("Оценка", HEADER)]]
    for response in survey["responses"]:
        rows.append([
            _p(response.get("code", "-"), BODY_CENTER),
            _p(SECTION_TITLES.get(response.get("section"), response.get("section", "-")), BODY_CENTER),
            _p(response.get("text", "")),
            _p(_score_label(response["score"]), BODY_CENTER),
        ])
    scores = LongTable(rows, colWidths=[25 * mm, 25 * mm, 97 * mm, 23 * mm], repeatRows=1)
    score_style = [
        ("BACKGROUND", (0, 0), (-1, 0), DARK),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), BOLD_FONT),
        ("GRID", (0, 0), (-1, -1), 0.35, GRID),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 5),
        ("RIGHTPADDING", (0, 0), (-1, -1), 5),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
    ]
    for row_number in range(2, len(rows), 2):
        score_style.append(("BACKGROUND", (0, row_number), (-1, row_number), PALE))
    scores.setStyle(TableStyle(score_style))
    story.append(scores)

    story.extend([Spacer(1, 12), Paragraph("Комментарии наставника", HEADING)])
    for title, value in survey["comments"]:
        story.extend([_comment_block(title, value), Spacer(1, 7)])

    signature = Table(
        [[_p("Наставник", SMALL), _p(survey["mentor"]), _p("Подпись", SMALL), _p("________________")]],
        colWidths=[25 * mm, 75 * mm, 22 * mm, 48 * mm],
    )
    signature.setStyle(TableStyle([
        ("GRID", (0, 0), (-1, -1), 0.4, GRID),
        ("BACKGROUND", (0, 0), (0, 0), PALE),
        ("BACKGROUND", (2, 0), (2, 0), PALE),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 7),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
    ]))
    story.extend([Spacer(1, 6), signature])

    def page_number(canvas, doc):
        canvas.saveState()
        canvas.setFont(NORMAL_FONT, 8)
        canvas.setFillColor(HexColor("#666666"))
        canvas.drawRightString(198 * mm, 9 * mm, f"Страница {doc.page}")
        canvas.restoreState()

    document.build(story, onFirstPage=page_number, onLaterPages=page_number)
    return filename
