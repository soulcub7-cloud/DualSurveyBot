from datetime import datetime

from aiogram import F, Router
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext

from states import Registration
from database import add_mentor, get_student, register_student_telegram
from keyboards import (
    main_menu_builder,
    registration_streams_keyboard,
    registration_students_keyboard,
    student_menu_builder,
)

router = Router()


@router.callback_query(Registration.choosing_role, F.data == "register_role_mentor")
async def choose_mentor_role(callback: CallbackQuery, state: FSMContext):
    await state.set_state(Registration.waiting_for_fio)
    await callback.message.edit_text(
        "👨‍🏭 <b>Регистрация наставника</b>\n\nВведите Ваше ФИО полностью.",
        parse_mode="HTML",
    )
    await callback.answer()


@router.callback_query(Registration.choosing_role, F.data == "register_role_student")
async def choose_student_role(callback: CallbackQuery, state: FSMContext):
    await state.set_state(Registration.choosing_student_stream)
    await callback.message.edit_text(
        "👨‍🎓 <b>Регистрация студента</b>\n\nВыберите свой поток:",
        parse_mode="HTML",
        reply_markup=registration_streams_keyboard(),
    )
    await callback.answer()


@router.callback_query(
    Registration.choosing_student_stream,
    F.data.startswith("reg_stream_"),
)
async def choose_student_stream(callback: CallbackQuery, state: FSMContext):
    stream = int(callback.data.removeprefix("reg_stream_"))
    await state.update_data(registration_stream=stream)
    await state.set_state(Registration.choosing_student)
    await callback.message.edit_text(
        f"👥 <b>{stream} поток</b>\n\nВыберите свои ФИО:",
        parse_mode="HTML",
        reply_markup=registration_students_keyboard(stream),
    )
    await callback.answer()


@router.callback_query(Registration.choosing_student, F.data == "reg_back_streams")
async def registration_back_streams(callback: CallbackQuery, state: FSMContext):
    await state.set_state(Registration.choosing_student_stream)
    await callback.message.edit_text(
        "👨‍🎓 <b>Регистрация студента</b>\n\nВыберите свой поток:",
        parse_mode="HTML",
        reply_markup=registration_streams_keyboard(),
    )
    await callback.answer()


@router.callback_query(
    Registration.choosing_student,
    F.data.startswith("reg_student_"),
)
async def register_student(callback: CallbackQuery, state: FSMContext):
    student_id = int(callback.data.removeprefix("reg_student_"))
    student = get_student(student_id)
    if not student:
        await callback.answer("Студент не найден.", show_alert=True)
        return
    try:
        fio = register_student_telegram(
            student_id,
            callback.from_user.id,
            datetime.now().strftime("%d.%m.%Y %H:%M"),
        )
    except ValueError as exc:
        await callback.answer(str(exc), show_alert=True)
        return
    await state.clear()
    await callback.message.edit_text(
        f"✅ Регистрация завершена!\n\nЗдравствуйте, <b>{fio}</b>!\n\n"
        "Ваш отзыв будет анонимным для наставника. ФИО автора доступно только администратору.",
        parse_mode="HTML",
    )
    await callback.message.answer("Выберите действие:", reply_markup=student_menu_builder())
    await callback.answer()


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
