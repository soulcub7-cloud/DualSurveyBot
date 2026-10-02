from utils.message_pages import send_pages
from keyboards import back_keyboard
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
        "Введите название учебного модуля.",
        reply_markup=back_keyboard("feedback_back_mentors", "← К наставникам"),
        parse_mode="HTML",
    )
    await callback.answer()


@router.message(MentorFeedback.entering_module)
async def enter_feedback_module(message: Message, state: FSMContext):
    module = (message.text or "").strip()
    if len(module) < 2:
        await message.answer("Введите название учебного модуля.")
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
    from handlers.assessment import begin
    await begin(callback, state, 'feedback')


@router.message(F.text == "📋 Мои отзывы")
async def my_mentor_feedback(message: Message):
    records = get_student_feedback(message.from_user.id)
    if not records:
        await message.answer("📭 Вы ещё не оставляли отзывов о наставниках.",reply_markup=back_keyboard())
        return
    text = "📋 <b>Мои отправленные отзывы</b>\n\n"
    for record in records[:20]:
        text += (
            f"• <b>{html.escape(record['mentor_name'])}</b>\n"
            f"  {html.escape(record['module'])} · {record['average']}/5 · {record['submitted_at']}\n\n"
        )
    await send_pages(message, text, back_keyboard())
