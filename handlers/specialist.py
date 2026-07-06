from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, FSInputFile

from database import get_survey_by_id
from database import get_statistics
from utils.excel_one_survey import export_one_survey
from utils.pdf_export import export_one_pdf
from database import (
    get_connection,
    get_all_surveys_for_excel
)

from utils.excel_export import export_surveys_to_excel

from utils.excel_export import export_surveys_to_excel
from keyboards import (
    specialist_panel_keyboard,
    surveys_keyboard,
    survey_view_keyboard,
    confirm_delete_keyboard,
    main_menu_builder
)

router = Router()


# =====================================================
# КАБИНЕТ СПЕЦИАЛИСТА
# =====================================================

@router.message(F.text == "👨‍💼 Кабинет специалиста")
async def show_specialist_menu(message: Message):

    await message.answer(
        "👨‍💼 <b>Кабинет специалиста</b>\n\n"
        "Выберите раздел:",
        parse_mode="HTML",
        reply_markup=specialist_panel_keyboard()
    )


# =====================================================
# ВСЕ АНКЕТЫ
# =====================================================

@router.callback_query(F.data == "sp_all_surveys")
async def callback_all_surveys(callback: CallbackQuery):

    from database import get_surveys

    surveys = get_surveys()

    await callback.answer()

    if not surveys:

        await callback.message.edit_text(
            "📭 Пока нет заполненных анкет."
        )
        return

    await callback.message.edit_text(
        "📋 <b>Все анкеты</b>\n\n"
        "Выберите анкету:",
        parse_mode="HTML",
        reply_markup=surveys_keyboard(surveys)
    )


# =====================================================
# СТУДЕНТЫ
# =====================================================

@router.callback_query(F.data == "sp_students")
async def callback_students(callback: CallbackQuery):

    from database import get_students_statistics

    students = get_students_statistics()

    await callback.answer()

    if not students:

        await callback.message.edit_text(
            "Студентов пока нет."
        )
        return

    text = "👨‍🎓 <b>Студенты</b>\n\n"

    for number, student in enumerate(students, start=1):

        average = student[3] if student[3] else "-"

        text += (
            f"{number}. <b>{student[1]}</b>\n"
            f"📝 Анкет: {student[2]}\n"
            f"⭐ Средний балл: {average}\n\n"
        )

    await callback.message.edit_text(
        text,
        parse_mode="HTML"
    )


# =====================================================
# НАСТАВНИКИ
# =====================================================

@router.callback_query(F.data == "sp_mentors")
async def callback_mentors(callback: CallbackQuery):

    from database import get_mentors_statistics

    mentors = get_mentors_statistics()

    await callback.answer()

    if not mentors:

        await callback.message.edit_text(
            "👨‍🏭 Наставники отсутствуют."
        )
        return

    text = "👨‍🏭 <b>Наставники</b>\n\n"

    for number, mentor in enumerate(mentors, start=1):

        average = mentor[3] if mentor[3] else "-"

        text += (
            f"{number}. <b>{mentor[1]}</b>\n"
            f"📝 Заполнено анкет: {mentor[2]}\n"
            f"⭐ Средний балл студентов: {average}\n\n"
        )

    await callback.message.edit_text(
        text,
        parse_mode="HTML"
    )


# =====================================================
# СТАТИСТИКА
# =====================================================

@router.callback_query(F.data == "sp_statistics")
async def callback_statistics(callback: CallbackQuery):

    (
        students,
        mentors,
        surveys,
        average,
        excellent,
        good,
        satisfactory,
        poor
    ) = get_statistics()

    text = (
        "📊 <b>Общая статистика</b>\n\n"

        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"

        f"👨‍🎓 <b>Студентов:</b> {students}\n"
        f"👨‍🏭 <b>Наставников:</b> {mentors}\n"
        f"📋 <b>Заполнено анкет:</b> {surveys}\n"
        f"⭐ <b>Средний балл:</b> {average}\n\n"

        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"

        f"🟢 Отлично (4.5–5.0) — <b>{excellent}</b>\n"
        f"🟡 Хорошо (3.5–4.49) — <b>{good}</b>\n"
        f"🟠 Удовлетворительно (2.5–3.49) — <b>{satisfactory}</b>\n"
        f"🔴 Требуют внимания (менее 2.5) — <b>{poor}</b>"
    )

    await callback.answer()

    await callback.message.edit_text(
        text,
        parse_mode="HTML"
    )


# =====================================================
# ЭКСПОРТ
# =====================================================

@router.callback_query(F.data == "sp_export_excel")
async def callback_export(callback):

    await callback.answer("✅ Экспорт завершён.")

    data = get_all_surveys_for_excel()

    if not data:

        await callback.message.edit_text(
            "❌ В базе данных пока нет анкет."
        )
        return

    filename = export_surveys_to_excel(data)

    document = FSInputFile(filename)

    await callback.message.answer_document(
        document=document,
        caption="📊 Отчет успешно сформирован."
    )
@router.message(F.text == "🔙 Главное меню")
async def back_to_menu(message: Message):

    await message.answer(
        "Главное меню",
        reply_markup=main_menu_builder(message.from_user.id)
    )


# =====================================================
# ПРОСМОТР АНКЕТЫ
# =====================================================

@router.callback_query(F.data.startswith("sp_survey_"))
async def callback_open_survey(callback: CallbackQuery):
    
    survey_id = int(callback.data.split("_")[2])

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            students.fio,
            mentors.fio,
            surveys.survey_date,
            surveys.average,
            surveys.best,
            surveys.improve,
            surveys.recommendation
        FROM surveys
        JOIN students
            ON students.id = surveys.student_id
        JOIN mentors
            ON mentors.id = surveys.mentor_id
        WHERE surveys.id = ?
    """, (survey_id,))

    survey = cursor.fetchone()

    conn.close()

    await callback.answer()

    if not survey:

        await callback.message.edit_text(
            "❌ Анкета не найдена."
        )
        return

    text = (
        f"<b>Анкета №{survey_id}</b>\n\n"
        f"👨‍🎓 <b>Студент:</b> {survey[0]}\n"
        f"👨‍🏭 <b>Наставник:</b> {survey[1]}\n"
        f"📅 <b>Дата:</b> {survey[2]}\n"
        f"⭐ <b>Средний балл:</b> {survey[3]}\n\n"
        f"✅ <b>Лучше всего:</b>\n{survey[4]}\n\n"
        f"📈 <b>Необходимо улучшить:</b>\n{survey[5]}\n\n"
        f"💬 <b>Рекомендации:</b>\n{survey[6]}"
    )

    await callback.message.edit_text(
    text,
    parse_mode="HTML",
    reply_markup=survey_view_keyboard(survey_id)
)

# =====================================================
# ЗАПРОС НА УДАЛЕНИЕ
# =====================================================

@router.callback_query(F.data.startswith("sp_delete_"))
async def callback_delete(callback: CallbackQuery):

    survey_id = int(callback.data.split("_")[2])

    await callback.answer()

    await callback.message.edit_text(
        "⚠️ Вы действительно хотите удалить эту анкету?\n\n"
        "Это действие нельзя отменить.",
        reply_markup=confirm_delete_keyboard(survey_id)
    )

# =====================================================
# ПОДТВЕРЖДЕНИЕ УДАЛЕНИЯ
# =====================================================

@router.callback_query(F.data.startswith("sp_confirm_delete_"))
async def callback_confirm_delete(callback: CallbackQuery):

    survey_id = int(callback.data.split("_")[3])

    from database import delete_survey, get_surveys

    # Удаляем анкету
    delete_survey(survey_id)

    await callback.answer("Анкета удалена")

    # Получаем обновленный список
    surveys = get_surveys()

    if surveys:

        await callback.message.edit_text(
            "📋 <b>Все анкеты</b>\n\nВыберите анкету:",
            parse_mode="HTML",
            reply_markup=surveys_keyboard(surveys)
        )

    else:

        await callback.message.edit_text(
            "📭 Анкет больше нет."
        )
# =====================================================
# НАЗАД В КАБИНЕТ СПЕЦИАЛИСТА
# =====================================================

@router.callback_query(F.data == "back_specialist")
async def callback_back_specialist(callback: CallbackQuery):

    await callback.answer()

    await callback.message.edit_text(
        "👨‍💼 <b>Кабинет специалиста</b>\n\n"
        "Выберите раздел:",
        parse_mode="HTML",
        reply_markup=specialist_panel_keyboard()
    )

# =====================================================
# EXCEL ОДНОЙ АНКЕТЫ
# =====================================================

@router.callback_query(F.data.startswith("excel_"))
async def callback_excel(callback: CallbackQuery):

    survey_id = int(callback.data.split("_")[1])

    survey = get_survey_by_id(survey_id)

    await callback.answer()

    if not survey:

        await callback.message.answer(
            "❌ Анкета не найдена."
        )
        return

    filename = export_one_survey(survey)

    document = FSInputFile(filename)

    await callback.message.answer_document(
        document=document,
        caption=f"📊 Анкета №{survey_id}"
    )

# =====================================================
# PDF ОДНОЙ АНКЕТЫ
# =====================================================

@router.callback_query(F.data.startswith("pdf_"))
async def callback_pdf(callback: CallbackQuery):

    survey_id = int(callback.data.split("_")[1])

    survey = get_survey_by_id(survey_id)

    await callback.answer()

    if not survey:

        await callback.message.answer(
            "❌ Анкета не найдена."
        )
        return

    filename = export_one_pdf(survey)

    document = FSInputFile(filename)

    await callback.message.answer_document(
        document=document,
        caption=f"📄 Анкета №{survey_id}"
    )