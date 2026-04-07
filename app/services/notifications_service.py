"""Notifications service — send Telegram messages to employees."""
import logging
from typing import Optional
from aiogram import Bot
from app.config import settings

logger = logging.getLogger(__name__)
_bot: Optional[Bot] = None

UPDATE_MESSAGES = {
    "uz": """<b>Jelly Follow bot yangilandi ✅</b>

Endi QR kod yangi ko'rinishda ishlaydi:
• QR tugmasi orqali ochiladi
• har safar yangi QR yaratiladi
• natija telefoningizda jonli ko'rinadi

Iltimos, botga qayta kiring va QR tugmasi orqali ishlating.""",
    "ru": """<b>Бот Jelly Follow обновился ✅</b>

Теперь QR-код работает по-новому:
• открывается через кнопку QR
• каждый раз создаётся новый QR
• результат показывается прямо у вас на телефоне в реальном времени

Пожалуйста, заново откройте бот и пользуйтесь кнопкой QR.""",
    "kg": """<b>Jelly Follow бот жаңыртылды ✅</b>

Эми QR-код жаңыча иштейт:
• QR баскычы аркылуу ачылат
• ар бир жолу жаңы QR түзүлөт
• жыйынтык телефонуңузда түз көрсөтүлөт

Сураныч, ботко кайра кирип, QR баскычы аркылуу колдонуңуз.""",
    "az": """<b>Jelly Follow botu yeniləndi ✅</b>

İndi QR kod yeni qaydada işləyir:
• QR düyməsi ilə açılır
• hər dəfə yeni QR yaradılır
• nəticə telefonunuzda canlı görünür

Zəhmət olmasa, bota yenidən daxil olun və QR düyməsi ilə istifadə edin.""",
}


def get_bot():
    global _bot
    if _bot is None:
        _bot = Bot(token=settings.BOT_TOKEN)
    return _bot


def _format_rewards(rewards, lang: str) -> str:
    if not rewards:
        return "-"
    seen = set()
    lines = []
    for reward in sorted(rewards, key=lambda r: int(r.get("place_number", 999999) or 999999)):
        key = (
            str(reward.get("place_number", "")),
            str(reward.get("reward_title", "")).strip(),
            str(reward.get("reward_amount", "")).strip(),
            str(reward.get("currency_code", "")).strip(),
        )
        if key in seen:
            continue
        seen.add(key)
        place = str(reward.get("place_number", "")).strip() or "-"
        title = str(reward.get("reward_title", "")).strip()
        amount = str(reward.get("reward_amount", "")).strip()
        currency = str(reward.get("currency_code", "")).strip()
        parts = []
        low = title.lower()
        if title and low not in {f"{place}-place", f"{place}-o'rin", f"{place}-orin"}:
            parts.append(title)
        if amount:
            parts.append(f"{amount} {currency}".strip())
        lines.append(f"• {place}-o'rin — <b>{' — '.join(parts) if parts else '-'}</b>")
    return "\n".join(lines) or "-"


async def notify_event_started(employees, event, rewards, lang_map=None):
    from app.bot.texts.translations import t
    from app.bot.keyboards.main_keyboards import event_participate_keyboard

    bot = get_bot()
    for emp in employees:
        tg_id = emp.get("telegram_user_id")
        if not tg_id:
            continue
        lang = emp.get("language_code", "uz")
        rewards_text = _format_rewards(rewards, lang)
        pool_amount = event.get("reward_pool_amount", "")
        pool_currency = event.get("reward_pool_currency", "")
        pool_line = ""
        if pool_amount:
            pool_line = f"\n{t('event.pool', lang).format(amount=pool_amount, currency=pool_currency)}"

        text = t("event.notification", lang).format(
            event_name=event.get("event_name", ""),
            description=event.get("description", "-") or "-",
            start_at=event.get("start_at", ""),
            end_at=event.get("end_at", ""),
            rules=event.get("rules_text", "-") or "-",
            rewards=rewards_text,
        ) + pool_line + "\n\n✅ / ❌ Tugma orqali qatnashishni tasdiqlang."
        try:
            await bot.send_message(
                chat_id=int(tg_id),
                text=text,
                parse_mode="HTML",
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


async def notify_scan_result(employee: dict, scan_result: dict, event: dict = None):
    """Send scan result notification to employee via Telegram.

    scan_result keys: point_decision, scan_status, point_tx_id, scan_id
    point_decision values: first_unique_device, duplicate_device, suspicious
    """
    from app.bot.texts.translations import t
    from app.services.points_service import get_employee_total_points
    from app.services.leaderboard_service import get_employee_rank

    tg_id = employee.get("telegram_user_id")
    if not tg_id:
        return

    lang = employee.get("language_code", "uz") or "uz"
    employee_id = employee.get("employee_id", "")
    country_code = employee.get("country_code", "")
    decision = scan_result.get("point_decision", "")
    total = get_employee_total_points(employee_id)

    text = ""

    if decision == "first_unique_device":
        rank = get_employee_rank(employee_id, country_code=country_code)
        rank_str = str(rank) if rank > 0 else "—"

        if event and event.get("event_id"):
            from app.services.points_service import get_employee_event_points
            event_points = get_employee_event_points(employee_id, event.get("event_id", ""))
            text = t("scan.notify.unique_event", lang).format(
                total=total,
                rank=rank_str,
                event_name=event.get("event_name", ""),
                event_points=event_points,
            )
        else:
            text = t("scan.notify.unique", lang).format(total=total, rank=rank_str)

    elif decision == "duplicate_device":
        text = t("scan.notify.duplicate", lang).format(total=total)

    elif decision == "suspicious":
        text = t("scan.notify.suspicious", lang)

    else:
        text = t("scan.notify.retry", lang).format(total=total)

    if text:
        try:
            await send_message(tg_id, text)
            logger.info("Scan notification sent to %s: %s", employee_id, decision)
        except Exception as e:
            logger.warning("Failed scan notification to %s: %s", tg_id, e)


async def send_localized_update_broadcast(employees):
    sent = 0
    failed = 0
    seen = set()

    for emp in employees:
        tg_id = str(emp.get("telegram_user_id") or "").strip()
        if not tg_id or tg_id in seen:
            continue
        if emp.get("status") != "active":
            continue
        seen.add(tg_id)

        lang = str(emp.get("language_code") or "uz").strip().lower()
        text = UPDATE_MESSAGES.get(lang) or UPDATE_MESSAGES["uz"]
        try:
            await send_message(tg_id, text)
            sent += 1
        except Exception:
            failed += 1

    return {"sent": sent, "failed": failed, "total": len(seen)}
