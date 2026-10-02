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
from reportlab.platypus import KeepTogether, LongTable, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from mentor_feedback_questions import MENTOR_FEEDBACK_OPEN_QUESTIONS


BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FONT_DIR = os.path.join(BASE_DIR, "assets", "fonts")
pdfmetrics.registerFont(TTFont("DejaVu", os.path.join(FONT_DIR, "DejaVuSans.ttf")))
pdfmetrics.registerFont(TTFont("DejaVu-Bold", os.path.join(FONT_DIR, "DejaVuSans-Bold.ttf")))

DARK = HexColor("#263238")
PALE = HexColor("#F3F5F6")
GRID = HexColor("#D9D9D9")
styles = getSampleStyleSheet()
TITLE = ParagraphStyle("FeedbackTitle", parent=styles["Heading1"], fontName="DejaVu-Bold", fontSize=15, leading=19, alignment=TA_CENTER, textColor=DARK, spaceAfter=10)
HEADING = ParagraphStyle("FeedbackHeading", parent=styles["Heading2"], fontName="DejaVu-Bold", fontSize=10.5, leading=14, textColor=DARK, spaceBefore=8, spaceAfter=5)
BODY = ParagraphStyle("FeedbackBody", parent=styles["Normal"], fontName="DejaVu", fontSize=8.5, leading=12, alignment=TA_LEFT)
CENTER = ParagraphStyle("FeedbackCenter", parent=BODY, alignment=TA_CENTER)
HEADER = ParagraphStyle("FeedbackHeader", parent=CENTER, fontName="DejaVu-Bold", textColor=colors.white)
SMALL = ParagraphStyle("FeedbackSmall", parent=BODY, fontSize=7.5, leading=10)


def _p(value, style=BODY):
    return Paragraph(html.escape(str(value if value not in (None, "") else "-")), style)


def export_mentor_feedback_pdf(record):
    filename = f"mentor_feedback_{record['id']}.pdf"
    document = SimpleDocTemplate(
        filename,
        pagesize=A4,
        leftMargin=18 * mm,
        rightMargin=18 * mm,
        topMargin=16 * mm,
        bottomMargin=16 * mm,
        title=f"Отзыв о наставнике №{record['id']}",
    )
    story = [Paragraph("Отзыв студента о наставнике", TITLE)]
    info = [
        [_p("№ отзыва", SMALL), _p(record["id"]), _p("Дата", SMALL), _p(record["submitted_at"])],
        [_p("Наставник", SMALL), _p(record["mentor_name"]), _p("Средняя оценка", SMALL), _p(f"{record['average']}/5")],
        [_p("Предприятие", SMALL), _p(record["enterprise"]), _p("Город / участок", SMALL), _p(" · ".join(value for value in (record["city"], record["workshop"]) if value))],
        [_p("Модуль", SMALL), _p(record["module"]), _p("Студент", SMALL), _p(record["student_name"])],
        [_p("Специальность", SMALL), _p(record["speciality"]), _p("Поток / курс", SMALL), _p(f"{record['stream']} поток · {record['course']} курс")],
    ]
    info_table = Table(info, colWidths=[29 * mm, 56 * mm, 29 * mm, 56 * mm])
    info_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (0, -1), PALE), ("BACKGROUND", (2, 0), (2, -1), PALE),
        ("FONTNAME", (0, 0), (0, -1), "DejaVu-Bold"), ("FONTNAME", (2, 0), (2, -1), "DejaVu-Bold"),
        ("GRID", (0, 0), (-1, -1), 0.4, GRID), ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING", (0, 0), (-1, -1), 6), ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ("TOPPADDING", (0, 0), (-1, -1), 6), ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
    ]))
    story.extend([info_table, Spacer(1, 10), Paragraph("Оценки", HEADING)])
    rows = [[_p("№", HEADER), _p("Критерий", HEADER), _p("Оценка", HEADER)]]
    for number, (question, score) in enumerate(zip(record["questions"], record["ratings"]), 1):
        rows.append([_p(number, CENTER), _p(question.get("text", "")), _p(f"{score}/5", CENTER)])
    table = LongTable(rows, colWidths=[22 * mm, 125 * mm, 23 * mm], repeatRows=1)
    style = [
        ("BACKGROUND", (0, 0), (-1, 0), DARK), ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("GRID", (0, 0), (-1, -1), 0.35, GRID), ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 5), ("RIGHTPADDING", (0, 0), (-1, -1), 5),
        ("TOPPADDING", (0, 0), (-1, -1), 5), ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
    ]
    for row_number in range(2, len(rows), 2):
        style.append(("BACKGROUND", (0, row_number), (-1, row_number), PALE))
    table.setStyle(TableStyle(style))
    story.append(table)
    story.extend([Spacer(1, 10), Paragraph("Развернутые ответы", HEADING)])
    for key, title in MENTOR_FEEDBACK_OPEN_QUESTIONS:
        block = Table([[_p(title, HEADING)], [_p(record.get(key, ""))]], colWidths=[170 * mm])
        block.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), PALE), ("GRID", (0, 0), (-1, -1), 0.35, GRID),
            ("LEFTPADDING", (0, 0), (-1, -1), 7), ("RIGHTPADDING", (0, 0), (-1, -1), 7),
            ("TOPPADDING", (0, 0), (-1, -1), 7), ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
        ]))
        story.append(KeepTogether([block, Spacer(1, 6)]))

    def page_number(canvas, doc):
        canvas.saveState()
        canvas.setFont("DejaVu", 8)
        canvas.setFillColor(HexColor("#666666"))
        canvas.drawRightString(198 * mm, 9 * mm, f"Страница {doc.page}")
        canvas.restoreState()

    document.build(story, onFirstPage=page_number, onLaterPages=page_number)
    return filename
