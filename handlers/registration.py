from datetime import datetime

from aiogram import Router
from aiogram.types import Message
from aiogram.fsm.context import FSMContext

from states import Registration
from database import add_mentor
from keyboards import main_menu_builder

router = Router()


@router.message(Registration.waiting_for_fio)
async def save_name(message: Message, state: FSMContext):

    fio = message.text.strip()

    add_mentor(
        telegram_id=message.from_user.id,
        fio=fio,
        date=datetime.now().strftime("%d.%m.%Y %H:%M")
    )

    await state.clear()

    await message.answer(
        f"✅ Регистрация завершена!\n\n"
        f"Здравствуйте, <b>{fio}</b>!",
        parse_mode="HTML",
        reply_markup=main_menu_builder(message.from_user.id)
    )