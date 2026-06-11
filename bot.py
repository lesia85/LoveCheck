import asyncio
from aiogram import Bot, Dispatcher
from config import BOT_TOKEN
from handlers.start import router as start_router 
from handlers.callbacks import router as callbacks_router
from handlers.main_menu import router as main_menu_router
from handlers.satisfaction import router as satisfaction_router
from handlers.ideal_partner import router as ideal_partner_router
from handlers.chat_with_ai import router as chat_router
import logging
from database import create_db

# Настройка логирования в файл
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("bot.log", encoding="utf-8")
    ],
    force=True
)

async def main():
    """
    Главная функция для запуска бота.
    Создаёт бота и диспетчер, добавляет в него роутер из модуля start и 
    из обработчика inline-кнопок, и запускает процесс опроса.
    Если при запуске бота возникнет ошибка, она будет записана в файле bot.log.
    """
    try:
        bot = Bot(token=BOT_TOKEN)
        dp = Dispatcher()

        logging.info("Инициализация базы данных...")
        await create_db()

        # Подключаем роутер с командой /start и роутер обработчика inline-кнопок


        dp.include_router(start_router)
        dp.include_router(callbacks_router)
        dp.include_router(main_menu_router)
        dp.include_router(satisfaction_router)
        dp.include_router(ideal_partner_router)
        #dp.include_router(results_router)
        dp.include_router(chat_router)

        print("Бот запущен...")
        await dp.start_polling(bot)

    except Exception as e:
        logging.error(f"Ошибка при запуске бота: {e}")
        raise

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except Exception as e:
        logging.error(f"Критическая ошибка в работе бота: {e}")
