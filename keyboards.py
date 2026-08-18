from aiogram.types import (
    ReplyKeyboardMarkup,
    KeyboardButton,
    InlineKeyboardMarkup,
    InlineKeyboardButton
)

from database import get_streams, get_students_by_stream


# ============================
# ГЛАВНОЕ МЕНЮ
# ============================
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from database import get_mentor_role


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


def specialist_panel_keyboard():

    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="📋 Все анкеты",
                    callback_data="sp_all_surveys"
                )
            ],
            [
                InlineKeyboardButton(
                    text="👨‍🎓 Студенты",
                    callback_data="sp_students"
                )
            ],
            [
                InlineKeyboardButton(
                    text="👨‍🏭 Наставники",
                    callback_data="sp_mentors"
                )
            ],
            [
                InlineKeyboardButton(
                    text="📊 Статистика",
                    callback_data="sp_statistics"
                )
            ],
            [
                InlineKeyboardButton(
                    text="📥 Экспорт Excel",
                    callback_data="sp_export_excel"
                )
            ]
        ]
    )
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
