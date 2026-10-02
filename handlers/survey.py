from utils.message_pages import send_pages
import html
from questions import survey_comments
from keyboards import back_keyboard
from aiogram import Router, F
from aiogram.types import (
    Message,
    CallbackQuery,
    InlineKeyboardMarkup,
    InlineKeyboardButton
)
from aiogram.fsm.context import FSMContext

from datetime import datetime
import asyncio
import json

from keyboards import (
    streams_keyboard,
    students_keyboard,
    enterprises_keyboard,
    marks_keyboard,
    main_menu_builder,
    start_survey_keyboard
)

from database import (
    get_mentor_id,
    save_survey,
    get_surveys_by_mentor,
    get_survey,
    get_student,
    get_enterprise,
    load_survey_questions,
)

from states import Survey
from questions import (
    OPEN_QUESTIONS,
    get_questionnaire_title,
    get_questions,
    questionnaire_key_for_enterprise,
    score_summary,
)

from utils.survey_manager import format_question
from lms_sync import sync_survey

router = Router()

def average_icon(avg):
    if avg is None: return "⚪"

    if avg >= 4.5:
        return "🟢"

    if avg >= 3.5:
        return "🟡"

    if avg >= 2.5:
        return "🟠"

    return "🔴"


def student_confirmation_text(student, enterprise, questionnaire_key):

    questionnaire_title = get_questionnaire_title(questionnaire_key)
    question_count = len(get_questions(questionnaire_key))

    return (
        "━━━━━━━━━━━━━━━━━━━━━━\n\n"
        "📝 <b>Новая анкета</b>\n\n"
        f"👨‍🎓 <b>Студент</b>\n{student[1]}\n\n"
        f"👥 <b>Поток</b>\n{student[5]} поток\n\n"
        f"🏭 <b>Предприятие</b>\n{enterprise}\n\n"
        f"📋 <b>Анкета</b>\n{questionnaire_title} · {question_count} вопросов\n\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n\n"
        "Проверьте правильность выбора."
    )

# =====================================================
# НОВАЯ АНКЕТА
# =====================================================

@router.message(F.text == "📝 Новая анкета")
async def new_survey(message: Message, state: FSMContext):

    await state.clear()
    await state.set_state(Survey.choosing_stream)

    await message.answer(
        "👥 Выберите поток:",
        reply_markup=streams_keyboard()
    )


# =====================================================
# ВЫБОР ПОТОКА
# =====================================================

@router.callback_query(
    Survey.choosing_stream,
    F.data.startswith("stream_")
)
async def choose_stream(callback: CallbackQuery, state: FSMContext):

    stream = int(callback.data.removeprefix("stream_"))

    await state.update_data(stream=stream)
    await state.set_state(Survey.choosing_student)

    await callback.message.edit_text(
        f"👥 <b>{stream} поток</b>\n\n"
        "👨‍🎓 Выберите студента:",
        parse_mode="HTML",
        reply_markup=students_keyboard(stream)
    )

    await callback.answer()


# =====================================================
# ВЫБОР ПРЕДПРИЯТИЯ
# =====================================================

@router.callback_query(
    Survey.choosing_enterprise,
    F.data.startswith("enterprise_")
)
async def choose_enterprise(
    callback: CallbackQuery,
    state: FSMContext
):

    enterprise_id = int(callback.data.removeprefix("enterprise_"))
    enterprise = get_enterprise(enterprise_id)
    data = await state.get_data()
    student = get_student(data["student_id"])

    if not student or not enterprise:
        await callback.answer("Данные не найдены.", show_alert=True)
        return

    questionnaire_key = questionnaire_key_for_enterprise(enterprise)
    if not questionnaire_key:
        await callback.answer(
            "Для этого предприятия новая анкета пока не настроена.",
            show_alert=True,
        )
        return
    await state.update_data(
        enterprise=enterprise,
        questionnaire_key=questionnaire_key,
    )
    await state.set_state(Survey.confirm_student)

    await callback.answer()

    await callback.message.edit_text(
        student_confirmation_text(student, enterprise, questionnaire_key),
        parse_mode="HTML",
        reply_markup=start_survey_keyboard()
    )


@router.callback_query(F.data == "back_enterprises")
async def back_to_enterprises(callback: CallbackQuery, state: FSMContext):

    data = await state.get_data()
    student = get_student(data.get("student_id"))

    if not student:
        await callback.answer("Студент не найден.", show_alert=True)
        return

    await state.set_state(Survey.choosing_enterprise)

    await callback.answer()

    await callback.message.edit_text(
        f"👨‍🎓 Студент: <b>{student[1]}</b>\n\n"
        f"👥 Поток: <b>{student[5]}</b>\n\n"
        "🏭 Выберите предприятие:",
        parse_mode="HTML",
        reply_markup=enterprises_keyboard()
    )

# =====================================================
# 📋 Мои анкеты (КНОПКИ)
# =====================================================

@router.message(F.text == "📋 Мои анкеты")
async def my_surveys(message: Message):

    mentor_id = get_mentor_id(message.from_user.id)
    surveys = get_surveys_by_mentor(mentor_id)

    if not surveys:
        await message.answer("📭 У вас пока нет заполненных анкет.",reply_markup=back_keyboard())
        return

    keyboard = []

    for s in surveys:
        survey_id = s[0]
        student_name = s[1]
        date = s[2]
        avg = s[3]

        keyboard.append([
            InlineKeyboardButton(
                text=f"{student_name} | ⭐ {avg if avg is not None else 'Не оценивалось'}",
                callback_data=f"survey_{survey_id}"
            )
        ])

    keyboard.append([InlineKeyboardButton(text="← Главное меню",callback_data="go_menu")])
    await message.answer(
        "📋 <b>Ваши анкеты:</b>",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard),
        parse_mode="HTML"
    )


# =====================================================
# ОТКРЫТИЕ АНКЕТЫ ПО КНОПКЕ
# =====================================================

@router.callback_query(F.data.startswith("survey_"))
async def open_survey(callback: CallbackQuery):

    survey_id = int(callback.data.split("_")[1])

    survey = get_survey(survey_id)

    if not survey or survey[1] != get_mentor_id(callback.from_user.id):
        await callback.message.answer("❌ Анкета не найдена.",reply_markup=back_keyboard())
        return

    answers = json.loads(survey[4])
    questions = load_survey_questions(survey[12], survey[13])

    text = (
        f"<b>📋 Анкета №{survey[0]}</b>\n\n"
        f"👨‍🎓 Студент: {survey[9]}\n"
        f"👥 Поток: {survey[11]}\n"
        f"🏭 Предприятие: {survey[10]}\n"
        f"📅 Дата: {survey[3]}\n"
        f"⭐ Средний балл: {survey[5] if survey[5] is not None else 'Не оценивалось'}\n"
        f"🔧 Hard skills: {survey[14] if survey[14] is not None else '-'}\n"
        f"🤝 Soft skills: {survey[15] if survey[15] is not None else '-'}\n"
        f"🎓 Профессиональная пригодность: {survey[16] if survey[16] is not None else '-'}\n\n"
        f"<b>Оценки:</b>\n"
    )

    for question, mark in zip(questions, answers):
        text += f"{question.get('text', '—')}: {mark if mark is not None else 'Не оценивалось'}\n"

    for title, value in survey_comments(questions, survey[6], survey[7], survey[8]):
        text += f"\n{html.escape(title)}\n{html.escape(value or '—')}\n"
    await send_pages(callback.message, text, back_keyboard())
    await callback.answer()


# =====================================================
# СТАТИСТИКА
# =====================================================

@router.message(F.text == "📊 Статистика")
async def my_statistics(message: Message):

    from database import get_mentor_statistics, is_specialist
    if is_specialist(message.from_user.id):
        from keyboards import statistics_keyboard
        await message.answer("📊 Статистика",reply_markup=statistics_keyboard())
        return

    stat = get_mentor_statistics(message.from_user.id)

    if stat is None:

        await message.answer(
            "❌ Вы не зарегистрированы."
        ,reply_markup=back_keyboard())
        return

    text = (
        "📊 <b>Моя статистика</b>\n\n"

        f"👨‍🏭 Наставник:\n"
        f"{stat['mentor']}\n\n"

        f"📝 Заполнено анкет: <b>{stat['count']}</b>\n"

        f"⭐ Средний балл студентов: <b>{stat['average'] if stat['average'] is not None else 'Не оценивалось'}</b>\n"
        f"🔧 Hard skills: <b>{stat['hard_average'] if stat['hard_average'] is not None else '-'}</b>\n"
        f"🤝 Soft skills: <b>{stat['soft_average'] if stat['soft_average'] is not None else '-'}</b>\n"
        f"🎓 Профессиональная пригодность: <b>{stat['suitability_average'] if stat['suitability_average'] is not None else '-'}</b>\n\n"
        f"CT Assembly: <b>{stat['ct_assembly_count']}</b> · CT Agro: <b>{stat['ct_agro_count']}</b>\n\n"
        f"📅 Последняя анкета:\n"
        f"{stat['last_date']}"
    )

    await message.answer(
        text,
        parse_mode="HTML"
    ,reply_markup=back_keyboard())

# =====================================================
# О ПРОГРАММЕ
# =====================================================

@router.message(F.text == "ℹ️ О программе")
async def about(message: Message):

    await message.answer(
        "🤖 Система анкетирования наставников\n"
        "Версия 2.1.3 · Анкеты CT Assembly / CT Agro и отзывы студентов"
    ,reply_markup=back_keyboard())


# =====================================================
# ВЫБОР СТУДЕНТА
# =====================================================

@router.callback_query(
    Survey.choosing_student,
    F.data.startswith("student_")
)
async def select_student(
    callback: CallbackQuery,
    state: FSMContext
):

    student_id = int(callback.data.split("_")[1])

    student = get_student(student_id)

    if not student:

        await callback.answer(
            "Студент не найден.",
            show_alert=True
        )
        return

    await state.update_data(
        student_id=student_id
    )

    await state.set_state(Survey.choosing_enterprise)

    await callback.message.edit_text(
        f"👨‍🎓 Студент: <b>{student[1]}</b>\n\n"
        f"👥 Поток: <b>{student[5]}</b>\n\n"
        "🏭 Выберите предприятие:",
        parse_mode="HTML",
        reply_markup=enterprises_keyboard()
    )

    await callback.answer()


# =====================================================
# НАЧАТЬ АНКЕТУ
# =====================================================

@router.callback_query(F.data == "start_survey")
async def start_survey(
    callback: CallbackQuery,
    state: FSMContext
):
    from handlers.assessment import begin
    await begin(callback, state, 'survey')


@router.callback_query(F.data == "back_students")
async def back_students(
    callback: CallbackQuery,
    state: FSMContext
):

    data = await state.get_data()
    stream = data.get("stream")

    if stream is None:
        await state.set_state(Survey.choosing_stream)
        await callback.message.edit_text(
            "👥 Выберите поток:",
            reply_markup=streams_keyboard()
        )
        await callback.answer()
        return

    await state.set_state(Survey.choosing_student)

    await callback.message.edit_text(
        f"👥 <b>{stream} поток</b>\n\n"
        "👨‍🎓 Выберите студента:",
        parse_mode="HTML",
        reply_markup=students_keyboard(stream)
    )

    await callback.answer()


@router.callback_query(F.data == "back_streams")
async def back_streams(callback: CallbackQuery, state: FSMContext):

    await state.set_state(Survey.choosing_stream)

    await callback.message.edit_text(
        "👥 Выберите поток:",
        reply_markup=streams_keyboard()
    )

    await callback.answer()

# =====================================================
# ОТВЕТЫ
# =====================================================

