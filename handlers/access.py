"""Owner-controlled specialist access, identified by Telegram user ID."""
import html
from contextlib import closing

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from database import can_manage_access, get_connection, is_specialist, set_specialist
from keyboards import specialist_panel_keyboard

router = Router()
PAGE_SIZE = 12


def access_list(page=0):
    with closing(get_connection()) as conn:
        people = conn.execute(
            "SELECT telegram_id, fio FROM mentors WHERE telegram_id > 0 ORDER BY fio, telegram_id"
        ).fetchall()
    page = max(0, min(page, max(0, (len(people) - 1) // PAGE_SIZE)))
    rows = [[InlineKeyboardButton(
        text=f"{'✓ ' if is_specialist(uid) else ''}{fio} · {uid}",
        callback_data=f"access_choose_{uid}",
    )] for uid, fio in people[page * PAGE_SIZE:(page + 1) * PAGE_SIZE]]
    navigation = []
    if page:
        navigation.append(InlineKeyboardButton(text="←", callback_data=f"access_list_{page - 1}"))
    if (page + 1) * PAGE_SIZE < len(people):
        navigation.append(InlineKeyboardButton(text="→", callback_data=f"access_list_{page + 1}"))
    if navigation:
        rows.append(navigation)
    rows.append([InlineKeyboardButton(text="← В кабинет", callback_data="back_specialist")])
    return (
        "🔐 Доступ к кабинету специалиста\n\n"
        "Выберите зарегистрированного наставника. ✓ — доступ уже есть.\n"
        "Перед назначением сверьте Telegram ID: наставник может узнать его командой /myid. "
        "Одного совпадения ФИО недостаточно.\n\n"
        + (f"Страница {page + 1}." if people else "Наставники пока не зарегистрированы."),
        InlineKeyboardMarkup(inline_keyboard=rows),
    )


@router.message(Command("myid"))
async def my_id(message):
    if message.chat.type != "private":
        await message.answer("Отправьте /myid в личном чате с ботом.")
        return
    uid = message.from_user.id
    role = "включён" if is_specialist(uid) else "не включён"
    await message.answer(f"Ваш Telegram ID: {uid}\nДоступ к кабинету специалиста: {role}.")


@router.message(Command("admins"))
async def access_command(message):
    if message.chat.type != "private" or not can_manage_access(message.from_user.id):
        await message.answer("Назначать доступ может только администратор, указанный в настройках бота, в личном чате.")
        return
    text, keyboard = access_list()
    await message.answer(text, reply_markup=keyboard)


@router.callback_query(F.data.startswith("access_"))
async def access_callback(callback):
    if (not can_manage_access(callback.from_user.id)
            or not callback.message or callback.message.chat.type != "private"):
        await callback.answer("Нет права назначать доступ.", show_alert=True)
        return
    try:
        _, action, value = callback.data.split("_")
        value = int(value)
    except (ValueError, TypeError):
        await callback.answer("Некорректная команда.", show_alert=True)
        return
    if action == "list":
        await callback.answer()
        text, keyboard = access_list(value)
        await callback.message.edit_text(text, reply_markup=keyboard)
        return
    if action not in {"choose", "grant"}:
        await callback.answer("Неизвестное действие.")
        return
    with closing(get_connection()) as conn:
        person = conn.execute("SELECT fio FROM mentors WHERE telegram_id=?", (value,)).fetchone()
    if not person or value <= 0:
        await callback.answer("Наставник не найден. Обновите список.", show_alert=True)
        return
    name = html.escape(person[0])
    if action == "choose":
        granted = is_specialist(value)
        rows = [] if granted else [[InlineKeyboardButton(
            text="Подтвердить доступ", callback_data=f"access_grant_{value}"
        )]]
        rows.append([InlineKeyboardButton(text="← К списку", callback_data="access_list_0")])
        await callback.answer()
        await callback.message.edit_text(
            f"<b>{name}</b>\nTelegram ID: <code>{value}</code>\n\n"
            + ("Доступ к кабинету специалиста уже включён. Отправьте /start для обновления меню."
               if granted else "Предоставить доступ ко всем анкетам, статистике, выгрузкам и функциям кабинета специалиста, включая удаление анкет?\n\nСверьте Telegram ID с командой /myid наставника."),
            parse_mode="HTML", reply_markup=InlineKeyboardMarkup(inline_keyboard=rows),
        )
        return
    if not set_specialist(value):
        await callback.answer("Не удалось назначить доступ: запись отсутствует.", show_alert=True)
        return
    await callback.answer("Доступ включён.")
    await callback.message.edit_text(
        f"Доступ к кабинету специалиста включён для <b>{name}</b> (Telegram ID: {value}).\n"
        "Попросите наставника отправить /start боту — появится кнопка «Кабинет специалиста».",
        parse_mode="HTML", reply_markup=specialist_panel_keyboard(callback.from_user.id),
    )
