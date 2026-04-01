"""Admin bot interface with full translation-key support and Telegram-based web approval."""
import asyncio
import calendar
import logging
from datetime import datetime

from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import (
    Message, CallbackQuery, ReplyKeyboardMarkup, KeyboardButton,
    InlineKeyboardMarkup, InlineKeyboardButton,
)

from app.bot.keyboards.main_keyboards import admin_panel_text, lang_select_keyboard, main_menu_keyboard
from app.bot.texts.translations import t, normalize_text, variants_for_key
from app.services.admins_service import (
    get_admin_by_telegram_id, is_admin, is_super_admin,
    create_admin, get_system_stats,
)
from app.services.employees_service import (
    get_all_employees, update_employee_status, get_employee_by_code,
)
from app.services.events_service import (
    create_event, set_event_status, get_all_events, get_event_by_id,
    get_event_countries, get_event_rewards,
)
from app.services.points_service import manual_adjust
from app.services.leaderboard_service import build_leaderboard
from app.services.notifications_service import notify_event_started
from app.services.web_auth_service import approve_request

logger = logging.getLogger(__name__)
router = Router()

COUNTRY_LABELS = {"UZ": "🇺🇿 UZ", "RU": "🇷🇺 RU", "KG": "🇰🇬 KG", "AZ": "🇦🇿 AZ"}
CURRENCY_LIST = ["UZS", "USD", "EUR", "RUB", "KGS", "AZN"]


class EventCreateStates(StatesGroup):
    name = State()
    description = State()
    rules = State()
    countries = State()
    start_date = State()
    start_hour = State()
    end_date = State()
    end_hour = State()
    reward_pool_amount = State()
    reward_pool_currency = State()
    reward_count = State()
    reward_place_amount = State()
    confirm = State()


class ManualPointsStates(StatesGroup):
    employee_code = State()


class EmployeeStatusStates(StatesGroup):
    employee_code = State()


class AddAdminStates(StatesGroup):
    tg_id = State()
    full_name = State()


def _get_admin_info(user_id):
    admin = get_admin_by_telegram_id(user_id)
    if not admin or admin.get("status") != "active":
        return None
    return admin


def _admin_matcher(tx: str, key: str) -> bool:
    return normalize_text(tx) in variants_for_key(key)


def _is_active_admin_user(user_id: int) -> bool:
    return _get_admin_info(user_id) is not None


def _admin_only():
    return F.from_user.id.func(_is_active_admin_user)


def _admin_text(key: str):
    return _admin_only() & F.text.func(lambda tx: _admin_matcher(tx, key))


def _admin_text_any(*keys: str):
    return _admin_only() & F.text.func(lambda tx: any(_admin_matcher(tx, key) for key in keys))


def _admin_keyboard(lang="uz", role="ga"):
    rows = [
        [KeyboardButton(text=t("admin.menu.events", lang)), KeyboardButton(text=t("admin.menu.create_event", lang))],
        [KeyboardButton(text=t("admin.menu.employees", lang)), KeyboardButton(text=t("admin.menu.leaderboard", lang))],
        [KeyboardButton(text=t("admin.menu.manual_points", lang)), KeyboardButton(text=t("admin.menu.employee_status", lang))],
        [KeyboardButton(text=t("admin.menu.stats", lang)), KeyboardButton(text=t("admin.menu.language", lang))],
    ]
    if role == "super_admin":
        rows.append([KeyboardButton(text=t("admin.menu.add_admin", lang))])
    rows.append([KeyboardButton(text=t("admin.menu.back_employee", lang))])
    return ReplyKeyboardMarkup(keyboard=rows, resize_keyboard=True)


def _cancel_reply_kb(lang="uz"):
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text=t("admin.cancel", lang))]],
        resize_keyboard=True,
    )


def _cancel_inline_kb(lang="uz"):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=t("admin.cancel", lang), callback_data="adm:cancel")]
    ])


def _countries_kb(selected, lang="uz"):
    rows = []
    row = []
    for code in ["UZ", "RU", "KG", "AZ"]:
        prefix = "✅ " if code in selected else "▫️ "
        row.append(InlineKeyboardButton(text=prefix + COUNTRY_LABELS[code], callback_data=f"adm:evt:ctry:{code}"))
        if len(row) == 2:
            rows.append(row)
            row = []
    if row:
        rows.append(row)
    rows.append([InlineKeyboardButton(text=t("admin.continue", lang), callback_data="adm:evt:ctry:done")])
    rows.append([InlineKeyboardButton(text=t("admin.cancel", lang), callback_data="adm:cancel")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


WEEKDAY_HEADERS = {
    "uz": ["Du", "Se", "Ch", "Pa", "Ju", "Sh", "Ya"],
    "ru": ["Пн", "Вт", "Ср", "Чт", "Пт", "Сб", "Вс"],
    "en": ["Mo", "Tu", "We", "Th", "Fr", "Sa", "Su"],
    "kg": ["Дү", "Ше", "Шр", "Бе", "Жу", "Иш", "Жк"],
    "az": ["Be", "Ça", "Çə", "Ca", "Cü", "Şə", "Ba"],
}


def _calendar_kb(year, month, prefix, lang="uz"):
    rows = []
    rows.append([InlineKeyboardButton(text=f"{calendar.month_name[month]} {year}", callback_data="noop")])
    rows.append([InlineKeyboardButton(text=d, callback_data="noop") for d in WEEKDAY_HEADERS.get(lang, WEEKDAY_HEADERS["uz"])])
    for week in calendar.monthcalendar(year, month):
        row = []
        for day in week:
            if day == 0:
                row.append(InlineKeyboardButton(text=" ", callback_data="noop"))
            else:
                row.append(InlineKeyboardButton(text=str(day), callback_data=f"adm:cal:{prefix}:{year}-{month:02d}-{day:02d}"))
        rows.append(row)
    prev_m = month - 1 if month > 1 else 12
    prev_y = year if month > 1 else year - 1
    next_m = month + 1 if month < 12 else 1
    next_y = year if month < 12 else year + 1
    rows.append([
        InlineKeyboardButton(text="◀️", callback_data=f"adm:calnav:{prefix}:{prev_y}-{prev_m:02d}"),
        InlineKeyboardButton(text="▶️", callback_data=f"adm:calnav:{prefix}:{next_y}-{next_m:02d}"),
    ])
    rows.append([InlineKeyboardButton(text=t("admin.cancel", lang), callback_data="adm:cancel")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def _hours_kb(prefix, lang="uz"):
    rows = []
    row = []
    for h in range(24):
        row.append(InlineKeyboardButton(text=f"{h:02d}:00", callback_data=f"adm:hour:{prefix}:{h:02d}"))
        if len(row) == 4:
            rows.append(row)
            row = []
    if row:
        rows.append(row)
    rows.append([InlineKeyboardButton(text=t("admin.cancel", lang), callback_data="adm:cancel")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def _pool_amount_kb(lang="uz"):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="0", callback_data="adm:pool:0"), InlineKeyboardButton(text="500 000", callback_data="adm:pool:500000")],
        [InlineKeyboardButton(text="1 000 000", callback_data="adm:pool:1000000"), InlineKeyboardButton(text="2 000 000", callback_data="adm:pool:2000000")],
        [InlineKeyboardButton(text="5 000 000", callback_data="adm:pool:5000000"), InlineKeyboardButton(text="10 000 000", callback_data="adm:pool:10000000")],
        [InlineKeyboardButton(text=t("admin.cancel", lang), callback_data="adm:cancel")],
    ])


def _currency_kb(lang="uz"):
    rows, row = [], []
    for cur in CURRENCY_LIST:
        row.append(InlineKeyboardButton(text=cur, callback_data=f"adm:currency:{cur}"))
        if len(row) == 3:
            rows.append(row)
            row = []
    if row:
        rows.append(row)
    rows.append([InlineKeyboardButton(text=t("admin.cancel", lang), callback_data="adm:cancel")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def _reward_count_kb(lang="uz"):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=t("admin.event.reward_none", lang), callback_data="adm:rwdcnt:0")],
        [InlineKeyboardButton(text=t("admin.event.reward_top3", lang), callback_data="adm:rwdcnt:3"),
         InlineKeyboardButton(text=t("admin.event.reward_top5", lang), callback_data="adm:rwdcnt:5")],
        [InlineKeyboardButton(text=t("admin.event.reward_top10", lang), callback_data="adm:rwdcnt:10")],
        [InlineKeyboardButton(text=t("admin.cancel", lang), callback_data="adm:cancel")],
    ])


def _confirm_event_kb(lang="uz"):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=t("admin.create", lang), callback_data="adm:event:save")],
        [InlineKeyboardButton(text=t("admin.cancel", lang), callback_data="adm:cancel")],
    ])


def _event_actions_kb(event_id, status, lang="uz"):
    buttons = []
    if status == "draft":
        buttons.append([InlineKeyboardButton(text=t("admin.event.action.activate", lang), callback_data=f"adm:evtact:activate:{event_id}")])
    elif status == "active":
        buttons.append([InlineKeyboardButton(text=t("admin.event.action.pause", lang), callback_data=f"adm:evtact:pause:{event_id}")])
        buttons.append([InlineKeyboardButton(text=t("admin.event.action.finish", lang), callback_data=f"adm:evtact:finish:{event_id}")])
    elif status == "paused":
        buttons.append([InlineKeyboardButton(text=t("admin.event.action.resume", lang), callback_data=f"adm:evtact:activate:{event_id}")])
        buttons.append([InlineKeyboardButton(text=t("admin.event.action.finish", lang), callback_data=f"adm:evtact:finish:{event_id}")])
    buttons.append([InlineKeyboardButton(text=t("admin.event.action.leaderboard", lang), callback_data=f"adm:evtlb:{event_id}")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def _leaderboard_country_kb():
    rows = [[InlineKeyboardButton(text="🌍 All", callback_data="adm:lb:all")]]
    row = []
    for code in ["UZ", "RU", "KG", "AZ"]:
        row.append(InlineKeyboardButton(text=COUNTRY_LABELS[code], callback_data=f"adm:lb:{code}"))
        if len(row) == 2:
            rows.append(row)
            row = []
    if row:
        rows.append(row)
    return InlineKeyboardMarkup(inline_keyboard=rows)


def _status_kb(lang="uz"):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ active", callback_data="adm:status:active")],
        [InlineKeyboardButton(text="⏸ inactive", callback_data="adm:status:inactive")],
        [InlineKeyboardButton(text="⛔ blocked", callback_data="adm:status:blocked")],
        [InlineKeyboardButton(text=t("admin.cancel", lang), callback_data="adm:cancel")],
    ])


def _manual_points_kb(lang="uz"):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="+1", callback_data="adm:mp:1"),
         InlineKeyboardButton(text="+5", callback_data="adm:mp:5"),
         InlineKeyboardButton(text="+10", callback_data="adm:mp:10")],
        [InlineKeyboardButton(text="-1", callback_data="adm:mp:-1"),
         InlineKeyboardButton(text="-5", callback_data="adm:mp:-5"),
         InlineKeyboardButton(text="-10", callback_data="adm:mp:-10")],
        [InlineKeyboardButton(text=t("admin.cancel", lang), callback_data="adm:cancel")],
    ])


def _medal(rank: int) -> str:
    return {1: "🥇", 2: "🥈", 3: "🥉"}.get(rank, f"{rank}.")


async def _restore_admin_kb(message: Message, user_id: int, lang: str = "uz"):
    admin = _get_admin_info(user_id)
    if not admin:
        return
    await message.answer(t("admin.panel.title", lang), reply_markup=_admin_keyboard(lang, admin.get("role_code", "ga")))


@router.callback_query(F.data == "adm:cancel")
async def cb_cancel(cb: CallbackQuery, state: FSMContext, lang: str, **kwargs):
    await state.clear()
    try:
        await cb.message.edit_reply_markup(reply_markup=None)
    except Exception:
        pass
    await _restore_admin_kb(cb.message, cb.from_user.id, lang)
    await cb.answer(t("admin.cancelled", lang))


@router.callback_query(F.data == "noop")
async def cb_noop(cb: CallbackQuery, **kwargs):
    await cb.answer()


@router.message(_admin_text_any("admin.cancel"))
async def text_cancel(message: Message, state: FSMContext, lang: str, **kwargs):
    await state.clear()
    await _restore_admin_kb(message, message.from_user.id, lang)


@router.message(F.text.in_({"/admin", admin_panel_text("uz"), admin_panel_text("ru"), admin_panel_text("en"), admin_panel_text("kg"), admin_panel_text("az")}))
async def cmd_admin(message: Message, state: FSMContext, lang: str, **kwargs):
    await state.clear()
    admin = _get_admin_info(message.from_user.id)
    if not admin:
        await message.answer(t("admin.no_permission", lang))
        return
    await message.answer(t("admin.panel.title", lang), reply_markup=_admin_keyboard(lang, admin.get("role_code", "ga")))


@router.message(_admin_text("admin.menu.back_employee"))
async def back_to_employee(message: Message, state: FSMContext, employee: dict, lang: str, **kwargs):
    await state.clear()
    await message.answer(t("menu.main", lang), reply_markup=main_menu_keyboard(lang, is_admin=is_admin(message.from_user.id)))


@router.message(_admin_text("admin.menu.language"))
async def admin_change_lang(message: Message, lang: str, **kwargs):
    await message.answer(t("admin.language.choose", lang), reply_markup=lang_select_keyboard())


@router.message(_admin_text("admin.menu.stats"))
async def admin_stats(message: Message, lang: str, **kwargs):
    admin = _get_admin_info(message.from_user.id)
    if not admin:
        return
    stats = get_system_stats()
    country_lines = "\n".join(f"  {cc}: {s['active']}/{s['employees']}" for cc, s in stats.get("country_stats", {}).items())
    text = "\n".join([
        t("admin.stats.title", lang),
        "",
        t("admin.stats.employees", lang).format(active=stats["employees_active"], total=stats["employees_total"]),
        t("admin.stats.admins", lang).format(total=stats["admins_total"]),
        t("admin.stats.events", lang).format(active=stats["events_active"], total=stats["events_total"]),
        "",
        t("admin.stats.scans", lang).format(total=stats["scans_total"]),
        t("admin.stats.unique", lang).format(total=stats["unique_awards"]),
        t("admin.stats.duplicate", lang).format(total=stats["duplicate_scans"]),
        t("admin.stats.suspicious", lang).format(total=stats.get("suspicious_scans", 0)),
        t("admin.stats.points", lang).format(total=stats["points_total"]),
        "",
        t("admin.stats.countries", lang),
        country_lines,
    ])
    await message.answer(text, parse_mode="HTML")


@router.message(_admin_text("admin.menu.employees"))
async def admin_employees(message: Message, lang: str, **kwargs):
    admin = _get_admin_info(message.from_user.id)
    if not admin:
        return
    employees = get_all_employees()
    if not employees:
        await message.answer(t("admin.employees.empty", lang))
        return
    active = [e for e in employees if e.get("status") == "active"]
    text = t("admin.employees.title", lang).format(active=len(active), total=len(employees)) + "\n\n"
    for e in employees[:30]:
        icon = "✅" if e.get("status") == "active" else "⏸" if e.get("status") == "inactive" else "⛔"
        text += f"{icon} <code>{e.get('employee_code')}</code> — {e.get('full_name')} ({e.get('country_code')})\n"
    if len(employees) > 30:
        text += f"\n... +{len(employees)-30}"
    await message.answer(text, parse_mode="HTML")


@router.message(_admin_text("admin.menu.events"))
async def admin_events(message: Message, lang: str, **kwargs):
    admin = _get_admin_info(message.from_user.id)
    if not admin:
        return
    events = get_all_events()
    if not events:
        await message.answer(t("admin.events.empty", lang))
        return
    status_map = {"draft": "📝", "active": "▶️", "paused": "⏸", "finished": "🏁"}
    for ev in events[:15]:
        icon = status_map.get(ev.get("status"), "❓")
        pool = ev.get("reward_pool_amount", "")
        pool_text = f"\n💰 {pool} {ev.get('reward_pool_currency', '')}" if pool else ""
        text = (
            f"{icon} <b>{ev.get('event_name')}</b>\n"
            f"🆔 <code>{ev.get('event_id')}</code>\n"
            f"📌 {ev.get('status')}\n"
            f"📅 {ev.get('start_at', '')} — {ev.get('end_at', '')}"
            f"{pool_text}"
        )
        await message.answer(text, parse_mode="HTML", reply_markup=_event_actions_kb(ev.get("event_id", ""), ev.get("status", ""), lang))


@router.callback_query(F.data.startswith("adm:evtact:"))
async def cb_event_action(cb: CallbackQuery, lang: str, **kwargs):
    admin = _get_admin_info(cb.from_user.id)
    if not admin:
        await cb.answer(t("admin.no_permission", lang), show_alert=True)
        return
    _, _, action, event_id = cb.data.split(":", 3)
    status_map = {"activate": "active", "pause": "paused", "finish": "finished"}
    new_status = status_map.get(action)
    if not new_status:
        await cb.answer(t("generic.error", lang), show_alert=True)
        return
    try:
        set_event_status(event_id, new_status)
    except Exception as e:
        await cb.answer(str(e)[:180], show_alert=True)
        return
    if new_status == "active":
        event = get_event_by_id(event_id)
        if event:
            countries = get_event_countries(event_id)
            employees = get_all_employees()
            target_emps = [e for e in employees if e.get("status") == "active" and e.get("country_code", "").upper() in [c.upper() for c in countries]]
            rewards = get_event_rewards(event_id)
            asyncio.create_task(notify_event_started(target_emps, event, rewards))
    try:
        await cb.message.edit_reply_markup(reply_markup=_event_actions_kb(event_id, new_status, lang))
    except Exception:
        pass
    await cb.answer(t("admin.event.status_changed", lang).format(status=new_status))


@router.callback_query(F.data.startswith("adm:evtlb:"))
async def cb_event_leaderboard(cb: CallbackQuery, lang: str, **kwargs):
    event_id = cb.data.split(":")[2]
    lb = build_leaderboard(event_id=event_id, top_n=20)
    if not lb:
        await cb.answer(t("admin.leaderboard.empty", lang), show_alert=True)
        return
    lines = [f"{_medal(e['rank'])} {e['full_name']} ({e['country_code']}) — <b>{e['points']}</b>" for e in lb]
    await cb.message.answer(t("admin.events.title", lang) + "\n\n" + "\n".join(lines), parse_mode="HTML")
    await cb.answer()


@router.message(_admin_text("admin.menu.create_event"))
async def admin_create_event(message: Message, state: FSMContext, lang: str, **kwargs):
    admin = _get_admin_info(message.from_user.id)
    if not admin:
        return
    await state.clear()
    await state.set_state(EventCreateStates.name)
    await state.update_data(admin_id=admin.get("admin_id", ""))
    await message.answer(t("admin.event.name_prompt", lang), reply_markup=_cancel_reply_kb(lang))


@router.message(EventCreateStates.name)
async def evt_name(message: Message, state: FSMContext, lang: str, **kwargs):
    name = (message.text or "").strip()
    if len(name) < 2:
        await message.answer(t("admin.event.name_short", lang))
        return
    await state.update_data(event_name=name)
    await state.set_state(EventCreateStates.description)
    await message.answer(t("admin.event.description_prompt", lang), reply_markup=_cancel_reply_kb(lang))


@router.message(EventCreateStates.description)
async def evt_description(message: Message, state: FSMContext, lang: str, **kwargs):
    await state.update_data(description=(message.text or "").strip())
    await state.set_state(EventCreateStates.rules)
    await message.answer(t("admin.event.rules_prompt", lang), reply_markup=_cancel_reply_kb(lang))


@router.message(EventCreateStates.rules)
async def evt_rules(message: Message, state: FSMContext, lang: str, **kwargs):
    await state.update_data(rules_text=(message.text or "").strip())
    await state.set_state(EventCreateStates.countries)
    await state.update_data(selected_countries=[])
    await message.answer(t("admin.event.countries_prompt", lang), reply_markup=_countries_kb(set(), lang))


@router.callback_query(F.data.startswith("adm:evt:ctry:"), EventCreateStates.countries)
async def evt_country_toggle(cb: CallbackQuery, state: FSMContext, lang: str, **kwargs):
    code = cb.data.split(":")[3]
    data = await state.get_data()
    selected = set(data.get("selected_countries", []))
    if code == "done":
        if not selected:
            await cb.answer(t("admin.event.select_one_country", lang), show_alert=True)
            return
        await state.update_data(selected_countries=list(selected))
        await state.set_state(EventCreateStates.start_date)
        now = datetime.utcnow()
        await cb.message.edit_text(t("admin.event.start_date", lang), reply_markup=_calendar_kb(now.year, now.month, "start", lang))
        await cb.answer()
        return
    if code in selected:
        selected.discard(code)
    else:
        selected.add(code)
    await state.update_data(selected_countries=list(selected))
    await cb.message.edit_reply_markup(reply_markup=_countries_kb(selected, lang))
    await cb.answer()


@router.callback_query(F.data.startswith("adm:calnav:"))
async def cal_nav(cb: CallbackQuery, lang: str, **kwargs):
    _, _, prefix, ym = cb.data.split(":", 3)
    year, month = map(int, ym.split("-"))
    await cb.message.edit_reply_markup(reply_markup=_calendar_kb(year, month, prefix, lang))
    await cb.answer()


@router.callback_query(F.data.startswith("adm:cal:start:"), EventCreateStates.start_date)
async def evt_start_date(cb: CallbackQuery, state: FSMContext, lang: str, **kwargs):
    date_str = cb.data.split(":")[3]
    await state.update_data(start_date=date_str)
    await state.set_state(EventCreateStates.start_hour)
    await cb.message.edit_text(t("admin.event.start_hour", lang).format(date=date_str), reply_markup=_hours_kb("start", lang))
    await cb.answer()


@router.callback_query(F.data.startswith("adm:hour:start:"), EventCreateStates.start_hour)
async def evt_start_hour(cb: CallbackQuery, state: FSMContext, lang: str, **kwargs):
    await state.update_data(start_hour=cb.data.split(":")[3])
    await state.set_state(EventCreateStates.end_date)
    now = datetime.utcnow()
    await cb.message.edit_text(t("admin.event.end_date", lang), reply_markup=_calendar_kb(now.year, now.month, "end", lang))
    await cb.answer()


@router.callback_query(F.data.startswith("adm:cal:end:"), EventCreateStates.end_date)
async def evt_end_date(cb: CallbackQuery, state: FSMContext, lang: str, **kwargs):
    date_str = cb.data.split(":")[3]
    await state.update_data(end_date=date_str)
    await state.set_state(EventCreateStates.end_hour)
    await cb.message.edit_text(t("admin.event.end_hour", lang).format(date=date_str), reply_markup=_hours_kb("end", lang))
    await cb.answer()


@router.callback_query(F.data.startswith("adm:hour:end:"), EventCreateStates.end_hour)
async def evt_end_hour(cb: CallbackQuery, state: FSMContext, lang: str, **kwargs):
    await state.update_data(end_hour=cb.data.split(":")[3])
    await state.set_state(EventCreateStates.reward_pool_amount)
    await cb.message.edit_text(t("admin.event.pool_prompt", lang), reply_markup=_pool_amount_kb(lang))
    await cb.answer()


@router.callback_query(F.data.startswith("adm:pool:"), EventCreateStates.reward_pool_amount)
async def evt_pool_amount(cb: CallbackQuery, state: FSMContext, lang: str, **kwargs):
    amount = cb.data.split(":")[2]
    await state.update_data(reward_pool_amount=amount)
    if amount == "0":
        await state.update_data(reward_pool_currency="")
        await state.set_state(EventCreateStates.reward_count)
        await cb.message.edit_text(t("admin.event.reward_count_prompt", lang), reply_markup=_reward_count_kb(lang))
    else:
        await state.set_state(EventCreateStates.reward_pool_currency)
        await cb.message.edit_text(t("admin.event.currency_prompt", lang).format(amount=f"{int(amount):,}"), reply_markup=_currency_kb(lang))
    await cb.answer()


@router.callback_query(F.data.startswith("adm:currency:"), EventCreateStates.reward_pool_currency)
async def evt_pool_currency(cb: CallbackQuery, state: FSMContext, lang: str, **kwargs):
    await state.update_data(reward_pool_currency=cb.data.split(":")[2])
    await state.set_state(EventCreateStates.reward_count)
    await cb.message.edit_text(t("admin.event.reward_count_prompt", lang), reply_markup=_reward_count_kb(lang))
    await cb.answer()


@router.callback_query(F.data.startswith("adm:rwdcnt:"), EventCreateStates.reward_count)
async def evt_reward_count(cb: CallbackQuery, state: FSMContext, lang: str, **kwargs):
    count = int(cb.data.split(":")[2])
    if count == 0:
        await state.update_data(rewards=[], reward_places=0, current_place=0)
        await state.set_state(EventCreateStates.confirm)
        await _show_confirm(cb, state, lang)
        return
    await state.update_data(reward_places=count, current_place=1, rewards=[])
    await state.set_state(EventCreateStates.reward_place_amount)
    data = await state.get_data()
    currency = data.get("reward_pool_currency", "UZS") or "UZS"
    await cb.message.edit_text(t("admin.event.reward_place_prompt", lang).format(place=1, currency=currency), parse_mode="HTML")
    await cb.answer()


@router.message(EventCreateStates.reward_place_amount)
async def evt_place_amount(message: Message, state: FSMContext, lang: str, **kwargs):
    text = (message.text or "").strip().replace(",", "").replace(" ", "")
    if not text.lstrip("-").isdigit():
        await message.answer(t("admin.only_number", lang))
        return
    amount = text
    data = await state.get_data()
    current_place = int(data.get("current_place", 1))
    total_places = int(data.get("reward_places", 3))
    currency = data.get("reward_pool_currency", "UZS") or "UZS"
    rewards = list(data.get("rewards", []))
    rewards.append({
        "place_number": current_place,
        "reward_title": f"{current_place}-place",
        "reward_amount": amount,
        "currency_code": currency,
    })
    next_place = current_place + 1
    if next_place > total_places:
        await state.update_data(rewards=rewards, current_place=next_place)
        await state.set_state(EventCreateStates.confirm)
        await _show_confirm_msg(message, state, lang)
        return
    await state.update_data(rewards=rewards, current_place=next_place)
    await message.answer(t("admin.event.reward_place_prompt", lang).format(place=next_place, currency=currency), parse_mode="HTML")


async def _show_confirm(cb: CallbackQuery, state: FSMContext, lang: str):
    text = _build_confirm_text(await state.get_data(), lang)
    await cb.message.edit_text(text, parse_mode="HTML", reply_markup=_confirm_event_kb(lang))
    await cb.answer()


async def _show_confirm_msg(message: Message, state: FSMContext, lang: str):
    text = _build_confirm_text(await state.get_data(), lang)
    await message.answer(text, parse_mode="HTML", reply_markup=_confirm_event_kb(lang))


def _build_confirm_text(data: dict, lang: str) -> str:
    lines = [
        t("admin.event.confirm_title", lang),
        "",
        t("admin.event.confirm_name", lang).format(value=data.get("event_name", "")),
        t("admin.event.confirm_description", lang).format(value=data.get("description", "")),
        t("admin.event.confirm_rules", lang).format(value=data.get("rules_text", "")),
        t("admin.event.confirm_countries", lang).format(value=", ".join(data.get("selected_countries", []))),
        t("admin.event.confirm_dates", lang).format(
            start=f"{data.get('start_date')} {data.get('start_hour')}:00",
            end=f"{data.get('end_date')} {data.get('end_hour')}:00",
        ),
    ]
    pool_amount = data.get("reward_pool_amount", "0")
    if pool_amount and pool_amount != "0":
        lines.append(t("admin.event.confirm_pool", lang).format(amount=f"{int(pool_amount):,}", currency=data.get("reward_pool_currency", "")))
    rewards = data.get("rewards", [])
    if rewards:
        lines.append(t("admin.event.confirm_rewards", lang))
        lines.extend([f"  {r['place_number']}. {r.get('reward_amount', '0')} {r.get('currency_code', '')}" for r in rewards])
    lines.extend(["", t("admin.event.confirm_ask", lang)])
    return "\n".join(lines)


@router.callback_query(F.data == "adm:event:save", EventCreateStates.confirm)
async def evt_save(cb: CallbackQuery, state: FSMContext, lang: str, **kwargs):
    data = await state.get_data()
    start_at = f"{data['start_date']} {data['start_hour']}:00"
    end_at = f"{data['end_date']} {data['end_hour']}:00"
    try:
        event = create_event(
            event_name=data["event_name"],
            description=data.get("description", ""),
            start_at=start_at,
            end_at=end_at,
            rules_text=data.get("rules_text", ""),
            country_codes=data.get("selected_countries", []),
            rewards=data.get("rewards", []),
            created_by_admin_id=data.get("admin_id", ""),
            reward_pool_amount=data.get("reward_pool_amount", ""),
            reward_pool_currency=data.get("reward_pool_currency", ""),
        )
        event_id = event.get("event_id", "")

        # Publish immediately and send participation request to matching employees
        set_event_status(event_id, "active")
        event = get_event_by_id(event_id) or event
        countries = get_event_countries(event_id)
        employees = get_all_employees()
        target_emps = [
            e for e in employees
            if e.get("status") == "active" and e.get("country_code", "").upper() in [c.upper() for c in countries]
        ]
        rewards = get_event_rewards(event_id)
        if target_emps:
            asyncio.create_task(notify_event_started(target_emps, event, rewards))

        success_text = t("admin.event.created", lang).format(event_id=event_id).replace("draft", "active")
        await cb.message.edit_text(success_text, parse_mode="HTML", reply_markup=_event_actions_kb(event_id, "active", lang))
    except Exception as e:
        logger.exception("Event creation failed")
        await cb.message.edit_text(f"❌ {e}")
    await state.clear()
    await cb.answer()


@router.message(_admin_text("admin.menu.leaderboard"))
async def admin_leaderboard(message: Message, lang: str, **kwargs):
    admin = _get_admin_info(message.from_user.id)
    if not admin:
        return
    await message.answer(t("admin.event.choose_country", lang), reply_markup=_leaderboard_country_kb())


@router.callback_query(F.data.startswith("adm:lb:"))
async def cb_leaderboard(cb: CallbackQuery, lang: str, **kwargs):
    code = cb.data.split(":")[2]
    country = None if code == "all" else code
    lb = build_leaderboard(country_code=country, top_n=20)
    if not lb:
        await cb.answer(t("admin.leaderboard.empty", lang), show_alert=True)
        return
    title = f"🌍 {code}" if code != "all" else "🌍 ALL"
    lines = [f"{_medal(e['rank'])} {e['full_name']} ({e['country_code']}) — <b>{e['points']}</b>" for e in lb]
    await cb.message.answer(f"🥇 <b>{title}</b>\n\n" + "\n".join(lines), parse_mode="HTML")
    await cb.answer()


@router.message(_admin_text("admin.menu.manual_points"))
async def admin_manual_points(message: Message, state: FSMContext, lang: str, **kwargs):
    admin = _get_admin_info(message.from_user.id)
    if not admin:
        return
    await state.clear()
    await state.set_state(ManualPointsStates.employee_code)
    await state.update_data(admin_id=admin.get("admin_id", ""))
    await message.answer(t("admin.manual_points.enter_code", lang), reply_markup=_cancel_reply_kb(lang))


@router.message(ManualPointsStates.employee_code)
async def mp_employee_code(message: Message, state: FSMContext, lang: str, **kwargs):
    code = (message.text or "").strip().upper()
    emp = get_employee_by_code(code)
    if not emp:
        await message.answer(t("admin.employee.not_found", lang).format(code=code))
        return
    await state.update_data(mp_employee_id=emp["employee_id"], mp_employee_code=emp["employee_code"], mp_country=emp.get("country_code", ""))
    await message.answer(t("admin.manual_points.choose_amount", lang).format(name=emp["full_name"], code=emp["employee_code"]), reply_markup=_manual_points_kb(lang))


@router.callback_query(F.data.startswith("adm:mp:"))
async def cb_manual_points(cb: CallbackQuery, state: FSMContext, lang: str, **kwargs):
    data = await state.get_data()
    emp_id = data.get("mp_employee_id")
    if not emp_id:
        await cb.answer(t("generic.error", lang), show_alert=True)
        await state.clear()
        return
    points = int(cb.data.split(":")[2])
    reason = "manual_bonus" if points > 0 else "manual_penalty"
    try:
        manual_adjust(employee_id=emp_id, employee_code=data.get("mp_employee_code", ""), points_delta=points, reason_code=reason, admin_id=data.get("admin_id", ""), country_code=data.get("mp_country", ""))
        try:
            await cb.message.edit_reply_markup(reply_markup=None)
        except Exception:
            pass
        await cb.message.answer(t("admin.manual_points.done", lang).format(code=data.get("mp_employee_code", ""), points=points))
    except Exception as e:
        await cb.message.answer(f"❌ {e}")
    await state.clear()
    await _restore_admin_kb(cb.message, cb.from_user.id, lang)
    await cb.answer()


@router.message(_admin_text("admin.menu.employee_status"))
async def admin_emp_status(message: Message, state: FSMContext, lang: str, **kwargs):
    admin = _get_admin_info(message.from_user.id)
    if not admin:
        return
    await state.clear()
    await state.set_state(EmployeeStatusStates.employee_code)
    await message.answer(t("admin.employee_status.enter_code", lang), reply_markup=_cancel_reply_kb(lang))


@router.message(EmployeeStatusStates.employee_code)
async def es_employee_code(message: Message, state: FSMContext, lang: str, **kwargs):
    code = (message.text or "").strip().upper()
    emp = get_employee_by_code(code)
    if not emp:
        await message.answer(t("admin.employee.not_found", lang).format(code=code))
        return
    await state.update_data(es_employee_id=emp["employee_id"], es_employee_code=emp["employee_code"])
    await message.answer(t("admin.employee_status.choose", lang).format(name=emp["full_name"], code=emp["employee_code"], status=emp.get("status", "")), reply_markup=_status_kb(lang))


@router.callback_query(F.data.startswith("adm:status:"))
async def cb_set_status(cb: CallbackQuery, state: FSMContext, lang: str, **kwargs):
    data = await state.get_data()
    emp_id = data.get("es_employee_id")
    if not emp_id:
        await cb.answer(t("generic.error", lang), show_alert=True)
        await state.clear()
        return
    new_status = cb.data.split(":")[2]
    update_employee_status(emp_id, new_status)
    try:
        await cb.message.edit_reply_markup(reply_markup=None)
    except Exception:
        pass
    await cb.message.answer(t("admin.employee_status.done", lang).format(code=data.get("es_employee_code", ""), status=new_status))
    await state.clear()
    await _restore_admin_kb(cb.message, cb.from_user.id, lang)
    await cb.answer()


@router.message(_admin_text("admin.menu.add_admin"))
async def admin_add_admin(message: Message, state: FSMContext, lang: str, **kwargs):
    if not is_super_admin(message.from_user.id):
        await message.answer(t("admin.super_admin_only", lang))
        return
    await state.clear()
    await state.set_state(AddAdminStates.tg_id)
    await message.answer(t("admin.add_admin.enter_tg", lang), reply_markup=_cancel_reply_kb(lang))


@router.message(AddAdminStates.tg_id)
async def aa_tg_id(message: Message, state: FSMContext, lang: str, **kwargs):
    tg_id = (message.text or "").strip()
    if not tg_id.isdigit():
        await message.answer(t("admin.add_admin.only_digits", lang))
        return
    await state.update_data(new_admin_tg_id=tg_id)
    await state.set_state(AddAdminStates.full_name)
    await message.answer(t("admin.add_admin.enter_name", lang), reply_markup=_cancel_reply_kb(lang))


@router.message(AddAdminStates.full_name)
async def aa_name(message: Message, state: FSMContext, lang: str, **kwargs):
    data = await state.get_data()
    name = (message.text or "").strip()
    try:
        admin = create_admin(telegram_user_id=data["new_admin_tg_id"], full_name=name, phone="", role_code="ga", created_by=str(message.from_user.id))
        await message.answer(t("admin.add_admin.done", lang).format(admin_id=admin.get("admin_id"), name=name))
    except Exception as e:
        await message.answer(f"❌ {e}")
    await state.clear()
    await _restore_admin_kb(message, message.from_user.id, lang)


@router.callback_query(F.data.startswith("web:approve:"))
async def cb_web_approve(cb: CallbackQuery, lang: str, **kwargs):
    admin = _get_admin_info(cb.from_user.id)
    if not admin:
        await cb.answer(t("admin.no_permission", lang), show_alert=True)
        return
    request_id = cb.data.split(":", 2)[2]
    approved = approve_request(request_id, str(cb.from_user.id))
    if not approved:
        await cb.answer(t("admin.web.approve_missing", lang), show_alert=True)
        return
    try:
        await cb.message.edit_reply_markup(reply_markup=None)
    except Exception:
        pass
    await cb.answer(t("admin.web.approved", lang), show_alert=True)
