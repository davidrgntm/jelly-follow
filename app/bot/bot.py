"""Bot factory — creates Bot and Dispatcher with all handlers."""
import logging
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from app.config import settings
from app.bot.middlewares.lang_middleware import LangMiddleware

logger = logging.getLogger(__name__)


def create_bot():
    return Bot(token=settings.BOT_TOKEN)


def create_dispatcher():
    dp = Dispatcher(storage=MemoryStorage())
    dp.message.middleware(LangMiddleware())
    dp.callback_query.middleware(LangMiddleware())

    from app.bot.handlers import registration, menu, admin
    dp.include_router(registration.router)
    dp.include_router(menu.router)
    dp.include_router(admin.router)

    logger.info("Dispatcher created with all handlers")
    return dp
