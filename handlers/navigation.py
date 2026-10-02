from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery
from database import get_student_by_telegram, is_specialist
from keyboards import main_menu_builder, student_menu_builder
router=Router()
@router.callback_query(F.data == 'go_menu')
async def go_menu(callback:CallbackQuery,state:FSMContext):
    await state.clear()
    await callback.answer()
    menu=student_menu_builder() if get_student_by_telegram(callback.from_user.id) and not is_specialist(callback.from_user.id) else main_menu_builder(callback.from_user.id)
    await callback.message.answer('Главное меню',reply_markup=menu)
