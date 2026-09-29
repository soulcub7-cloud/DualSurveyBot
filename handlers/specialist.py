import html

from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, FSInputFile
from config import ADMIN_ID, SPECIALIST_ID
from questions import OPEN_QUESTIONS
from database import get_survey_by_id
from database import get_extended_statistics, get_statistics
from utils.excel_one_survey import export_one_survey
from utils.pdf_export import export_one_pdf
from database import (
    get_all_mentor_feedback,
    get_connection,
    get_all_surveys_for_excel,
    get_mentor_feedback,
    get_mentor_feedback_statistics,
)

from utils.excel_export import export_surveys_to_excel
from utils.feedback_excel import export_mentor_feedback_excel
from utils.feedback_pdf import export_mentor_feedback_pdf

from keyboards import (
    specialist_panel_keyboard,
    surveys_keyboard,
    survey_view_keyboard,
    confirm_delete_keyboard,
    main_menu_builder,
    mentor_feedback_list_keyboard,
    mentor_feedback_view_keyboard,
)

router = Router()
PRIVILEGED_IDS = {identifier for identifier in (ADMIN_ID, SPECIALIST_ID) if identifier}
router.message.filter(lambda message: message.from_user.id in PRIVILEGED_IDS)
router.callback_query.filter(lambda callback: callback.from_user.id in PRIVILEGED_IDS)


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
            f"⭐ Средний балл: {average}\n"
            f"🔧 Hard: {student[4] if student[4] is not None else '-'} · "
            f"🤝 Soft: {student[5] if student[5] is not None else '-'}\n\n"
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
            f"⭐ Средний балл студентов: {average}\n"
            f"🔧 Hard: {mentor[4] if mentor[4] is not None else '-'} · "
            f"🤝 Soft: {mentor[5] if mentor[5] is not None else '-'}\n\n"
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
    extended = get_extended_statistics()

    text = (
        "📊 <b>Общая статистика</b>\n\n"

        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"

        f"👨‍🎓 <b>Студентов:</b> {students}\n"
        f"👨‍🏭 <b>Наставников:</b> {mentors}\n"
        f"📋 <b>Заполнено анкет:</b> {surveys}\n"
        f"⭐ <b>Средний балл:</b> {average}\n\n"

        f"🔧 <b>Hard skills:</b> {extended['hard_average'] if extended['hard_average'] is not None else '-'}\n"
        f"🤝 <b>Soft skills:</b> {extended['soft_average'] if extended['soft_average'] is not None else '-'}\n"
        f"🎓 <b>Профессиональная пригодность:</b> {extended['suitability_average'] if extended['suitability_average'] is not None else '-'}\n"
        f"🏭 <b>CT Assembly:</b> {extended['ct_assembly_count']} · <b>CT Agro:</b> {extended['ct_agro_count']}\n\n"

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
# ОТЗЫВЫ СТУДЕНТОВ О НАСТАВНИКАХ
# =====================================================

@router.callback_query(F.data == "sp_mentor_feedback")
async def callback_mentor_feedback(callback: CallbackQuery):
    records = get_all_mentor_feedback()
    await callback.answer()
    if not records:
        await callback.message.edit_text(
            "📭 Отзывов студентов о наставниках пока нет.",
            reply_markup=specialist_panel_keyboard(),
        )
        return
    await callback.message.edit_text(
        "🗣 <b>Отзывы студентов о наставниках</b>\n\n"
        "ФИО автора видно только в карточке отзыва и административных выгрузках.",
        parse_mode="HTML",
        reply_markup=mentor_feedback_list_keyboard(records),
    )


@router.callback_query(F.data == "sp_feedback_statistics")
async def callback_feedback_statistics(callback: CallbackQuery):
    stats = get_mentor_feedback_statistics()
    text = (
        "📈 <b>Статистика отзывов о наставниках</b>\n\n"
        f"Всего отзывов: <b>{stats['count']}</b>\n"
        f"Оценено наставников: <b>{stats['mentor_count']}</b>\n"
        f"Средняя оценка: <b>{stats['average']}/5</b>\n\n"
    )
    for item in stats["mentors"][:40]:
        text += (
            f"• <b>{html.escape(item['mentor_name'])}</b>\n"
            f"  {html.escape(item['enterprise'] or 'Предприятие не указано')} · "
            f"{item['feedback_count']} отзыв(а) · {item['average']}/5\n\n"
        )
    await callback.answer()
    await callback.message.edit_text(text[:4090], parse_mode="HTML", reply_markup=specialist_panel_keyboard())


@router.callback_query(F.data.regexp(r"^sp_feedback_\d+$"))
async def callback_open_feedback(callback: CallbackQuery):
    feedback_id = int(callback.data.rsplit("_", 1)[1])
    record = get_mentor_feedback(feedback_id)
    await callback.answer()
    if not record:
        await callback.message.edit_text("Отзыв не найден.")
        return
    scores = " · ".join(
        f"{question.get('code', index + 1)}: {score}"
        for index, (question, score) in enumerate(zip(record["questions"], record["ratings"]))
    )
    text = (
        f"🗣 <b>Отзыв №{record['id']}</b>\n\n"
        f"👨‍🏭 <b>Наставник:</b> {html.escape(record['mentor_name'])}\n"
        f"🏭 <b>Предприятие:</b> {html.escape(record['enterprise'] or 'Не указано')}\n"
        f"📍 <b>Город / участок:</b> {html.escape(' · '.join(value for value in (record['city'], record['workshop']) if value) or 'Не указано')}\n"
        f"📘 <b>Модуль:</b> {html.escape(record['module'])}\n"
        f"⭐ <b>Средняя оценка:</b> {record['average']}/5\n"
        f"📅 <b>Дата:</b> {record['submitted_at']}\n\n"
        f"🔐 <b>Автор — только для администратора:</b>\n"
        f"{html.escape(record['student_name'])} · {record['stream']} поток · {record['course']} курс\n\n"
        f"<b>Оценки:</b>\n{scores}\n\n"
        f"<b>Сильные стороны:</b>\n{html.escape(record['strengths'] or '-')}\n\n"
        f"<b>Что улучшить:</b>\n{html.escape(record['weaknesses'] or '-')}\n\n"
        f"<b>Общий вывод:</b>\n{html.escape(record['conclusion'] or '-')}"
    )
    await callback.message.edit_text(
        text[:4090],
        parse_mode="HTML",
        reply_markup=mentor_feedback_view_keyboard(feedback_id),
    )


@router.callback_query(F.data == "sp_feedback_excel")
async def callback_feedback_excel_all(callback: CallbackQuery):
    records = get_all_mentor_feedback()
    await callback.answer()
    if not records:
        await callback.message.answer("Отзывов для выгрузки пока нет.")
        return
    filename = export_mentor_feedback_excel(records)
    await callback.message.answer_document(
        document=FSInputFile(filename),
        caption="📊 Отзывы студентов о наставниках",
    )


@router.callback_query(F.data.regexp(r"^feedback_excel_\d+$"))
async def callback_feedback_excel_one(callback: CallbackQuery):
    feedback_id = int(callback.data.rsplit("_", 1)[1])
    record = get_mentor_feedback(feedback_id)
    await callback.answer()
    if not record:
        await callback.message.answer("Отзыв не найден.")
        return
    filename = export_mentor_feedback_excel([record], feedback_id)
    await callback.message.answer_document(document=FSInputFile(filename), caption=f"📊 Отзыв №{feedback_id}")


@router.callback_query(F.data.regexp(r"^feedback_pdf_\d+$"))
async def callback_feedback_pdf_one(callback: CallbackQuery):
    feedback_id = int(callback.data.rsplit("_", 1)[1])
    record = get_mentor_feedback(feedback_id)
    await callback.answer()
    if not record:
        await callback.message.answer("Отзыв не найден.")
        return
    filename = export_mentor_feedback_pdf(record)
    await callback.message.answer_document(document=FSInputFile(filename), caption=f"📄 Отзыв №{feedback_id}")


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
            surveys.recommendation,
            COALESCE(
                surveys.enterprise,
                students.enterprise,
                'Не указано'
            ),
            students.stream,
            COALESCE(surveys.questionnaire_key, 'legacy'),
            surveys.hard_average,
            surveys.soft_average,
            surveys.suitability_score
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
        f"👥 <b>Поток:</b> {survey[8]}\n"
        f"🏭 <b>Предприятие:</b> {survey[7]}\n"
        f"👨‍🏭 <b>Наставник:</b> {survey[1]}\n"
        f"📅 <b>Дата:</b> {survey[2]}\n"
        f"📋 <b>Тип анкеты:</b> {survey[9]}\n"
        f"⭐ <b>Средний балл:</b> {survey[3]}\n"
        f"🔧 <b>Hard skills:</b> {survey[10] if survey[10] is not None else '-'}\n"
        f"🤝 <b>Soft skills:</b> {survey[11] if survey[11] is not None else '-'}\n"
        f"🎓 <b>Профессиональная пригодность:</b> {survey[12] if survey[12] is not None else '-'}\n\n"
        f"✅ <b>{OPEN_QUESTIONS[0]}</b>\n{survey[4]}\n\n"
        f"📈 <b>{OPEN_QUESTIONS[1]}</b>\n{survey[5]}\n\n"
        f"💬 <b>{OPEN_QUESTIONS[2]}</b>\n{survey[6]}"
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
