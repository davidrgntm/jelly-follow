"""Language middleware — injects employee and lang into every handler."""
import logging
from typing import Any, Awaitable, Callable, Dict
from aiogram import BaseMiddleware
from aiogram.types import TelegramObject, Message, CallbackQuery
from app.services.employees_service import get_employee_by_telegram_id
from app.services.admins_service import is_admin, get_admin_language

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
            is_admin_user = False
            try:
                is_admin_user = is_admin(user.id)
            except Exception as e:
                logger.debug("Admin lookup failed: %s", e)

            # MUHIM: admin foydalanuvchi uchun tilni avval admin saqlangan tilidan olamiz.
            # Aks holda employee.language_code ustiga qaytib, admin panel yana uzbekchaga tushib qolishi mumkin.
            if is_admin_user:
                try:
                    lang = get_admin_language(user.id, default="uz")
                except Exception as e:
                    logger.debug("Admin language lookup failed: %s", e)

            try:
                employee = get_employee_by_telegram_id(user.id)
            except Exception as e:
                logger.debug("Employee lookup failed: %s", e)

            if employee and not is_admin_user:
                lang = employee.get("language_code", "uz") or "uz"

        data["employee"] = employee
        data["lang"] = lang
        return await handler(event, data)
