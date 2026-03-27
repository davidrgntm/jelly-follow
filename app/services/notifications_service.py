"""
Notifications service — send Telegram messages to employees.
"""
import logging
import asyncio
from typing import Optional

from aiogram import Bot
from app.config import settings

logger = logging.getLogger(__name__)

_bot: Optional[Bot] = None


def get_bot() -> Bot:
    global _bot
    if _bot is None:
        _bot = Bot(token=settings.BOT_TOKEN)
    return _bot


async def notify_event_started(employees: list[dict], event: dict, rewards: list[dict]):
    """
    Send event notification to all relevant employees.
    employees: list of employee dicts with telegram_user_id and language_code
    """
    from app.bot.texts.translations import t

    bot = get_bot()
    for emp in employees:
        tg_id = emp.get("telegram_user_id")
        if not tg_id:
            continue
        lang = emp.get("language_code", "uz")

        reward_lines = "\n".join(
            f"{r.get('place_number')}-o'rin: {r.get('reward_title')} ({r.get('reward_amount')} {r.get('currency_code', '')})"
            for r in rewards
        )

        text = t("event.notification", lang).format(
            event_name=event.get("event_name", ""),
            description=event.get("description", ""),
            start_at=event.get("start_at", ""),
            end_at=event.get("end_at", ""),
            rules=event.get("rules_text", ""),
            rewards=reward_lines or "-",
        )

        try:
            await bot.send_message(chat_id=int(tg_id), text=text, parse_mode="HTML")
            logger.info(f"Notified employee {emp.get('employee_id')} about event {event.get('event_id')}")
        except Exception as e:
            logger.warning(f"Failed to notify {tg_id}: {e}")


async def send_message(telegram_user_id: int, text: str):
    bot = get_bot()
    try:
        await bot.send_message(chat_id=telegram_user_id, text=text, parse_mode="HTML")
    except Exception as e:
        logger.warning(f"Failed to send message to {telegram_user_id}: {e}")
