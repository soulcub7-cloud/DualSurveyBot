from aiogram import Router
from aiogram.filters import CommandStart
from aiogram.types import Message
from aiogram.fsm.context import FSMContext

from keyboards import main_menu_builder, registration_role_keyboard, student_menu_builder
from states import Registration
from database import (
    get_mentor_name,
    get_student_by_telegram,
    mentor_exists,
    student_exists,
)

router = Router()


@router.message(CommandStart())
async def start(message: Message, state: FSMContext):

    telegram_id = message.from_user.id

    if student_exists(telegram_id):
        student = get_student_by_telegram(telegram_id)
        await state.clear()
        await message.answer(
            f"Здравствуйте, <b>{student[1]}</b>!\n\n"
            "Ваши ответы о наставнике будут анонимны для наставника. "
            "ФИО автора доступно только администратору.",
            parse_mode="HTML",
            reply_markup=student_menu_builder(),
        )
        return

    if not mentor_exists(telegram_id):

        await message.answer(
            "👋 Добро пожаловать!\n\n"
            "Вы впервые используете систему.\n\n"
            "Выберите свою роль:",
            reply_markup=registration_role_keyboard(),
        )

        await state.set_state(Registration.choosing_role)

        return

    fio = get_mentor_name(telegram_id)

    await message.answer(
        f"Здравствуйте, <b>{fio}</b>!\n\n"
        "Выберите действие:",
        parse_mode="HTML",
        reply_markup=main_menu_builder(message.from_user.id)
    )
