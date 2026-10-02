from aiogram.types import (
    ReplyKeyboardMarkup,
    KeyboardButton,
    InlineKeyboardMarkup,
    InlineKeyboardButton
)

from database import get_streams, get_students_by_stream, get_mentor_role, can_manage_access


# ============================
# ГЛАВНОЕ МЕНЮ
# ============================
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton


def registration_role_keyboard():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="👨‍🏭 Я наставник", callback_data="register_role_mentor")],
            [InlineKeyboardButton(text="👨‍🎓 Я студент", callback_data="register_role_student")],
        ]
    )


def registration_streams_keyboard():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=f"{stream} поток", callback_data=f"reg_stream_{stream}")]
            for stream in get_streams()
        ]
    )


def registration_students_keyboard(stream):
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=f"👨‍🎓 {fio}", callback_data=f"reg_student_{student_id}")]
            for student_id, fio in get_students_by_stream(stream)
        ] + [[InlineKeyboardButton(text="⬅ К выбору потока", callback_data="reg_back_streams")]]
    )


def student_menu_builder():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🗣 Оценить наставника")],
            [KeyboardButton(text="📋 Мои отзывы")],
            [KeyboardButton(text="ℹ️ О программе")],
        ],
        resize_keyboard=True,
        input_field_placeholder="Выберите действие...",
    )


def main_menu_builder(telegram_id):

    role = get_mentor_role(telegram_id)

    keyboard = [
        [KeyboardButton(text="📝 Новая анкета")],
        [
            KeyboardButton(text="📋 Мои анкеты"),
            KeyboardButton(text="📊 Статистика")
        ],
        [KeyboardButton(text="ℹ️ О программе")]
    ]

    # 👇 Кабинет только для специалиста
    if role == "specialist":
        keyboard.insert(2, [
            KeyboardButton(text="👨‍💼 Кабинет специалиста")
        ])

    return ReplyKeyboardMarkup(
        keyboard=keyboard,
        resize_keyboard=True,
        input_field_placeholder="Выберите действие..."
    )


# ============================
# ВЫБОР ПОТОКА
# ============================

def streams_keyboard():

    keyboard = []

    for stream in get_streams():

        keyboard.append([
            InlineKeyboardButton(
                text=f"{stream} поток",
                callback_data=f"stream_{stream}"
            )
        ])

    keyboard.append([InlineKeyboardButton(text="← Главное меню",callback_data="go_menu")])
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


# ============================
# ВЫБОР СТУДЕНТА
# ============================

def students_keyboard(stream):

    students = get_students_by_stream(stream)

    keyboard = []

    for student_id, fio in students:

        keyboard.append([
            InlineKeyboardButton(
                text=f"👨‍🎓 {fio}",
                callback_data=f"student_{student_id}"
            )
        ])

    keyboard.append([
        InlineKeyboardButton(
            text="⬅ К выбору потока",
            callback_data="back_streams"
        )
    ])

    return InlineKeyboardMarkup(inline_keyboard=keyboard)


# ============================
# ОЦЕНКИ
# ============================

def marks_keyboard():

    return InlineKeyboardMarkup(
        inline_keyboard=[[
            InlineKeyboardButton(text="⭐1", callback_data="mark_1"),
            InlineKeyboardButton(text="⭐2", callback_data="mark_2"),
            InlineKeyboardButton(text="⭐3", callback_data="mark_3"),
            InlineKeyboardButton(text="⭐4", callback_data="mark_4"),
            InlineKeyboardButton(text="⭐5", callback_data="mark_5")
        ]]
    )


def mentor_directory_keyboard(mentors):
    keyboard = []
    for mentor in mentors:
        location = " · ".join(item for item in (mentor.get("enterprise"), mentor.get("city")) if item)
        label = mentor.get("full_name", "Наставник")
        if location:
            label = f"{label} · {location}"
        keyboard.append([
            InlineKeyboardButton(
                text=label[:64],
                callback_data=f"feedback_mentor_{mentor['lms_id']}",
            )
        ])
    keyboard.append([InlineKeyboardButton(text="← Главное меню",callback_data="go_menu")])
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def start_mentor_feedback_keyboard():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="▶ Начать отзыв", callback_data="feedback_start")],
            [InlineKeyboardButton(text="👨‍🏭 Выбрать другого наставника", callback_data="feedback_back_mentors")],
        ]
    )
# ============================
# КАБИНЕТ СПЕЦИАЛИСТА
# ============================

specialist_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="📋 Все анкеты")],
        [KeyboardButton(text="👨‍🎓 Студенты")],
        [KeyboardButton(text="👨‍🏭 Наставники")],
        [KeyboardButton(text="📊 Статистика")],
        [KeyboardButton(text="📥 Экспорт Excel")],
        [KeyboardButton(text="🔙 Главное меню")]
    ],
    resize_keyboard=True
)
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


def back_keyboard(target="go_menu", label="← Главное меню"):
    return InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text=label,callback_data=target)]])


def statistics_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Общая статистика",callback_data="sp_statistics")],
        [InlineKeyboardButton(text="Статистика отзывов",callback_data="sp_feedback_statistics")],
        [InlineKeyboardButton(text="← Кабинет специалиста",callback_data="back_specialist")]])


def exports_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Оценки наставников — Excel",callback_data="sp_export_excel")],
        [InlineKeyboardButton(text="Отзывы студентов — Excel",callback_data="sp_feedback_excel")],
        [InlineKeyboardButton(text="← Кабинет специалиста",callback_data="back_specialist")]])


def specialist_panel_keyboard(telegram_id=0):
    items=[("📋 Все анкеты","sp_all_surveys"),("👨‍🎓 Студенты","sp_students"),("👨‍🏭 Наставники","sp_mentors"),("📊 Статистика","sp_stats_menu"),("🗣 Отзывы студентов","sp_mentor_feedback"),("📥 Экспорт","sp_exports_menu")]
    if can_manage_access(telegram_id): items.insert(0,("🔐 Доступ к кабинету","access_list_0"))
    items.append(("← Главное меню","go_menu"))
    return InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text=t,callback_data=c)] for t,c in items])

# ==========================================
# СПИСОК АНКЕТ
# ==========================================

from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


def surveys_keyboard(surveys):

    keyboard = []

    for survey in surveys:

        keyboard.append(
            [
                InlineKeyboardButton(
                    text=f"👨‍🎓 {survey[1]}   ⭐ {survey[4]}",
                    callback_data=f"sp_survey_{survey[0]}"
                )
            ]
        )

    keyboard.append(
        [
            InlineKeyboardButton(
                text="⬅ Назад",
                callback_data="back_specialist"
            )
        ]
    )

    return InlineKeyboardMarkup(
        inline_keyboard=keyboard
    )
# ==========================================
# КНОПКИ ПРОСМОТРА АНКЕТЫ
# ==========================================

def survey_view_keyboard(survey_id):

    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="📄 PDF",
                    callback_data=f"pdf_{survey_id}"
                ),
                InlineKeyboardButton(
                    text="📥 Excel",
                    callback_data=f"excel_{survey_id}"
                )
            ],
            [
                InlineKeyboardButton(
                    text="🗑 Удалить",
                    callback_data=f"sp_delete_{survey_id}"
                )
            ],
            [
                InlineKeyboardButton(
                    text="⬅ К списку",
                    callback_data="sp_all_surveys"
                )
            ]
        ]
    )
# ==========================================
# ПОДТВЕРЖДЕНИЕ УДАЛЕНИЯ
# ==========================================

def confirm_delete_keyboard(survey_id):

    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="✅ Да",
                    callback_data=f"sp_confirm_delete_{survey_id}"
                ),
                InlineKeyboardButton(
                    text="❌ Нет",
                    callback_data=f"sp_survey_{survey_id}"
                )
            ]
        ]
    )


def mentor_feedback_list_keyboard(records):
    keyboard = []
    for record in records[:50]:
        keyboard.append([
            InlineKeyboardButton(
                text=f"{record['mentor_name']} · {record['average']}/5 · {record['submitted_at'][:10]}",
                callback_data=f"sp_feedback_{record['id']}",
            )
        ])
    keyboard.append([InlineKeyboardButton(text="⬅ Назад", callback_data="back_specialist")])
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def mentor_feedback_view_keyboard(feedback_id):
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="📄 PDF", callback_data=f"feedback_pdf_{feedback_id}"),
                InlineKeyboardButton(text="📥 Excel", callback_data=f"feedback_excel_{feedback_id}"),
            ],
            [InlineKeyboardButton(text="⬅ К отзывам", callback_data="sp_mentor_feedback")],
        ]
    )
# ==========================================
# ПРЕДПРИЯТИЯ
# ==========================================

from database import get_enterprises


# ==========================================
# ПРЕДПРИЯТИЯ
# ==========================================

def enterprises_keyboard():

    keyboard = []

    for enterprise_id, enterprise in get_enterprises():

        keyboard.append([
            InlineKeyboardButton(
                text=f"🏭 {enterprise}",
                callback_data=f"enterprise_{enterprise_id}"
            )
        ])

    keyboard.append([
        InlineKeyboardButton(
            text="⬅ Выбрать другой поток",
            callback_data="back_streams"
        )
    ])

    keyboard.append([
        InlineKeyboardButton(
            text="⬅ Выбрать другого студента",
            callback_data="back_students"
        )
    ])

    return InlineKeyboardMarkup(
        inline_keyboard=keyboard
    )
def start_survey_keyboard():

    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="▶ Начать анкетирование",
                    callback_data="start_survey"
                )
            ],
            [
                InlineKeyboardButton(
                    text="🏭 Выбрать другое предприятие",
                    callback_data="back_enterprises"
                )
            ],
            [
                InlineKeyboardButton(
                    text="👨‍🎓 Выбрать другого студента",
                    callback_data="back_students"
                )
            ]
        ]
    )
