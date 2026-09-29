import asyncio
import html
from datetime import datetime, timedelta, timezone

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from database import (
    get_directory_mentor,
    get_directory_mentors,
    get_student_by_telegram,
    get_student_feedback,
    save_mentor_feedback,
)
from keyboards import (
    marks_keyboard,
    mentor_directory_keyboard,
    start_mentor_feedback_keyboard,
    student_menu_builder,
)
from lms_sync import sync_mentor_feedback, sync_mentor_reference
from mentor_feedback_questions import (
    MENTOR_FEEDBACK_OPEN_QUESTIONS,
    MENTOR_FEEDBACK_QUESTIONS,
    format_mentor_feedback_question,
)
from states import MentorFeedback


router = Router()
ALMATY_TIMEZONE = timezone(timedelta(hours=5))


async def show_mentor_selection(message: Message, state: FSMContext, edit=False):
    try:
        await sync_mentor_reference()
    except Exception as exc:
        print(f"Не удалось обновить список наставников из LMS: {exc}")
    mentors = get_directory_mentors()
    if not mentors:
        text = (
            "Список наставников пока недоступен. Попробуйте ещё раз через несколько минут "
            "или сообщите администратору."
        )
        if edit:
            await message.edit_text(text)
        else:
            await message.answer(text)
        return False
    await state.set_state(MentorFeedback.choosing_mentor)
    text = (
        "👨‍🏭 <b>Выберите наставника</b>\n\n"
        "Список загружен из LMS. Некоторые ФИО могут быть сокращены — выберите нужного сотрудника."
    )
    if edit:
        await message.edit_text(
            text,
            parse_mode="HTML",
            reply_markup=mentor_directory_keyboard(mentors),
        )
    else:
        await message.answer(
            text,
            parse_mode="HTML",
            reply_markup=mentor_directory_keyboard(mentors),
        )
    return True


@router.message(F.text == "🗣 Оценить наставника")
async def new_mentor_feedback(message: Message, state: FSMContext):
    student = get_student_by_telegram(message.from_user.id)
    if not student:
        await message.answer("Сначала зарегистрируйтесь как студент с помощью команды /start.")
        return
    await state.clear()
    await show_mentor_selection(message, state)


@router.callback_query(
    MentorFeedback.choosing_mentor,
    F.data.startswith("feedback_mentor_"),
)
async def choose_feedback_mentor(callback: CallbackQuery, state: FSMContext):
    mentor_id = int(callback.data.removeprefix("feedback_mentor_"))
    mentor = get_directory_mentor(mentor_id)
    if not mentor:
        await callback.answer("Наставник не найден. Обновите список.", show_alert=True)
        return
    await state.update_data(mentor=mentor)
    await state.set_state(MentorFeedback.entering_module)
    await callback.message.edit_text(
        f"👨‍🏭 Наставник: <b>{html.escape(mentor['full_name'])}</b>\n"
        f"🏭 Предприятие: <b>{html.escape(mentor.get('enterprise') or 'Не указано')}</b>\n\n"
        "Введите название учебного модуля, вида работ или участка, по которому проходила практика.",
        parse_mode="HTML",
    )
    await callback.answer()


@router.message(MentorFeedback.entering_module)
async def enter_feedback_module(message: Message, state: FSMContext):
    module = (message.text or "").strip()
    if len(module) < 2:
        await message.answer("Введите название модуля или вида работ.")
        return
    await state.update_data(module=module)
    data = await state.get_data()
    mentor = data["mentor"]
    student = get_student_by_telegram(message.from_user.id)
    await state.set_state(MentorFeedback.confirming)
    await message.answer(
        "🗣 <b>Отзыв студента о наставнике</b>\n\n"
        f"Наставник: <b>{html.escape(mentor['full_name'])}</b>\n"
        f"Предприятие: <b>{html.escape(mentor.get('enterprise') or 'Не указано')}</b>\n"
        f"Модуль: <b>{html.escape(module)}</b>\n"
        f"Специальность: <b>{html.escape(student[2] or 'Не указана')}</b>\n\n"
        f"В анкете {len(MENTOR_FEEDBACK_QUESTIONS)} оценок и "
        f"{len(MENTOR_FEEDBACK_OPEN_QUESTIONS)} развернутых ответов.\n\n"
        "🔒 Наставник не увидит ваше имя и отдельные ответы. "
        "ФИО автора доступны только администратору.",
        parse_mode="HTML",
        reply_markup=start_mentor_feedback_keyboard(),
    )


@router.callback_query(F.data == "feedback_back_mentors")
async def feedback_back_mentors(callback: CallbackQuery, state: FSMContext):
    await show_mentor_selection(callback.message, state, edit=True)
    await callback.answer()


@router.callback_query(MentorFeedback.confirming, F.data == "feedback_start")
async def start_feedback_questions(callback: CallbackQuery, state: FSMContext):
    await state.update_data(question=0, ratings=[], open_answers={})
    await state.set_state(MentorFeedback.answering)
    await callback.message.edit_text(
        format_mentor_feedback_question(0),
        parse_mode="HTML",
        reply_markup=marks_keyboard(),
    )
    await callback.answer()


@router.callback_query(MentorFeedback.answering, F.data.startswith("mark_"))
async def next_feedback_question(callback: CallbackQuery, state: FSMContext):
    score = int(callback.data.removeprefix("mark_"))
    data = await state.get_data()
    ratings = list(data.get("ratings", []))
    ratings.append(score)
    question_index = int(data.get("question", 0)) + 1
    await state.update_data(ratings=ratings, question=question_index)
    if question_index >= len(MENTOR_FEEDBACK_QUESTIONS):
        key, question = MENTOR_FEEDBACK_OPEN_QUESTIONS[0]
        await state.update_data(open_index=0, current_open_key=key)
        await state.set_state(MentorFeedback.open_answer)
        await callback.message.edit_text(f"✍️ <b>Развернутый ответ 1 из {len(MENTOR_FEEDBACK_OPEN_QUESTIONS)}</b>\n\n{question}", parse_mode="HTML")
        await callback.answer()
        return
    await callback.message.edit_text(
        format_mentor_feedback_question(question_index),
        parse_mode="HTML",
        reply_markup=marks_keyboard(),
    )
    await callback.answer()


@router.message(MentorFeedback.open_answer)
async def save_feedback_open_answer(message: Message, state: FSMContext):
    answer = (message.text or "").strip()
    if not answer:
        await message.answer("Ответьте текстом. Если добавить нечего, напишите «Нет».")
        return
    data = await state.get_data()
    open_index = int(data.get("open_index", 0))
    key, _ = MENTOR_FEEDBACK_OPEN_QUESTIONS[open_index]
    open_answers = dict(data.get("open_answers", {}))
    open_answers[key] = answer
    next_index = open_index + 1
    if next_index < len(MENTOR_FEEDBACK_OPEN_QUESTIONS):
        next_key, next_question = MENTOR_FEEDBACK_OPEN_QUESTIONS[next_index]
        await state.update_data(
            open_answers=open_answers,
            open_index=next_index,
            current_open_key=next_key,
        )
        await message.answer(
            f"✍️ <b>Развернутый ответ {next_index + 1} из {len(MENTOR_FEEDBACK_OPEN_QUESTIONS)}</b>\n\n"
            f"{next_question}",
            parse_mode="HTML",
        )
        return

    await state.update_data(open_answers=open_answers)
    data = await state.get_data()
    student = get_student_by_telegram(message.from_user.id)
    ratings = [int(score) for score in data["ratings"]]
    average = round(sum(ratings) / len(ratings), 2)
    submitted_at = datetime.now(ALMATY_TIMEZONE).strftime("%d.%m.%Y %H:%M")
    feedback_id = save_mentor_feedback(
        student_id=student[0],
        mentor=data["mentor"],
        module=data["module"],
        submitted_at=submitted_at,
        ratings=ratings,
        questions=MENTOR_FEEDBACK_QUESTIONS,
        average=average,
        open_answers=open_answers,
    )
    asyncio.create_task(sync_mentor_feedback(feedback_id))
    await state.clear()
    await message.answer(
        "✅ <b>Спасибо! Отзыв сохранён.</b>\n\n"
        f"Наставник: {html.escape(data['mentor']['full_name'])}\n"
        f"Средняя оценка: <b>{average}/5</b>\n\n"
        "Наставник не увидит ваше имя. Полная запись доступна только администратору.",
        parse_mode="HTML",
        reply_markup=student_menu_builder(),
    )


@router.message(F.text == "📋 Мои отзывы")
async def my_mentor_feedback(message: Message):
    records = get_student_feedback(message.from_user.id)
    if not records:
        await message.answer("📭 Вы ещё не оставляли отзывов о наставниках.")
        return
    text = "📋 <b>Мои отправленные отзывы</b>\n\n"
    for record in records[:20]:
        text += (
            f"• <b>{html.escape(record['mentor_name'])}</b>\n"
            f"  {html.escape(record['module'])} · {record['average']}/5 · {record['submitted_at']}\n\n"
        )
    await message.answer(text, parse_mode="HTML")
