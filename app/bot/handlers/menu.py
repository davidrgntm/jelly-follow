"""Main menu handlers for employees. Event QR sending included."""
import logging
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, BufferedInputFile, InlineKeyboardMarkup, InlineKeyboardButton
from app.bot.texts.translations import t, TRANSLATIONS
from app.bot.keyboards.main_keyboards import (
    main_menu_keyboard, lang_select_keyboard, qr_resend_keyboard, event_participate_keyboard,
)
from app.services.admins_service import is_admin
from app.services.employees_service import get_employee_stats, update_employee_language, update_last_active
from app.services.qr_service import get_qr_bytes, generate_employee_qr, generate_event_qr, get_event_qr_bytes
from app.services.events_service import (
    get_events_for_employee, respond_participation, get_primary_active_event_for_country,
    get_active_events_for_country, get_event_by_id,
)
from app.services.leaderboard_service import build_leaderboard, get_employee_rank
from app.services.points_service import get_employee_total_points
from app.integrations.qr_generator import generate_qr_bytes as gen_qr_bytes

logger = logging.getLogger(__name__)
router = Router()


def _normalize_text(value):
    if not value:
        return ""
    return value.strip().lower().replace("\ufe0f", "")

def _all_variants_for_key(key):
    entry = TRANSLATIONS.get(key, {})
    return list({_normalize_text(v) for v in entry.values() if isinstance(v, str) and v.strip()})

def _menu_matcher(tx, lang_keys):
    normalized = _normalize_text(tx)
    if not normalized:
        return False
    for key in lang_keys:
        if normalized in _all_variants_for_key(key):
            return True
    return False

def _menu_markup(lang, user_id):
    return main_menu_keyboard(lang, is_admin=is_admin(user_id))


STATUS_LABELS = {
    "accepted": {"uz": "Qatnashaman", "ru": "Участвую", "en": "Joined", "kg": "Катышам", "az": "Qatılıram"},
    "declined": {"uz": "Qatnashmayman", "ru": "Не участвую", "en": "Declined", "kg": "Катышпайм", "az": "Qatılmıram"},
    "pending": {"uz": "Javob kutilmoqda", "ru": "Ожидается ответ", "en": "Awaiting reply", "kg": "Жооп күтүлүүдө", "az": "Cavab gözlənilir"},
    "": {"uz": "Javob berilmagan", "ru": "Нет ответа", "en": "No reply yet", "kg": "Жооп жок", "az": "Cavab yoxdur"},
}

REWARD_TITLE = {
    "uz": "🎁 Mukofotlar",
    "ru": "🎁 Mukofotlar",
    "en": "🎁 Rewards",
    "kg": "🎁 Сыйлыктар",
    "az": "🎁 Mükafatlar",
}

RULES_TITLE = {
    "uz": "📋 Qoidalar",
    "ru": "📋 Правила",
    "en": "📋 Rules",
    "kg": "📋 Эрежелер",
    "az": "📋 Qaydalar",
}

STATUS_TITLE = {
    "uz": "👤 Holat",
    "ru": "👤 Status",
    "en": "👤 Status",
    "kg": "👤 Абал",
    "az": "👤 Status",
}


def _lang_label(mapping, lang, default=""):
    return mapping.get(lang) or mapping.get("uz") or default


def _event_status_label(status: str, lang: str) -> str:
    return _lang_label(STATUS_LABELS.get(status or "", STATUS_LABELS[""]), lang, status or "—")


def _format_event_rewards(rewards, lang: str) -> str:
    if not rewards:
        return "-"
    seen = set()
    lines = []
    for reward in sorted(rewards, key=lambda r: int(r.get("place_number", 999999) or 999999)):
        key = (str(reward.get("place_number", "")), str(reward.get("reward_title", "")), str(reward.get("reward_amount", "")), str(reward.get("currency_code", "")))
        if key in seen:
            continue
        seen.add(key)
        place = reward.get("place_number", "")
        title = (str(reward.get("reward_title") or "")).strip()
        amount = (str(reward.get("reward_amount") or "")).strip()
        currency = (str(reward.get("currency_code") or "")).strip()
        parts = []
        if title and title.lower() not in {f"{place}-place", f"{place}-o'rin", f"{place}-orin"}:
            parts.append(title)
        if amount:
            parts.append(f"{amount} {currency}".strip())
        tail = " — ".join(parts) if parts else "-"
        lines.append(f"• {place}-o'rin — <b>{tail}</b>")
    return "\n".join(lines) or "-"


def _render_event_text(ev: dict, lang: str) -> str:
    title = (ev.get("event_name") or "").strip()
    code = (ev.get("event_code") or ev.get("event_id") or "").strip()
    description = (ev.get("description") or "").strip()
    start_at = (ev.get("start_at") or "").strip()
    end_at = (ev.get("end_at") or "").strip()
    rules = (ev.get("rules_text") or "").strip()
    my_status = ev.get("my_participation", "")
    rewards_text = _format_event_rewards(ev.get("rewards", []), lang)
    pool_amount = (str(ev.get("reward_pool_amount") or "")).strip()
    pool_currency = (str(ev.get("reward_pool_currency") or "")).strip()

    lines = [f"🏆 <b>{title}</b>", f"🆔 <code>{code}</code>"]
    if description:
        lines.extend(["", description])
    lines.extend(["", f"📅 <b>{start_at}</b> — <b>{end_at}</b>"])
    if pool_amount:
        lines.append(t("event.pool", lang).format(amount=pool_amount, currency=pool_currency))
    lines.append(f"{_lang_label(STATUS_TITLE, lang)}: <b>{_event_status_label(my_status, lang)}</b>")
    if rules:
        lines.extend(["", f"{_lang_label(RULES_TITLE, lang)}:", rules])
    lines.extend(["", f"{_lang_label(REWARD_TITLE, lang)}:", rewards_text])
    return "\n".join(lines)


@router.message(F.text == "/menu")
async def cmd_menu(message: Message, employee: dict, lang: str):
    if not employee:
        await message.answer(t("generic.not_registered", lang))
        return
    update_last_active(message.from_user.id)
    await message.answer(t("menu.main", lang), reply_markup=_menu_markup(lang, message.from_user.id))


@router.message(F.text.func(lambda tx: _menu_matcher(tx, ["menu.profile"])))
async def menu_profile(message: Message, employee: dict, lang: str):
    if not employee:
        await message.answer(t("generic.not_registered", lang))
        return
    update_last_active(message.from_user.id)
    points = get_employee_total_points(employee["employee_id"])
    await message.answer(
        t("profile.info", lang).format(
            name=employee.get("full_name", ""), phone=employee.get("phone", ""),
            country=employee.get("country_code", ""), code=employee.get("employee_code", ""),
            status=employee.get("status", ""), points=points,
        ), parse_mode="HTML", reply_markup=_menu_markup(lang, message.from_user.id))


@router.message(F.text.func(lambda tx: _menu_matcher(tx, ["menu.my_qr"])))
async def menu_qr(message: Message, employee: dict, lang: str):
    if not employee:
        await message.answer(t("generic.not_registered", lang))
        return
    update_last_active(message.from_user.id)
    events = get_active_events_for_country(employee.get("country_code", ""))
    if not events:
        await _send_personal_qr(message, employee, lang)
        return
    await message.answer(t("qr.choose_type", lang), reply_markup=_qr_select_keyboard(events, lang))


@router.callback_query(F.data == "qr:resend")
async def cb_qr_resend(cb: CallbackQuery, employee: dict, lang: str):
    if not employee:
        await cb.answer(t("generic.not_registered", lang))
        return
    events = get_active_events_for_country(employee.get("country_code", ""))
    if not events:
        await _send_personal_qr(cb.message, employee, lang)
    else:
        await cb.message.answer(t("qr.choose_type", lang), reply_markup=_qr_select_keyboard(events, lang))
    await cb.answer()


@router.callback_query(F.data == "qr:self")
async def cb_qr_self(cb: CallbackQuery, employee: dict, lang: str):
    if not employee:
        await cb.answer(t("generic.not_registered", lang))
        return
    await _send_personal_qr(cb.message, employee, lang)
    await cb.answer()


@router.callback_query(F.data.startswith("qr:event:"))
async def cb_qr_event(cb: CallbackQuery, employee: dict, lang: str):
    if not employee:
        await cb.answer(t("generic.not_registered", lang))
        return
    event_id = cb.data.split(":", 2)[2]
    await _send_event_qr(cb.message, employee, event_id, lang)
    await cb.answer()


def _qr_select_keyboard(events, lang):
    rows = [[InlineKeyboardButton(text=t("qr.personal", lang), callback_data="qr:self")]]
    for ev in events:
        event_name = (ev.get("event_name") or ev.get("event_id") or "Event").strip()
        rows.append([InlineKeyboardButton(text=f"{t('qr.event_prefix', lang)}: {event_name[:40]}", callback_data=f"qr:event:{ev['event_id']}")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


async def _send_personal_qr(message, employee, lang):
    qr_bytes = get_qr_bytes(employee["employee_id"])
    qr_info = None
    if not qr_bytes:
        qr_info = generate_employee_qr(employee["employee_id"], employee["employee_code"], employee["country_code"])
        qr_bytes = gen_qr_bytes(qr_info["short_link"])
    short_link = (qr_info or {}).get("short_link") or employee.get("short_link", "")
    photo = BufferedInputFile(qr_bytes, filename="qr.png")
    await message.answer_photo(photo=photo, caption=t("qr.caption", lang).format(link=short_link),
                               parse_mode="HTML", reply_markup=qr_resend_keyboard(lang))


async def _send_event_qr(message, employee, event_id, lang):
    qr_bytes = get_event_qr_bytes(employee["employee_id"], event_id)
    qr_info = None
    if not qr_bytes:
        qr_info = generate_event_qr(employee["employee_id"], employee["employee_code"], event_id, employee["country_code"])
        qr_bytes = gen_qr_bytes(qr_info["short_link"])
    event = get_event_by_id(event_id) or {}
    short_link = (qr_info or {}).get("short_link", "")
    if not short_link:
        event_code = event.get("event_code") or event_id
        short_link = f"{employee.get('short_link', '')}?event={event_code}" if employee.get("short_link") else ""
    photo = BufferedInputFile(qr_bytes, filename="event_qr.png")
    await message.answer_photo(
        photo=photo,
        caption=t("qr.event_caption", lang).format(link=short_link, event_name=event.get("event_name", event_id)),
        parse_mode="HTML",
        reply_markup=qr_resend_keyboard(lang),
    )


@router.message(F.text.func(lambda tx: _menu_matcher(tx, ["menu.my_link"])))
async def menu_link(message: Message, employee: dict, lang: str):
    if not employee:
        await message.answer(t("generic.not_registered", lang))
        return
    update_last_active(message.from_user.id)
    link = employee.get("short_link", "")
    await message.answer(f"🔗 <b>{link}</b>", parse_mode="HTML",
                         reply_markup=_menu_markup(lang, message.from_user.id))


@router.message(F.text.func(lambda tx: _menu_matcher(tx, ["menu.stats"])))
async def menu_stats(message: Message, employee: dict, lang: str):
    if not employee:
        await message.answer(t("generic.not_registered", lang))
        return
    update_last_active(message.from_user.id)
    stats = get_employee_stats(employee["employee_id"])
    event_lines = ""
    if stats.get("event_points"):
        event_lines = "\n\n🏁 Event ballari:\n" + "\n".join(
            f"• {row['event_name']}: <b>{row['points']}</b>" for row in stats["event_points"][:5])
    await message.answer(
        t("stats.info", lang).format(
            total=stats["total_points"], today=stats["today_points"],
            week=stats["week_points"], month=stats["month_points"],
            unique=stats["unique_devices"], duplicate=stats["duplicate_scans"],
        ) + event_lines, parse_mode="HTML", reply_markup=_menu_markup(lang, message.from_user.id))


@router.message(F.text.func(lambda tx: _menu_matcher(tx, ["menu.events"])))
async def menu_events(message: Message, employee: dict, lang: str):
    if not employee:
        await message.answer(t("generic.not_registered", lang))
        return
    update_last_active(message.from_user.id)
    events = get_events_for_employee(employee["employee_id"], employee["country_code"])
    if not events:
        await message.answer(t("events.list_empty", lang), reply_markup=_menu_markup(lang, message.from_user.id))
        return
    events = sorted(events, key=lambda ev: (ev.get("start_at") or "", ev.get("event_name") or ""))
    for ev in events:
        my_status = ev.get("my_participation", "")
        text = _render_event_text(ev, lang)
        kb = event_participate_keyboard(lang, ev["event_id"], my_status)
        await message.answer(text, parse_mode="HTML", reply_markup=kb)


@router.callback_query(F.data.startswith("event:join:"))
async def cb_event_join(cb: CallbackQuery, employee: dict, lang: str):
    if not employee:
        await cb.answer(t("generic.not_registered", lang))
        return
    event_id = cb.data.split(":")[2]
    respond_participation(event_id=event_id, employee_id=employee["employee_id"],
                          country_code=employee["country_code"], status="accepted")
    await cb.message.edit_reply_markup(
        reply_markup=event_participate_keyboard(lang, event_id, "accepted"))
    # Send event QR
    try:
        qr_info = generate_event_qr(employee["employee_id"], employee["employee_code"],
                                     event_id, employee["country_code"])
        qr_bytes = gen_qr_bytes(qr_info["short_link"])
        photo = BufferedInputFile(qr_bytes, filename="event_qr.png")
        await cb.message.answer_photo(
            photo=photo,
            caption=f"📱 <b>{t('event.qr_sent', lang)}</b>\n\n🔗 {qr_info['short_link']}",
            parse_mode="HTML",
            reply_markup=qr_resend_keyboard(lang),
        )
    except Exception as e:
        logger.warning("Event QR generation failed: %s", e)
    await cb.answer(t("events.joined", lang), show_alert=True)


@router.callback_query(F.data.startswith("event:decline:"))
async def cb_event_decline(cb: CallbackQuery, employee: dict, lang: str):
    if not employee:
        await cb.answer(t("generic.not_registered", lang))
        return
    event_id = cb.data.split(":")[2]
    respond_participation(event_id=event_id, employee_id=employee["employee_id"],
                          country_code=employee["country_code"], status="declined")
    await cb.message.edit_reply_markup(
        reply_markup=event_participate_keyboard(lang, event_id, "declined"))
    await cb.answer(t("events.declined", lang), show_alert=True)


@router.message(F.text.func(lambda tx: _menu_matcher(tx, ["menu.rating"])))
async def menu_rating(message: Message, employee: dict, lang: str):
    if not employee:
        await message.answer(t("generic.not_registered", lang))
        return
    update_last_active(message.from_user.id)
    country = employee.get("country_code", "")
    lb = build_leaderboard(country_code=country, top_n=10)
    if not lb:
        await message.answer(t("rating.empty", lang), reply_markup=_menu_markup(lang, message.from_user.id))
        return
    medals = {1: "🥇", 2: "🥈", 3: "🥉"}
    rows = [f"{medals.get(e['rank'], str(e['rank'])+'.') } {e['full_name']} — <b>{e['points']}</b>" for e in lb]
    my_rank = get_employee_rank(employee["employee_id"], country_code=country)
    text = t("rating.title", lang).format(country=country) + "\n".join(rows)

    active_event = get_primary_active_event_for_country(country)
    if active_event:
        event_lb = build_leaderboard(event_id=active_event["event_id"], top_n=5)
        if event_lb:
            text += f"\n\n🏆 <b>{active_event.get('event_name')}</b>\n"
            text += "\n".join(f"{medals.get(e['rank'], str(e['rank'])+'.') } {e['full_name']} — <b>{e['points']}</b>" for e in event_lb)
            event_rank = get_employee_rank(employee["employee_id"], event_id=active_event["event_id"])
            text += f"\n\nEvent o'rningiz: <b>{event_rank if event_rank > 0 else '—'}</b>"

    text += t("rating.my_rank", lang).format(rank=my_rank if my_rank > 0 else "—")
    await message.answer(text, parse_mode="HTML", reply_markup=_menu_markup(lang, message.from_user.id))


@router.message(F.text.func(lambda tx: _menu_matcher(tx, ["menu.change_lang"])))
async def menu_change_lang(message: Message, employee: dict, lang: str):
    await message.answer(t("start.choose_lang", lang), reply_markup=lang_select_keyboard())


@router.callback_query(F.data.startswith("setlang:"))
async def cb_change_lang(cb: CallbackQuery, employee: dict, lang: str):
    new_lang = cb.data.split(":")[1]
    if employee:
        update_employee_language(cb.from_user.id, new_lang)
    await cb.message.edit_reply_markup(reply_markup=None)
    await cb.message.answer(t("generic.lang_changed", new_lang),
                            reply_markup=main_menu_keyboard(new_lang, is_admin=is_admin(cb.from_user.id)))
    await cb.answer()


@router.message(F.text.func(lambda tx: _menu_matcher(tx, ["menu.help"])))
async def menu_help(message: Message, employee: dict, lang: str):
    await message.answer(t("help.text", lang), parse_mode="HTML",
                         reply_markup=_menu_markup(lang, message.from_user.id))
