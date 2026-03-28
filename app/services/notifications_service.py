"""Notifications service — send Telegram messages to employees."""
import logging
from typing import Optional
from aiogram import Bot
from app.config import settings

logger = logging.getLogger(__name__)
_bot: Optional[Bot] = None

def get_bot():
    global _bot
    if _bot is None:
        _bot = Bot(token=settings.BOT_TOKEN)
    return _bot

async def notify_event_started(employees, event, rewards, lang_map=None):
    from app.bot.texts.translations import t
    from app.bot.keyboards.main_keyboards import event_participate_keyboard
    bot = get_bot()
    for emp in employees:
        tg_id = emp.get("telegram_user_id")
        if not tg_id:
            continue
        lang = emp.get("language_code", "uz")
        reward_lines = "\n".join(
            f"  {r.get('place_number')}-o'rin: {r.get('reward_title')} ({r.get('reward_amount')} {r.get('currency_code', '')})"
            for r in rewards
        )
        pool_amount = event.get("reward_pool_amount", "")
        pool_currency = event.get("reward_pool_currency", "")
        pool_line = ""
        if pool_amount:
            pool_line = f"\n{t('event.pool', lang).format(amount=pool_amount, currency=pool_currency)}"

        text = t("event.notification", lang).format(
            event_name=event.get("event_name", ""),
            description=event.get("description", ""),
            start_at=event.get("start_at", ""),
            end_at=event.get("end_at", ""),
            rules=event.get("rules_text", ""),
            rewards=reward_lines or "-",
        ) + pool_line
        try:
            await bot.send_message(
                chat_id=int(tg_id), text=text, parse_mode="HTML",
                reply_markup=event_participate_keyboard(lang, event.get("event_id", ""), ""),
            )
            logger.info("Notified %s about event %s", emp.get("employee_id"), event.get("event_id"))
        except Exception as e:
            logger.warning("Failed to notify %s: %s", tg_id, e)

async def send_message(telegram_user_id, text):
    bot = get_bot()
    try:
        await bot.send_message(chat_id=int(telegram_user_id), text=text, parse_mode="HTML")
    except Exception as e:
        logger.warning("Failed to send to %s: %s", telegram_user_id, e)
