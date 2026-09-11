import asyncio
from contextlib import suppress

from aiogram import Bot, Dispatcher

from config import BOT_TOKEN

# ============================
# РОУТЕРЫ
# ============================

from handlers.start import router as start_router
from handlers.registration import router as registration_router
from handlers.survey import router as survey_router
from handlers.specialist import router as specialist_router
from fill_students import sync_reference_data
from lms_sync import periodic_lms_sync


# ============================
# БОТ И ДИСПЕТЧЕР
# ============================

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()


# ============================
# ПОДКЛЮЧЕНИЕ РОУТЕРОВ
# ============================

dp.include_router(start_router)
dp.include_router(registration_router)
dp.include_router(survey_router)
dp.include_router(specialist_router)


# ============================
# ЗАПУСК
# ============================

async def main():

    try:
        sync_reference_data()
    except Exception as error:
        print(f"Не удалось синхронизировать справочники: {error}")

    print("=" * 50)
    print("🤖 Система анкетирования наставников")
    print("Бот успешно запущен")
    print("=" * 50)

    sync_task = asyncio.create_task(periodic_lms_sync())
    try:
        await dp.start_polling(bot)
    finally:
        sync_task.cancel()
        with suppress(asyncio.CancelledError):
            await sync_task


if __name__ == "__main__":
    asyncio.run(main())
