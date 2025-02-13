from aiogram import Bot, Dispatcher
from aiogram.types import Message
from aiogram.filters import Command
import asyncio
from utils.config import Config
from admin.middlewares.admin import AdminMiddleware
from admin.handlers import accounts, channels, stickerpacks, common
from database.database import init_db
from utils.logger import logger

bot = Bot(token=Config.telegram_bot.admin_token)
dp = Dispatcher()

# Подключаем middleware
dp.message.middleware(AdminMiddleware())
dp.callback_query.middleware(AdminMiddleware())

# Регистрируем обработчики
dp.include_router(accounts.router)
dp.include_router(channels.router)
dp.include_router(stickerpacks.router)
dp.include_router(common.router)

async def main():
    await init_db()
    logger.success("Database connected")
    logger.success("Bot started")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main()) 
