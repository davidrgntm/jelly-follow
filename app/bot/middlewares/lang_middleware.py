"""Language middleware — injects employee and lang into every handler."""
import logging
from typing import Any, Awaitable, Callable, Dict
from aiogram import BaseMiddleware
from aiogram.types import TelegramObject, Message, CallbackQuery
from app.services.employees_service import get_employee_by_telegram_id

logger = logging.getLogger(__name__)


class LangMiddleware(BaseMiddleware):
    async def __call__(self, handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
                       event: TelegramObject, data: Dict[str, Any]) -> Any:
        user = None
        if isinstance(event, Message) and event.from_user:
            user = event.from_user
        elif isinstance(event, CallbackQuery) and event.from_user:
            user = event.from_user

        employee = None
        lang = "uz"
        if user:
            try:
                employee = get_employee_by_telegram_id(user.id)
            except Exception as e:
                logger.debug("Employee lookup failed: %s", e)
            if employee:
                lang = employee.get("language_code", "uz") or "uz"

        data["employee"] = employee
        data["lang"] = lang
        return await handler(event, data)
