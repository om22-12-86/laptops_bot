from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties
from handlers.user_handlers import router as user_router
from handlers.admin_handlers import router as admin_router
from database.database import init_db
from dotenv import load_dotenv
import os

# Загружаем .env
load_dotenv()

# Проверяем, загружен ли токен
BOT_TOKEN = os.getenv("BOT_TOKEN")
if not BOT_TOKEN:
    raise ValueError("Ошибка: BOT_TOKEN не найден! Проверьте .env файл.")

# Создаём бота (новый синтаксис)
bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
dp = Dispatcher()

# Подключаем роутеры
dp.include_router(user_router)
dp.include_router(admin_router)

# Инициализация базы данных при старте
async def on_startup():
    await init_db()

if __name__ == "__main__":
    dp.run_polling(bot, on_startup=on_startup)