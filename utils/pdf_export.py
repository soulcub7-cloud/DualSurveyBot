import json
import os

from questions import QUESTIONS

from reportlab.lib import colors
from reportlab.lib.colors import HexColor
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm

from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    Image,
    HRFlowable
)

import os

BASE_DIR = os.path.dirname(
    os.path.dirname(
        os.path.abspath(__file__)
    )
)

FONT_DIR = os.path.join(
    BASE_DIR,
    "assets",
    "fonts"
)

LOGO_PATH = os.path.join(
    BASE_DIR,
    "assets",
    "logo_ct_assembly.png"
)

pdfmetrics.registerFont(
    TTFont(
        "DejaVu",
        os.path.join(FONT_DIR, "DejaVuSans.ttf")
    )
)

pdfmetrics.registerFont(
    TTFont(
        "DejaVu-Bold",
        os.path.join(FONT_DIR, "DejaVuSans-Bold.ttf")
    )
)

NORMAL_FONT = "DejaVu"
BOLD_FONT = "DejaVu-Bold"


styles = getSampleStyleSheet()


# -----------------------------
# Регистрация шрифтов
# -----------------------------


BOLD_FONT = "DejaVu-Bold"
NORMAL_FONT = "DejaVu"


styles = getSampleStyleSheet()


TITLE_STYLE = ParagraphStyle(
    "TITLE",
    parent=styles["Heading1"],
    fontName=BOLD_FONT,
    fontSize=20,
    alignment=TA_CENTER,
    textColor=HexColor("#123A72"),
    spaceAfter=10
)

SUBTITLE_STYLE = ParagraphStyle(
    "SUBTITLE",
    parent=styles["Heading2"],
    fontName=BOLD_FONT,
    fontSize=12,
    alignment=TA_CENTER,
    textColor=HexColor("#123A72"),
    spaceAfter=12
)

HEADING_STYLE = ParagraphStyle(
    "HEADING",
    parent=styles["Heading2"],
    fontName=BOLD_FONT,
    fontSize=12,
    textColor=HexColor("#123A72"),
    spaceAfter=6
)

NORMAL_STYLE = ParagraphStyle(
    "NORMAL",
    parent=styles["Normal"],
    fontName=NORMAL_FONT,
    fontSize=10,
    leading=16,
    alignment=TA_LEFT
)

CENTER_STYLE = ParagraphStyle(
    "CENTER",
    parent=NORMAL_STYLE,
    alignment=TA_CENTER
)

BIG_STYLE = ParagraphStyle(
    "BIG",
    parent=NORMAL_STYLE,
    fontName=BOLD_FONT,
    fontSize=26,
    alignment=TA_CENTER,
    textColor=HexColor("#123A72")
)
def stars(value):
    value = max(
    1,
    min(
        5,
        int(round(float(value)))
    )
)
    return "★" * value + "☆" * (5 - value)


def final_mark(avg):

    avg = float(avg)

    if avg >= 4.5:
        return "ОТЛИЧНО"

    elif avg >= 3.5:
        return "ХОРОШО"

    elif avg >= 2.5:
        return "УДОВЛЕТВОРИТЕЛЬНО"

    return "ТРЕБУЕТ УЛУЧШЕНИЯ"


def comment_block(title, text):

    tbl = Table(
        [
            [Paragraph(f"<b>{title}</b>", HEADING_STYLE)],
            [Paragraph(text if text else "-", NORMAL_STYLE)]
        ],
        colWidths=[170 * mm]
    )

    tbl.setStyle(TableStyle([

        ("BACKGROUND", (0, 0), (-1, 0), HexColor("#EAF2FD")),

        ("GRID", (0, 0), (-1, -1), 0.4, colors.grey),

        ("BOTTOMPADDING", (0, 0), (-1, -1), 7),

        ("TOPPADDING", (0, 0), (-1, -1), 7)

    ]))

    return tbl


def export_one_pdf(data):

    filename = f"survey_{data[0]}.pdf"

    doc = SimpleDocTemplate(
        filename,
        leftMargin=18 * mm,
        rightMargin=18 * mm,
        topMargin=18 * mm,
        bottomMargin=18 * mm
    )

    story = []

    # --------------------------------------------------
    # Логотип
    # --------------------------------------------------

    logo = Spacer(1, 1)

    logo_path = LOGO_PATH

    if os.path.exists(logo_path):
        logo = Image(
            logo_path,
            width=34 * mm,
            height=24 * mm
        )

    # --------------------------------------------------
    # Шапка документа
    # --------------------------------------------------

    header = Table(
        [
            [
                logo,
                Paragraph(
                    "<b>ТОО «CT Assembly»</b>"
                    "ОЦЕНКА РЕЗУЛЬТАТОВ ПРОИЗВОДСТВЕННОЙ ПРАКТИКИ",
                    SUBTITLE_STYLE
                )
            ]
        ],
        colWidths=[42 * mm, 128 * mm]
    )

    header.setStyle(TableStyle([

    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),

    ("BOTTOMPADDING", (0, 0), (-1, -1), 6),

    ("LINEBELOW", (0, 0), (-1, 0), 1.3, HexColor("#123A72"))

]))

    story.append(header)
    story.append(Spacer(1, 12))
    

    
    student_table = Table(

        [

            ["№ анкеты", data[0]],

            ["Дата", data[1]],

            ["Студент", data[2]],

            ["Специальность", data[3]],

            ["Курс", data[4]],

            ["Предприятие", data[5]],

            ["Наставник", data[6]]

        ],

        colWidths=[45 * mm, 125 * mm]

    )

    student_table.setStyle(TableStyle([

    ("BACKGROUND", (0, 0), (0, -1), HexColor("#EAF2FD")),

    ("FONTNAME", (0, 0), (0, -1), BOLD_FONT),

    ("FONTNAME", (1, 0), (1, -1), NORMAL_FONT),

    ("TEXTCOLOR", (0, 0), (0, -1), HexColor("#123A72")),

    ("GRID", (0, 0), (-1, -1), 0.35, HexColor("#D0D0D0")),

    ("BOTTOMPADDING", (0, 0), (-1, -1), 8),

    ("TOPPADDING", (0, 0), (-1, -1), 8),

    ("LEFTPADDING", (0, 0), (-1, -1), 8),

    ("RIGHTPADDING", (0, 0), (-1, -1), 8),

    ("VALIGN", (0, 0), (-1, -1), "MIDDLE")

]))

    story.append(student_table)

    story.append(Spacer(1, 14))
    story.append(
        Paragraph(
            "ОЦЕНКА КОМПЕТЕНЦИЙ СТУДЕНТА",
            HEADING_STYLE
        )
    )

        # --------------------------------------------------
    # Оценка компетенций
    # --------------------------------------------------

    answers = json.loads(data[7])

    rows = [
        [
            Paragraph("<b>№</b>", CENTER_STYLE),
            Paragraph("<b>Критерий оценки</b>", CENTER_STYLE),
            Paragraph("<b>Оценка</b>", CENTER_STYLE)
        ]
    ]

    for i, answer in enumerate(answers):

        rows.append([
            Paragraph(str(i + 1), CENTER_STYLE),
            Paragraph(QUESTIONS[i], NORMAL_STYLE),
            Paragraph(stars(answer), CENTER_STYLE)
        ])

    score_table = Table(
        rows,
        colWidths=[12 * mm, 128 * mm, 30 * mm],
        repeatRows=1
    )

    score_table.setStyle(TableStyle([

        ("FONTNAME", (0, 0), (-1, -1), NORMAL_FONT),
        ("FONTNAME", (0, 0), (-1, 0), BOLD_FONT),

        ("BACKGROUND", (0, 0), (-1, 0), HexColor("#123A72")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),

        ("GRID", (0, 0), (-1, -1), 0.35, colors.grey),

        ("VALIGN", (0, 0), (-1, -1), "TOP"),

        ("ALIGN", (0, 0), (0, -1), "CENTER"),
        ("ALIGN", (2, 1), (2, -1), "CENTER"),

        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),

        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6)

    ]))

    for r in range(1, len(rows)):
        if r % 2 == 0:
            score_table.setStyle(TableStyle([
                ("BACKGROUND", (0, r), (-1, r), HexColor("#F8F9FA"))
            ]))

    story.append(score_table)

    story.append(Spacer(1, 15))

        # --------------------------------------------------
    # Итоговая оценка
    # --------------------------------------------------

    average = float(data[8])
    result = final_mark(average)

    if average >= 4.5:
        result_color = HexColor("#2E7D32")   # Зеленый
    elif average >= 3.5:
        result_color = HexColor("#1565C0")   # Синий
    elif average >= 2.5:
        result_color = HexColor("#F9A825")   # Желтый
    else:
        result_color = HexColor("#C62828")   # Красный

    summary = Table(
        [
            [
                Paragraph(
                    "<font color='white'><b>ИТОГОВАЯ ОЦЕНКА</b></font>",
                    CENTER_STYLE
                )
            ],
            [
                Paragraph(
                    f"{average:.2f}",
                    BIG_STYLE
                )
            ],
            [
                Paragraph(
                    f"<font size='18'>{stars(round(average))}</font>",
                    CENTER_STYLE
                )
            ],
            [
                Paragraph(
                    f"<font color='{result_color.hexval()}'><b>{result}</b></font>",
                    CENTER_STYLE
                )
            ]
        ],
        colWidths=[170 * mm]
    )

    summary.setStyle(TableStyle([

        ("BACKGROUND", (0, 0), (-1, 0), HexColor("#123A72")),

        ("BACKGROUND", (0, 1), (-1, -1), HexColor("#FAFAFA")),

        ("GRID", (0, 0), (-1, -1), 0.6, HexColor("#BDBDBD")),

        ("BOTTOMPADDING", (0, 0), (-1, -1), 12),

        ("TOPPADDING", (0, 0), (-1, -1), 12),

        ("ALIGN", (0, 0), (-1, -1), "CENTER")

    ]))

    story.append(summary)

    story.append(Spacer(1, 18))
    # --------------------------------------------------
    # Комментарии наставника
    # --------------------------------------------------

    story.append(
        Paragraph(
            "КОММЕНТАРИИ НАСТАВНИКА",
            HEADING_STYLE
        )
    )

    story.append(
        comment_block(
            "Лучшие качества студента",
            data[9]
        )
    )

    story.append(Spacer(1, 8))

    story.append(
        comment_block(
            "Что необходимо улучшить",
            data[10]
        )
    )

    story.append(Spacer(1, 8))

    story.append(
        comment_block(
            "Рекомендации наставника",
            data[11]
        )
    )

    story.append(Spacer(1, 18))

# --------------------------------------------------
# Подпись
# --------------------------------------------------

    story.append(
        HRFlowable(
            width="100%",
            thickness=1,
            color=HexColor("#B0B0B0")
        )
    )

    story.append(Spacer(1, 12))

    signature = Table(

        [

            [
                Paragraph(
                    "<b>Наставник предприятия</b>",
                    NORMAL_STYLE
                ),

                Paragraph(
                    "<b>Подпись</b>",
                    NORMAL_STYLE
                )

            ],

            [

                Paragraph(data[6], NORMAL_STYLE),

                Paragraph("______________________", NORMAL_STYLE)

            ]

        ],

        colWidths=[110 * mm, 60 * mm]

    )

    signature.setStyle(TableStyle([

        ("GRID", (0, 0), (-1, -1), 0.4, colors.grey),

        ("BACKGROUND", (0, 0), (-1, 0), HexColor("#EAF2FD")),

        ("BOTTOMPADDING", (0, 0), (-1, -1), 8),

        ("TOPPADDING", (0, 0), (-1, -1), 8),

        ("VALIGN", (0, 0), (-1, -1), "MIDDLE")

    ]))

    story.append(signature)

    story.append(Spacer(1, 15))
# --------------------------------------------------
# Дата формирования документа
# --------------------------------------------------

    story.append(
        Paragraph(
            f"Дата формирования отчета: {data[1]}",
            CENTER_STYLE
        )
    )

    story.append(Spacer(1, 8))

# --------------------------------------------------
 # Нижний колонтитул
# --------------------------------------------------

    story.append(
        Paragraph(
            "<font size='8' color='#666666'>"
            "Документ сформирован автоматически системой оценки "
            "производственной практики CT Assembly"
            "</font>",
            CENTER_STYLE
        )
    )

# --------------------------------------------------
# Формирование PDF
# --------------------------------------------------

    def add_page_number(canvas, doc):

        canvas.saveState()

        canvas.setFont(NORMAL_FONT, 9)

        canvas.setFillColor(HexColor("#666666"))

        canvas.drawRightString(
            200 * mm,
            10 * mm,
            f"Страница {doc.page}"
        )

        canvas.restoreState()

    doc.build(
        story,
        onFirstPage=add_page_number,
        onLaterPages=add_page_number
    )

    return filename