from aiogram import Router, F
from aiogram.types import (
    Message,
    CallbackQuery,
    InlineKeyboardMarkup,
    InlineKeyboardButton
)
from aiogram.fsm.context import FSMContext

from datetime import datetime
import json

from keyboards import (
    students_keyboard,
    enterprise_students_keyboard,
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
    get_student
)

from states import Survey
from questions import QUESTIONS

from utils.survey_manager import (
    get_question,
    format_question
)

router = Router()

def average_icon(avg):

    if avg >= 4.5:
        return "🟢"

    if avg >= 3.5:
        return "🟡"

    if avg >= 2.5:
        return "🟠"

    return "🔴"

# =====================================================
# НОВАЯ АНКЕТА
# =====================================================

@router.message(F.text == "📝 Новая анкета")
async def new_survey(message: Message, state: FSMContext):

    await state.clear()

    await message.answer(
        "🏭 Выберите предприятие:",
        reply_markup=enterprises_keyboard()
    )


# =====================================================
# ВЫБОР ПРЕДПРИЯТИЯ
# =====================================================

@router.callback_query(F.data.startswith("enterprise_"))
async def choose_enterprise(
    callback: CallbackQuery,
    state: FSMContext
):

    enterprise = callback.data.replace("enterprise_", "")

    await state.set_state(Survey.choosing_student)

    await callback.answer()

    await callback.message.edit_text(
        f"🏭 Предприятие:\n<b>{enterprise}</b>\n\n"
        "Выберите студента:",
        parse_mode="HTML",
        reply_markup=enterprise_students_keyboard(enterprise)
    )
@router.callback_query(F.data == "choose_enterprise")
async def back_to_enterprises(callback: CallbackQuery, state: FSMContext):

    await state.clear()

    await callback.answer()

    await callback.message.edit_text(
        "🏭 Выберите предприятие:",
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
        await message.answer("📭 У вас пока нет заполненных анкет.")
        return

    keyboard = []

    for s in surveys:
        survey_id = s[0]
        student_name = s[1]
        date = s[2]
        avg = s[3]

        keyboard.append([
            InlineKeyboardButton(
                text=f"{student_name} | ⭐ {avg}",
                callback_data=f"survey_{survey_id}"
            )
        ])

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

    if not survey:
        await callback.message.answer("❌ Анкета не найдена.")
        return

    answers = json.loads(survey[4])

    text = (
        f"<b>📋 Анкета №{survey[0]}</b>\n\n"
        f"👨‍🎓 Студент: {survey[9]}\n"
        f"📅 Дата: {survey[3]}\n"
        f"⭐ Средний балл: {survey[5]}\n\n"
        f"<b>Оценки:</b>\n"
    )

    for i, mark in enumerate(answers, 1):
        text += f"Вопрос {i}: {mark}\n"

    text += (
        f"\n<b>Лучшее:</b>\n{survey[6]}\n\n"
        f"<b>Что улучшить:</b>\n{survey[7]}\n\n"
        f"<b>Рекомендации:</b>\n{survey[8]}"
    )

    await callback.message.answer(text, parse_mode="HTML")
    await callback.answer()


# =====================================================
# СТАТИСТИКА
# =====================================================

@router.message(F.text == "📊 Статистика")
async def my_statistics(message: Message):

    from database import get_mentor_statistics

    stat = get_mentor_statistics(message.from_user.id)

    if stat is None:

        await message.answer(
            "❌ Вы не зарегистрированы."
        )
        return

    text = (
        "📊 <b>Моя статистика</b>\n\n"

        f"👨‍🏭 Наставник:\n"
        f"{stat['mentor']}\n\n"

        f"📝 Заполнено анкет: <b>{stat['count']}</b>\n"

        f"⭐ Средний балл студентов: <b>{stat['average']}</b>\n"

        f"📅 Последняя анкета:\n"
        f"{stat['last_date']}"
    )

    await message.answer(
        text,
        parse_mode="HTML"
    )

# =====================================================
# О ПРОГРАММЕ
# =====================================================

@router.message(F.text == "ℹ️ О программе")
async def about(message: Message):

    await message.answer(
        "🤖 Система анкетирования наставников\nВерсия 1.0"
    )


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

    await state.set_state(Survey.confirm_student)

    text = (
        "━━━━━━━━━━━━━━━━━━━━━━\n\n"
        "📝 <b>Новая анкета</b>\n\n"

        f"👨‍🎓 <b>Студент</b>\n"
        f"{student[1]}\n\n"

        f"🏭 <b>Предприятие</b>\n"
        f"{student[4]}\n\n"

        f"📚 <b>Курс</b>\n"
        f"{student[3]}\n\n"

        "━━━━━━━━━━━━━━━━━━━━━━\n\n"

        "Проверьте правильность выбранного студента."
    )

    await callback.message.edit_text(
        text,
        parse_mode="HTML",
        reply_markup=start_survey_keyboard()
    )

    await callback.answer()


# =====================================================
# НАЧАТЬ АНКЕТУ
# =====================================================

@router.callback_query(
    Survey.confirm_student,
    F.data == "start_survey"
)
async def start_survey(
    callback: CallbackQuery,
    state: FSMContext
):

    await state.update_data(
        question=0,
        answers=[]
    )

    await state.set_state(Survey.answering)

    await callback.message.edit_text(
        format_question(0),
        parse_mode="HTML",
        reply_markup=marks_keyboard()
    )

    await callback.answer()


    # =====================================================
# ВЫБРАТЬ ДРУГОГО СТУДЕНТА
# =====================================================

@router.callback_query(
    Survey.confirm_student,
    F.data == "back_students"
)
async def back_students(
    callback: CallbackQuery,
    state: FSMContext
):

    data = await state.get_data()

    student = get_student(data["student_id"])

    enterprise = student[4]

    await state.set_state(Survey.choosing_student)

    await callback.message.edit_text(
        f"🏭 Предприятие\n<b>{enterprise}</b>\n\n"
        "Выберите студента:",
        parse_mode="HTML",
        reply_markup=enterprise_students_keyboard(enterprise)
    )

    await callback.answer()

# =====================================================
# ОТВЕТЫ
# =====================================================

@router.callback_query(Survey.answering, F.data.startswith("mark_"))
async def next_question(callback: CallbackQuery, state: FSMContext):

    mark = int(callback.data.split("_")[1])
    data = await state.get_data()

    answers = data["answers"]
    answers.append(mark)

    question = data["question"] + 1

    await state.update_data(
        answers=answers,
        question=question
    )

    if question >= len(QUESTIONS):

        await callback.message.edit_text("✍️ Что студент сделал лучше всего?")
        await state.set_state(Survey.best)
        await callback.answer()
        return

    await callback.message.edit_text(
    format_question(question),
    reply_markup=marks_keyboard(),
    parse_mode="HTML"
)

    await callback.answer()


# =====================================================
# ЛУЧШЕЕ / УЛУЧШИТЬ / РЕКОМЕНДАЦИИ
# =====================================================

@router.message(Survey.best)
async def best(message: Message, state: FSMContext):
    await state.update_data(best=message.text)
    await message.answer("✍️ Что нужно улучшить?")
    await state.set_state(Survey.improve)


@router.message(Survey.improve)
async def improve(message: Message, state: FSMContext):
    await state.update_data(improve=message.text)
    await message.answer("✍️ Рекомендации студенту:")
    await state.set_state(Survey.recommendation)


@router.message(Survey.recommendation)
async def finish(message: Message, state: FSMContext):

    await state.update_data(
        recommendation=message.text
    )

    data = await state.get_data()

    answers = data["answers"]
    average = round(sum(answers) / len(answers), 2)

    mentor_id = get_mentor_id(message.from_user.id)

    save_survey(
        mentor_id=mentor_id,
        student_id=data["student_id"],
        answers=answers,
        average=average,
        best=data["best"],
        improve=data["improve"],
        recommendation=data["recommendation"],
        survey_date=datetime.now().strftime("%d.%m.%Y %H:%M")
    )

    student = get_student(data["student_id"])

    icon = average_icon(average)

    text = (
        "━━━━━━━━━━━━━━━━━━━━━━\n\n"

        "✅ <b>Анкета успешно сохранена</b>\n\n"

        f"👨‍🎓 <b>Студент</b>\n"
        f"{student[1]}\n\n"

        f"🏭 <b>Предприятие</b>\n"
        f"{student[4]}\n\n"

        f"{icon} <b>Средний балл</b>\n"
        f"{average:.2f}\n\n"

        f"📅 <b>Дата</b>\n"
        f"{datetime.now().strftime('%d.%m.%Y %H:%M')}\n\n"

        "Спасибо за участие в оценке\n"
        "практической подготовки!"

        "\n\n━━━━━━━━━━━━━━━━━━━━━━"
    )

    await message.answer(
        text,
        parse_mode="HTML",
        reply_markup=main_menu_builder(message.from_user.id)
    )

    await state.clear()