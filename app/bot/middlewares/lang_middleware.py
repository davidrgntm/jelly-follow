"""
Language middleware — injects user language into handler data.
"""
from typing import Any, Awaitable, Callable, Dict
from aiogram import BaseMiddleware
from aiogram.types import TelegramObject, Message, CallbackQuery

from app.services.employees_service import get_employee_by_telegram_id


class LangMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any],
    ) -> Any:
        user_id = None
        if isinstance(event, Message):
            user_id = event.from_user.id if event.from_user else None
        elif isinstance(event, CallbackQuery):
            user_id = event.from_user.id if event.from_user else None

        lang = "uz"  # default
        employee = None
        if user_id:
            employee = get_employee_by_telegram_id(user_id)
            if employee:
                lang = employee.get("language_code", "uz") or "uz"

        data["lang"] = lang
        data["employee"] = employee
        return await handler(event, data)
