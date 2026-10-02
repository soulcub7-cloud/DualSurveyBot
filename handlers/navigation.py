"""Global navigation works from forms, reports and document messages."""
from aiogram import Router, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from database import get_student_by_telegram, is_specialist, mentor_exists
from keyboards import (main_menu_builder, student_menu_builder,
                       registration_role_keyboard, specialist_panel_keyboard)
from states import Registration

router = Router()
MENU_LABELS = {'Главное меню', '🔙 Главное меню', '← Главное меню',
               '⬅ Главное меню', '⬅️ Главное меню', '🏠 Главное меню'}

async def show_main_menu(message: Message, telegram_id: int, state: FSMContext):
    await state.clear()
    if is_specialist(telegram_id):
        menu = main_menu_builder(telegram_id)
    elif get_student_by_telegram(telegram_id):
        menu = student_menu_builder()
    elif mentor_exists(telegram_id):
        menu = main_menu_builder(telegram_id)
    else:
        await state.set_state(Registration.choosing_role)
        await message.answer('Выберите роль для регистрации:', reply_markup=registration_role_keyboard())
        return
    await message.answer('🏠 Главное меню открыто. Выберите действие на клавиатуре под строкой ввода:', reply_markup=menu)

@router.callback_query(F.data == 'go_menu')
async def go_menu(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    await show_main_menu(callback.message, callback.from_user.id, state)

@router.message(F.text.in_(MENU_LABELS))
@router.message(Command('menu'))
async def menu_message(message: Message, state: FSMContext):
    await show_main_menu(message, message.from_user.id, state)

@router.callback_query(F.data == 'back_specialist')
async def back_specialist(callback: CallbackQuery, state: FSMContext):
    if not is_specialist(callback.from_user.id):
        await callback.answer('Кабинет доступен только специалисту.', show_alert=True)
        return
    await callback.answer()
    await state.clear()
    # Documents have captions, not editable message text. A fresh message also
    # avoids Telegram's "message is not modified" error on repeated presses.
    await callback.message.answer('👨‍💼 Кабинет специалиста\n\nВыберите раздел:',
        reply_markup=specialist_panel_keyboard(callback.from_user.id))
