"""
Telegram Bot main setup.
"""
import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.client.default import DefaultBotProperties

from app.config import settings
from app.bot.middlewares.lang_middleware import LangMiddleware
from app.bot.handlers import registration, menu, admin

logger = logging.getLogger(__name__)


def create_bot() -> Bot:
    return Bot(
        token=settings.BOT_TOKEN,
        default=DefaultBotProperties(parse_mode="HTML"),
    )


def create_dispatcher() -> Dispatcher:
    dp = Dispatcher(storage=MemoryStorage())

    # Middlewares
    dp.message.middleware(LangMiddleware())
    dp.callback_query.middleware(LangMiddleware())

    # Routers (order matters)
    dp.include_router(registration.router)
    dp.include_router(admin.router)
    dp.include_router(menu.router)

    return dp


async def start_polling():
    bot = create_bot()
    dp = create_dispatcher()

    logger.info("Starting bot polling...")
    await dp.start_polling(bot, allowed_updates=["message", "callback_query"])
