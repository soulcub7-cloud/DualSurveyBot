import asyncio

from aiogram import Bot, Dispatcher

from config import BOT_TOKEN

# ============================
# РОУТЕРЫ
# ============================

from handlers.start import router as start_router
from handlers.registration import router as registration_router
from handlers.survey import router as survey_router
from handlers.specialist import router as specialist_router


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

    print("=" * 50)
    print("🤖 Система анкетирования наставников")
    print("Бот успешно запущен")
    print("=" * 50)

    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())