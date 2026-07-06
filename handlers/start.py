from aiogram import Router
from aiogram.filters import CommandStart
from aiogram.types import Message
from aiogram.fsm.context import FSMContext

from keyboards import main_menu_builder
from states import Registration
from database import mentor_exists, get_mentor_name

router = Router()


@router.message(CommandStart())
async def start(message: Message, state: FSMContext):

    telegram_id = message.from_user.id

    if not mentor_exists(telegram_id):

        await message.answer(
            "👋 Добро пожаловать!\n\n"
            "Вы впервые используете систему.\n\n"
            "Введите Ваше ФИО полностью."
        )

        await state.set_state(Registration.waiting_for_fio)

        return

    fio = get_mentor_name(telegram_id)

    await message.answer(
        f"Здравствуйте, <b>{fio}</b>!\n\n"
        "Выберите действие:",
        parse_mode="HTML",
        reply_markup=main_menu_builder(message.from_user.id)
    )