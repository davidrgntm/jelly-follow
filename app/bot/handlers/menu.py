"""
Main menu handlers for employees.
"""
import logging
import io
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, BufferedInputFile
from aiogram.fsm.context import FSMContext

from app.bot.texts.translations import t
from app.bot.keyboards.main_keyboards import (
    main_menu_keyboard, lang_select_keyboard, qr_resend_keyboard,
    event_participate_keyboard,
)
from app.services.employees_service import (
    get_employee_stats, update_employee_language,
)
from app.services.qr_service import get_qr_bytes, generate_employee_qr
from app.services.events_service import get_events_for_employee, respond_participation
from app.services.leaderboard_service import build_leaderboard, get_employee_rank
from app.services.points_service import get_employee_total_points

logger = logging.getLogger(__name__)
router = Router()


def _require_employee(employee, lang, message):
    """Return True if employee missing (sends error message)."""
    return employee is None


# ── Profile ──────────────────────────────────────────────────────────────────

@router.message(F.text.func(lambda t: any(
    w in t for w in ["Profilim", "профиль", "Profile", "профилим", "Profilim"]
)))
async def menu_profile(message: Message, employee: dict, lang: str):
    if not employee:
        await message.answer(t("generic.not_registered", lang))
        return
    points = get_employee_total_points(employee["employee_id"])
    await message.answer(
        t("profile.info", lang).format(
            name=employee.get("full_name", ""),
            phone=employee.get("phone", ""),
            country=employee.get("country_code", ""),
            code=employee.get("employee_code", ""),
            status=employee.get("status", ""),
            points=points,
        ),
        parse_mode="HTML",
        reply_markup=main_menu_keyboard(lang),
    )


# ── QR Code ──────────────────────────────────────────────────────────────────

@router.message(F.text.contains("QR"))
async def menu_qr(message: Message, employee: dict, lang: str):
    if not employee:
        await message.answer(t("generic.not_registered", lang))
        return
    await _send_qr(message, employee, lang)


@router.callback_query(F.data == "qr:resend")
async def cb_qr_resend(cb: CallbackQuery, employee: dict, lang: str):
    if not employee:
        await cb.answer(t("generic.not_registered", lang))
        return
    await _send_qr(cb.message, employee, lang)
    await cb.answer()


async def _send_qr(message: Message, employee: dict, lang: str):
    qr_bytes = get_qr_bytes(employee["employee_id"])
    if not qr_bytes:
        # Generate if missing
        qr_info = generate_employee_qr(
            employee_id=employee["employee_id"],
            employee_code=employee["employee_code"],
            country_code=employee["country_code"],
        )
        from app.integrations.qr_generator import generate_qr_bytes
        qr_bytes = generate_qr_bytes(qr_info["short_link"])

    short_link = employee.get("short_link", "")
    photo = BufferedInputFile(qr_bytes, filename="qr.png")
    await message.answer_photo(
        photo=photo,
        caption=t("qr.caption", lang).format(link=short_link),
        parse_mode="HTML",
        reply_markup=qr_resend_keyboard(lang),
    )


# ── My Link ──────────────────────────────────────────────────────────────────

@router.message(F.text.func(lambda tx: any(
    w in tx for w in ["linkim", "ссылка", "Link", "шилтемем", "linkım"]
)))
async def menu_link(message: Message, employee: dict, lang: str):
    if not employee:
        await message.answer(t("generic.not_registered", lang))
        return
    link = employee.get("short_link", "")
    await message.answer(
        f"🔗 <b>{link}</b>",
        parse_mode="HTML",
        reply_markup=main_menu_keyboard(lang),
    )


# ── Stats ─────────────────────────────────────────────────────────────────────

@router.message(F.text.func(lambda tx: any(
    w in tx for w in ["statistika", "Статистика", "Stats", "статистикам", "Statistika"]
)))
async def menu_stats(message: Message, employee: dict, lang: str):
    if not employee:
        await message.answer(t("generic.not_registered", lang))
        return
    stats = get_employee_stats(employee["employee_id"])
    await message.answer(
        t("stats.info", lang).format(
            total=stats["total_points"],
            today=stats["today_points"],
            week=stats["week_points"],
            month=stats["month_points"],
            unique=stats["unique_devices"],
            duplicate=stats["duplicate_scans"],
        ),
        parse_mode="HTML",
        reply_markup=main_menu_keyboard(lang),
    )


# ── Events ────────────────────────────────────────────────────────────────────

@router.message(F.text.func(lambda tx: any(
    w in tx for w in ["Event", "event", "Меропри", "Иш-чара", "Tədbir"]
)))
async def menu_events(message: Message, employee: dict, lang: str):
    if not employee:
        await message.answer(t("generic.not_registered", lang))
        return

    events = get_events_for_employee(
        employee_id=employee["employee_id"],
        country_code=employee["country_code"],
    )

    if not events:
        await message.answer(
            t("events.list_empty", lang),
            reply_markup=main_menu_keyboard(lang),
        )
        return

    for ev in events:
        rewards_text = "\n".join(
            f"  {r['place_number']}-o'rin: {r['reward_title']}"
            for r in ev.get("rewards", [])
        )
        text = (
            f"🏆 <b>{ev.get('event_name')}</b>\n"
            f"{ev.get('description', '')}\n\n"
            f"📅 {ev.get('start_at')} — {ev.get('end_at')}\n"
            f"📋 {ev.get('rules_text', '')}\n\n"
            f"🎁 Mukofotlar:\n{rewards_text or '-'}"
        )
        kb = event_participate_keyboard(lang, ev["event_id"], ev.get("my_participation", ""))
        await message.answer(text, parse_mode="HTML", reply_markup=kb)


@router.callback_query(F.data.startswith("event:join:"))
async def cb_event_join(cb: CallbackQuery, employee: dict, lang: str):
    if not employee:
        await cb.answer(t("generic.not_registered", lang))
        return
    event_id = cb.data.split(":")[2]
    respond_participation(
        event_id=event_id,
        employee_id=employee["employee_id"],
        country_code=employee["country_code"],
        status="accepted",
    )
    await cb.message.edit_reply_markup(
        reply_markup=event_participate_keyboard(lang, event_id, "accepted")
    )
    await cb.answer(t("events.joined", lang), show_alert=True)


@router.callback_query(F.data.startswith("event:decline:"))
async def cb_event_decline(cb: CallbackQuery, employee: dict, lang: str):
    if not employee:
        await cb.answer(t("generic.not_registered", lang))
        return
    event_id = cb.data.split(":")[2]
    respond_participation(
        event_id=event_id,
        employee_id=employee["employee_id"],
        country_code=employee["country_code"],
        status="declined",
    )
    await cb.message.edit_reply_markup(
        reply_markup=event_participate_keyboard(lang, event_id, "declined")
    )
    await cb.answer(t("events.declined", lang), show_alert=True)


# ── Rating ────────────────────────────────────────────────────────────────────

@router.message(F.text.func(lambda tx: any(
    w in tx for w in ["Reyting", "Рейтинг", "Rating", "Reytinq"]
)))
async def menu_rating(message: Message, employee: dict, lang: str):
    if not employee:
        await message.answer(t("generic.not_registered", lang))
        return

    country = employee.get("country_code", "")
    lb = build_leaderboard(country_code=country, top_n=10)

    if not lb:
        await message.answer(t("rating.empty", lang), reply_markup=main_menu_keyboard(lang))
        return

    medals = {1: "🥇", 2: "🥈", 3: "🥉"}
    rows = []
    for entry in lb:
        medal = medals.get(entry["rank"], f"{entry['rank']}.")
        rows.append(f"{medal} {entry['full_name']} — <b>{entry['points']}</b> ball")

    my_rank = get_employee_rank(employee["employee_id"], country_code=country)
    text = (
        t("rating.title", lang).format(country=country)
        + "\n".join(rows)
        + t("rating.my_rank", lang).format(rank=my_rank if my_rank > 0 else "—")
    )
    await message.answer(text, parse_mode="HTML", reply_markup=main_menu_keyboard(lang))


# ── Change Language ───────────────────────────────────────────────────────────

@router.message(F.text.func(lambda tx: any(
    w in tx for w in ["Tilni", "Сменить язык", "Change Language", "Тилди", "Dili"]
)))
async def menu_change_lang(message: Message, employee: dict, lang: str):
    await message.answer(
        t("start.choose_lang", lang),
        reply_markup=lang_select_keyboard(),
    )


@router.callback_query(F.data.startswith("setlang:"))
async def cb_change_lang(cb: CallbackQuery, employee: dict, lang: str):
    new_lang = cb.data.split(":")[1]
    if employee:
        update_employee_language(cb.from_user.id, new_lang)
    await cb.message.edit_reply_markup(reply_markup=None)
    await cb.message.answer(
        t("generic.lang_changed", new_lang),
        reply_markup=main_menu_keyboard(new_lang),
    )
    await cb.answer()


# ── Help ──────────────────────────────────────────────────────────────────────

@router.message(F.text.func(lambda tx: any(
    w in tx for w in ["Yordam", "Помощь", "Help", "Жардам", "Kömək"]
)))
async def menu_help(message: Message, employee: dict, lang: str):
    await message.answer(
        t("help.text", lang),
        parse_mode="HTML",
        reply_markup=main_menu_keyboard(lang),
    )
