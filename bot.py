import logging
from aiogram import Bot, Dispatcher
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.contrib.middlewares.logging import LoggingMiddleware
import settings


logging.basicConfig(level=logging.INFO)

bot = Bot(token=settings.API_KEY)
dp = Dispatcher(bot, storage=MemoryStorage())
dp.middleware.setup(LoggingMiddleware())


async def send_message(message, chat_id=settings.ADMIN_CHAT, keyboard = None):
    if keyboard:
        await bot.send_message(chat_id=chat_id, text=message, reply_markup=keyboard)
    else:
        await bot.send_message(chat_id=chat_id, text=message)


async def send_document(filename, file):
    await bot.send_document(chat_id=settings.ADMIN_CHAT, document=(filename, file))
