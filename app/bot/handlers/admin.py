"""
Admin / GA bot interface.
Fully button-based. Event creation with reward pool.
Event activate triggers notifications.
"""
import asyncio
import calendar
import logging
from datetime import datetime, timedelta

from aiogram import Router, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import (
    Message, CallbackQuery, ReplyKeyboardMarkup, KeyboardButton,
    InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardRemove,
)

from app.bot.keyboards.main_keyboards import ADMIN_PANEL_TEXT, main_menu_keyboard
from app.bot.texts.translations import t
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

logger = logging.getLogger(__name__)
router = Router()

COUNTRY_LABELS = {"UZ": "🇺🇿 UZ", "RU": "🇷🇺 RU", "KG": "🇰🇬 KG", "AZ": "🇦🇿 AZ"}
CURRENCY_LIST = ["UZS", "USD", "EUR", "RUB", "KGS", "AZN"]


class EventCreateStates(StatesGroup):
    name = State()
    countries = State()
    start_date = State()
    start_hour = State()
    end_date = State()
    end_hour = State()
    reward_pool_amount = State()
    reward_pool_currency = State()
    reward_template = State()
    confirm = State()


class ManualPointsStates(StatesGroup):
    employee_code = State()

class EmployeeStatusStates(StatesGroup):
    employee_code = State()

class AddAdminStates(StatesGroup):
    tg_id = State()
    full_name = State()

class LeaderboardStates(StatesGroup):
    choose_country = State()


# ── Admin keyboards ──────────────────────────────────────────────────────────

def _admin_keyboard(lang, role):
    rows = [
        [KeyboardButton(text="🏆 Eventlar"), KeyboardButton(text="➕ Yangi event")],
        [KeyboardButton(text="👥 Xodimlar"), KeyboardButton(text="🥇 Reyting")],
        [KeyboardButton(text="💰 Ball berish"), KeyboardButton(text="🔒 Xodim statusi")],
        [KeyboardButton(text="📊 Statistika")],
    ]
    if role == "super_admin":
        rows.append([KeyboardButton(text="➕ GA/Admin qo'shish")])
    rows.append([KeyboardButton(text="⬅️ Xodim menyusi")])
    return ReplyKeyboardMarkup(keyboard=rows, resize_keyboard=True)


def _cancel_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="❌ Bekor qilish", callback_data="adm:cancel")]
    ])


def _countries_kb(selected):
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
    rows.append([InlineKeyboardButton(text="✅ Davom etish", callback_data="adm:evt:ctry:done")])
    rows.append([InlineKeyboardButton(text="❌ Bekor", callback_data="adm:cancel")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def _hours_kb(prefix):
    rows = []
    row = []
    for h in range(0, 24):
        row.append(InlineKeyboardButton(text=f"{h:02d}:00", callback_data=f"adm:hour:{prefix}:{h:02d}"))
        if len(row) == 4:
            rows.append(row)
            row = []
    if row:
        rows.append(row)
    rows.append([InlineKeyboardButton(text="❌ Bekor", callback_data="adm:cancel")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def _calendar_kb(year, month, prefix):
    rows = []
    rows.append([InlineKeyboardButton(text=f"{calendar.month_name[month]} {year}", callback_data="noop")])
    header = [InlineKeyboardButton(text=d, callback_data="noop") for d in ["Du", "Se", "Ch", "Pa", "Ju", "Sh", "Ya"]]
    rows.append(header)
    cal = calendar.monthcalendar(year, month)
    for week in cal:
        row = []
        for day in week:
            if day == 0:
                row.append(InlineKeyboardButton(text=" ", callback_data="noop"))
            else:
                row.append(InlineKeyboardButton(text=str(day), callback_data=f"adm:cal:{prefix}:{year}-{month:02d}-{day:02d}"))
        rows.append(row)
    nav = []
    prev_m = month - 1 if month > 1 else 12
    prev_y = year if month > 1 else year - 1
    next_m = month + 1 if month < 12 else 1
    next_y = year if month < 12 else year + 1
    nav.append(InlineKeyboardButton(text="◀️", callback_data=f"adm:calnav:{prefix}:{prev_y}-{prev_m:02d}"))
    nav.append(InlineKeyboardButton(text="▶️", callback_data=f"adm:calnav:{prefix}:{next_y}-{next_m:02d}"))
    rows.append(nav)
    rows.append([InlineKeyboardButton(text="❌ Bekor", callback_data="adm:cancel")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def _pool_amount_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Yo'q (0)", callback_data="adm:pool:0"),
         InlineKeyboardButton(text="500 000", callback_data="adm:pool:500000")],
        [InlineKeyboardButton(text="1 000 000", callback_data="adm:pool:1000000"),
         InlineKeyboardButton(text="2 000 000", callback_data="adm:pool:2000000")],
        [InlineKeyboardButton(text="5 000 000", callback_data="adm:pool:5000000"),
         InlineKeyboardButton(text="10 000 000", callback_data="adm:pool:10000000")],
        [InlineKeyboardButton(text="❌ Bekor", callback_data="adm:cancel")],
    ])


def _currency_kb():
    rows = []
    row = []
    for c in CURRENCY_LIST:
        row.append(InlineKeyboardButton(text=c, callback_data=f"adm:currency:{c}"))
        if len(row) == 3:
            rows.append(row)
            row = []
    if row:
        rows.append(row)
    rows.append([InlineKeyboardButton(text="❌ Bekor", callback_data="adm:cancel")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def _reward_template_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Mukofot yo'q", callback_data="adm:reward:none")],
        [InlineKeyboardButton(text="Top 3", callback_data="adm:reward:top3")],
        [InlineKeyboardButton(text="Top 5", callback_data="adm:reward:top5")],
        [InlineKeyboardButton(text="❌ Bekor", callback_data="adm:cancel")],
    ])


def _confirm_event_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Yaratish", callback_data="adm:event:save")],
        [InlineKeyboardButton(text="❌ Bekor", callback_data="adm:cancel")],
    ])


def _status_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ active", callback_data="adm:status:active")],
        [InlineKeyboardButton(text="⏸ inactive", callback_data="adm:status:inactive")],
        [InlineKeyboardButton(text="⛔ blocked", callback_data="adm:status:blocked")],
        [InlineKeyboardButton(text="❌ Bekor", callback_data="adm:cancel")],
    ])


def _manual_points_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="+1", callback_data="adm:mp:1"),
         InlineKeyboardButton(text="+5", callback_data="adm:mp:5"),
         InlineKeyboardButton(text="+10", callback_data="adm:mp:10")],
        [InlineKeyboardButton(text="-1", callback_data="adm:mp:-1"),
         InlineKeyboardButton(text="-5", callback_data="adm:mp:-5"),
         InlineKeyboardButton(text="-10", callback_data="adm:mp:-10")],
        [InlineKeyboardButton(text="❌ Bekor", callback_data="adm:cancel")],
    ])


def _event_actions_kb(event_id, status):
    buttons = []
    if status == "draft":
        buttons.append([InlineKeyboardButton(text="▶️ Boshlash (active)", callback_data=f"adm:evtact:activate:{event_id}")])
    elif status == "active":
        buttons.append([InlineKeyboardButton(text="⏸ Pauza", callback_data=f"adm:evtact:pause:{event_id}")])
        buttons.append([InlineKeyboardButton(text="🏁 Tugatish", callback_data=f"adm:evtact:finish:{event_id}")])
    elif status == "paused":
        buttons.append([InlineKeyboardButton(text="▶️ Davom", callback_data=f"adm:evtact:activate:{event_id}")])
        buttons.append([InlineKeyboardButton(text="🏁 Tugatish", callback_data=f"adm:evtact:finish:{event_id}")])
    buttons.append([InlineKeyboardButton(text="🥇 Reyting", callback_data=f"adm:evtlb:{event_id}")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def _leaderboard_country_kb():
    rows = [[InlineKeyboardButton(text="🌍 Hammasi", callback_data="adm:lb:all")]]
    row = []
    for code in ["UZ", "RU", "KG", "AZ"]:
        row.append(InlineKeyboardButton(text=COUNTRY_LABELS[code], callback_data=f"adm:lb:{code}"))
        if len(row) == 2:
            rows.append(row)
            row = []
    if row:
        rows.append(row)
    return InlineKeyboardMarkup(inline_keyboard=rows)


# ── Handlers ─────────────────────────────────────────────────────────────────

def _get_admin_info(user_id):
    admin = get_admin_by_telegram_id(user_id)
    return admin if admin and admin.get("status") == "active" else None


@router.message(F.text.in_({ADMIN_PANEL_TEXT, "/admin"}))
async def cmd_admin(message: Message, state: FSMContext, lang: str, **kwargs):
    await state.clear()
    admin = _get_admin_info(message.from_user.id)
    if not admin:
        await message.answer("⛔ Sizda admin huquqi yo'q.")
        return
    role = admin.get("role_code", "ga")
    await message.answer("👑 Admin panel", reply_markup=_admin_keyboard(lang, role))


@router.message(F.text == "⬅️ Xodim menyusi")
async def back_to_employee(message: Message, state: FSMContext, employee: dict, lang: str):
    await state.clear()
    await message.answer(t("menu.main", lang),
                         reply_markup=main_menu_keyboard(lang, is_admin=is_admin(message.from_user.id)))


@router.callback_query(F.data == "adm:cancel")
async def cb_cancel(cb: CallbackQuery, state: FSMContext, lang: str, **kwargs):
    await state.clear()
    await cb.message.edit_reply_markup(reply_markup=None)
    await cb.message.answer("❌ Bekor qilindi.")
    await cb.answer()


# ── System stats ─────────────────────────────────────────────────────────────

@router.message(F.text == "📊 Statistika")
async def admin_stats(message: Message, lang: str, **kwargs):
    admin = _get_admin_info(message.from_user.id)
    if not admin:
        return
    stats = get_system_stats()
    country_lines = "\n".join(f"  {cc}: {s['active']}/{s['employees']}" for cc, s in stats.get("country_stats", {}).items())
    text = (
        f"📊 <b>Tizim statistikasi</b>\n\n"
        f"👥 Xodimlar: {stats['employees_active']}/{stats['employees_total']}\n"
        f"👑 Adminlar: {stats['admins_total']}\n"
        f"🏆 Eventlar: {stats['events_active']} faol / {stats['events_total']} jami\n\n"
        f"📱 Skanlar: {stats['scans_total']}\n"
        f"✅ Unique: {stats['unique_awards']}\n"
        f"🔁 Takror: {stats['duplicate_scans']}\n"
        f"⚠️ Shubhali: {stats['suspicious_scans']}\n"
        f"⭐ Jami ball: {stats['points_total']}\n\n"
        f"📱 Qurilmalar: {stats['devices_total']} (toza: {stats['devices_clean']}, shubhali: {stats['devices_suspicious']})\n\n"
        f"🌍 Mamlakat bo'yicha (faol/jami):\n{country_lines}"
    )
    await message.answer(text, parse_mode="HTML")


# ── Employees list ───────────────────────────────────────────────────────────

@router.message(F.text == "👥 Xodimlar")
async def admin_employees(message: Message, **kwargs):
    admin = _get_admin_info(message.from_user.id)
    if not admin:
        return
    employees = get_all_employees()
    if not employees:
        await message.answer("ℹ️ Xodimlar yo'q.")
        return
    active = [e for e in employees if e.get("status") == "active"]
    text = f"👥 <b>Xodimlar</b> ({len(active)} faol / {len(employees)} jami)\n\n"
    for e in employees[:30]:
        status_icon = "✅" if e.get("status") == "active" else "⏸" if e.get("status") == "inactive" else "⛔"
        text += f"{status_icon} <code>{e.get('employee_code')}</code> — {e.get('full_name')} ({e.get('country_code')})\n"
    if len(employees) > 30:
        text += f"\n... va yana {len(employees) - 30} ta"
    await message.answer(text, parse_mode="HTML")


# ── Events list ──────────────────────────────────────────────────────────────

@router.message(F.text == "🏆 Eventlar")
async def admin_events(message: Message, **kwargs):
    admin = _get_admin_info(message.from_user.id)
    if not admin:
        return
    events = get_all_events()
    if not events:
        await message.answer("ℹ️ Eventlar yo'q.")
        return
    for ev in events[:10]:
        status_map = {"draft": "📝", "active": "▶️", "paused": "⏸", "finished": "🏁"}
        icon = status_map.get(ev.get("status"), "❓")
        pool = ev.get("reward_pool_amount", "")
        pool_text = f"\n💰 Pul: {pool} {ev.get('reward_pool_currency', '')}" if pool else ""
        text = (f"{icon} <b>{ev.get('event_name')}</b>\n"
                f"🆔 <code>{ev.get('event_id')}</code>\n"
                f"📌 Status: {ev.get('status')}\n"
                f"📅 {ev.get('start_at', '')} — {ev.get('end_at', '')}"
                f"{pool_text}")
        await message.answer(text, parse_mode="HTML",
                             reply_markup=_event_actions_kb(ev["event_id"], ev.get("status", "")))


# ── Event actions ────────────────────────────────────────────────────────────

@router.callback_query(F.data.startswith("adm:evtact:"))
async def cb_event_action(cb: CallbackQuery, **kwargs):
    admin = _get_admin_info(cb.from_user.id)
    if not admin:
        await cb.answer("⛔ Ruxsat yo'q")
        return
    parts = cb.data.split(":")
    action = parts[2]
    event_id = parts[3]
    status_map = {"activate": "active", "pause": "paused", "finish": "finished"}
    new_status = status_map.get(action)
    if not new_status:
        await cb.answer("Noto'g'ri amal")
        return
    try:
        set_event_status(event_id, new_status)
    except Exception as e:
        await cb.answer(str(e), show_alert=True)
        return

    # If activating — send notifications!
    if new_status == "active":
        event = get_event_by_id(event_id)
        if event:
            countries = get_event_countries(event_id)
            employees = get_all_employees()
            target_employees = [e for e in employees
                                if e.get("status") == "active"
                                and e.get("country_code", "").upper() in [c.upper() for c in countries]]
            rewards = get_event_rewards(event_id)
            asyncio.create_task(notify_event_started(target_employees, event, rewards))

    await cb.message.edit_reply_markup(reply_markup=_event_actions_kb(event_id, new_status))
    await cb.answer(f"✅ Event {new_status}!")


@router.callback_query(F.data.startswith("adm:evtlb:"))
async def cb_event_leaderboard(cb: CallbackQuery, **kwargs):
    event_id = cb.data.split(":")[2]
    lb = build_leaderboard(event_id=event_id, top_n=20)
    if not lb:
        await cb.answer("Reyting bo'sh", show_alert=True)
        return
    medals = {1: "🥇", 2: "🥈", 3: "🥉"}
    lines = [f"{medals.get(e['rank'], str(e['rank'])+'.')} {e['full_name']} ({e['country_code']}) — <b>{e['points']}</b>"
             for e in lb]
    text = "🥇 <b>Event reytingi</b>\n\n" + "\n".join(lines)
    await cb.message.answer(text, parse_mode="HTML")
    await cb.answer()


# ── Create event ─────────────────────────────────────────────────────────────

@router.message(F.text == "➕ Yangi event")
async def admin_create_event(message: Message, state: FSMContext, **kwargs):
    admin = _get_admin_info(message.from_user.id)
    if not admin:
        return
    await state.set_state(EventCreateStates.name)
    await state.update_data(admin_id=admin.get("admin_id", ""))
    await message.answer("📝 Event nomini kiriting:", reply_markup=ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="❌ Bekor qilish")]], resize_keyboard=True))


@router.message(F.text == "❌ Bekor qilish")
async def text_cancel(message: Message, state: FSMContext, lang: str, **kwargs):
    current = await state.get_state()
    if current:
        await state.clear()
        admin = _get_admin_info(message.from_user.id)
        role = admin.get("role_code", "ga") if admin else "ga"
        await message.answer("❌ Bekor qilindi.", reply_markup=_admin_keyboard(lang, role))


@router.message(EventCreateStates.name)
async def evt_name(message: Message, state: FSMContext, **kwargs):
    if not message.text or len(message.text.strip()) < 2:
        await message.answer("Ism juda qisqa. Qayta kiriting:")
        return
    await state.update_data(event_name=message.text.strip())
    await state.set_state(EventCreateStates.countries)
    await state.update_data(selected_countries=set())
    await message.answer("🌍 Mamlakatlarni tanlang:", reply_markup=_countries_kb(set()))


@router.callback_query(F.data.startswith("adm:evt:ctry:"), EventCreateStates.countries)
async def evt_country_toggle(cb: CallbackQuery, state: FSMContext, **kwargs):
    code = cb.data.split(":")[3]
    data = await state.get_data()
    selected = set(data.get("selected_countries", []))
    if code == "done":
        if not selected:
            await cb.answer("Kamida 1 mamlakat tanlang!", show_alert=True)
            return
        await state.update_data(selected_countries=list(selected))
        await state.set_state(EventCreateStates.start_date)
        now = datetime.utcnow()
        await cb.message.edit_text("📅 Boshlanish sanasi:", reply_markup=_calendar_kb(now.year, now.month, "start"))
        await cb.answer()
        return
    if code in selected:
        selected.discard(code)
    else:
        selected.add(code)
    await state.update_data(selected_countries=list(selected))
    await cb.message.edit_reply_markup(reply_markup=_countries_kb(selected))
    await cb.answer()


@router.callback_query(F.data.startswith("adm:calnav:"))
async def cal_nav(cb: CallbackQuery, state: FSMContext, **kwargs):
    parts = cb.data.split(":")
    prefix = parts[2]
    ym = parts[3].split("-")
    year, month = int(ym[0]), int(ym[1])
    await cb.message.edit_reply_markup(reply_markup=_calendar_kb(year, month, prefix))
    await cb.answer()


@router.callback_query(F.data.startswith("adm:cal:start:"), EventCreateStates.start_date)
async def evt_start_date(cb: CallbackQuery, state: FSMContext, **kwargs):
    date_str = cb.data.split(":")[3]
    await state.update_data(start_date=date_str)
    await state.set_state(EventCreateStates.start_hour)
    await cb.message.edit_text(f"📅 Boshlanish: {date_str}\n⏰ Soatni tanlang:", reply_markup=_hours_kb("start"))
    await cb.answer()


@router.callback_query(F.data.startswith("adm:hour:start:"), EventCreateStates.start_hour)
async def evt_start_hour(cb: CallbackQuery, state: FSMContext, **kwargs):
    hour = cb.data.split(":")[3]
    await state.update_data(start_hour=hour)
    await state.set_state(EventCreateStates.end_date)
    now = datetime.utcnow()
    await cb.message.edit_text("📅 Tugash sanasi:", reply_markup=_calendar_kb(now.year, now.month, "end"))
    await cb.answer()


@router.callback_query(F.data.startswith("adm:cal:end:"), EventCreateStates.end_date)
async def evt_end_date(cb: CallbackQuery, state: FSMContext, **kwargs):
    date_str = cb.data.split(":")[3]
    await state.update_data(end_date=date_str)
    await state.set_state(EventCreateStates.end_hour)
    await cb.message.edit_text(f"📅 Tugash: {date_str}\n⏰ Soatni tanlang:", reply_markup=_hours_kb("end"))
    await cb.answer()


@router.callback_query(F.data.startswith("adm:hour:end:"), EventCreateStates.end_hour)
async def evt_end_hour(cb: CallbackQuery, state: FSMContext, **kwargs):
    hour = cb.data.split(":")[3]
    await state.update_data(end_hour=hour)
    await state.set_state(EventCreateStates.reward_pool_amount)
    await cb.message.edit_text("💰 Mukofot puli (umumiy summa):", reply_markup=_pool_amount_kb())
    await cb.answer()


@router.callback_query(F.data.startswith("adm:pool:"), EventCreateStates.reward_pool_amount)
async def evt_pool_amount(cb: CallbackQuery, state: FSMContext, **kwargs):
    amount = cb.data.split(":")[2]
    await state.update_data(reward_pool_amount=amount)
    if amount == "0":
        await state.update_data(reward_pool_currency="")
        await state.set_state(EventCreateStates.reward_template)
        await cb.message.edit_text("🎁 Mukofot shabloni:", reply_markup=_reward_template_kb())
    else:
        await state.set_state(EventCreateStates.reward_pool_currency)
        await cb.message.edit_text(f"💰 Summa: {int(amount):,}\n💱 Valyutani tanlang:", reply_markup=_currency_kb())
    await cb.answer()


@router.callback_query(F.data.startswith("adm:currency:"), EventCreateStates.reward_pool_currency)
async def evt_pool_currency(cb: CallbackQuery, state: FSMContext, **kwargs):
    currency = cb.data.split(":")[2]
    await state.update_data(reward_pool_currency=currency)
    await state.set_state(EventCreateStates.reward_template)
    await cb.message.edit_text("🎁 Mukofot shabloni:", reply_markup=_reward_template_kb())
    await cb.answer()


@router.callback_query(F.data.startswith("adm:reward:"), EventCreateStates.reward_template)
async def evt_reward_template(cb: CallbackQuery, state: FSMContext, **kwargs):
    template = cb.data.split(":")[2]
    data = await state.get_data()
    currency = data.get("reward_pool_currency", "UZS") or "UZS"
    rewards = []
    if template == "top3":
        rewards = [
            {"place_number": 1, "reward_title": "1-o'rin", "reward_amount": "", "currency_code": currency},
            {"place_number": 2, "reward_title": "2-o'rin", "reward_amount": "", "currency_code": currency},
            {"place_number": 3, "reward_title": "3-o'rin", "reward_amount": "", "currency_code": currency},
        ]
    elif template == "top5":
        rewards = [
            {"place_number": i, "reward_title": f"{i}-o'rin", "reward_amount": "", "currency_code": currency}
            for i in range(1, 6)
        ]
    await state.update_data(rewards=rewards, reward_template=template)
    await state.set_state(EventCreateStates.confirm)

    start_date = data.get("start_date", "")
    start_hour = data.get("start_hour", "00")
    end_date = data.get("end_date", "")
    end_hour = data.get("end_hour", "00")
    pool_amount = data.get("reward_pool_amount", "0")
    pool_currency = data.get("reward_pool_currency", "")
    countries = data.get("selected_countries", [])

    pool_text = f"💰 Mukofot puli: {int(pool_amount):,} {pool_currency}\n" if pool_amount != "0" else ""
    text = (
        f"📝 <b>Event tekshiruv</b>\n\n"
        f"📌 Nomi: <b>{data.get('event_name')}</b>\n"
        f"🌍 Mamlakatlar: {', '.join(countries)}\n"
        f"📅 {start_date} {start_hour}:00 — {end_date} {end_hour}:00\n"
        f"{pool_text}"
        f"🎁 Mukofot: {template}\n\n"
        f"Tasdiqlaysizmi?"
    )
    await cb.message.edit_text(text, parse_mode="HTML", reply_markup=_confirm_event_kb())
    await cb.answer()


@router.callback_query(F.data == "adm:event:save", EventCreateStates.confirm)
async def evt_save(cb: CallbackQuery, state: FSMContext, lang: str, **kwargs):
    data = await state.get_data()
    start_at = f"{data['start_date']} {data['start_hour']}:00"
    end_at = f"{data['end_date']} {data['end_hour']}:00"
    try:
        event = create_event(
            event_name=data["event_name"], description="", start_at=start_at, end_at=end_at,
            rules_text="", country_codes=data.get("selected_countries", []),
            rewards=data.get("rewards", []),
            created_by_admin_id=data.get("admin_id", ""),
            reward_pool_amount=data.get("reward_pool_amount", ""),
            reward_pool_currency=data.get("reward_pool_currency", ""),
        )
        await cb.message.edit_text(
            f"✅ Event yaratildi!\n\n🆔 <code>{event.get('event_id')}</code>\n📌 Status: draft",
            parse_mode="HTML",
            reply_markup=_event_actions_kb(event["event_id"], "draft"),
        )
    except Exception as e:
        await cb.message.edit_text(f"❌ Xatolik: {e}")
    await state.clear()
    await cb.answer()


# ── Leaderboard ──────────────────────────────────────────────────────────────

@router.message(F.text == "🥇 Reyting")
async def admin_leaderboard(message: Message, **kwargs):
    admin = _get_admin_info(message.from_user.id)
    if not admin:
        return
    await message.answer("🌍 Mamlakatni tanlang:", reply_markup=_leaderboard_country_kb())


@router.callback_query(F.data.startswith("adm:lb:"))
async def cb_leaderboard(cb: CallbackQuery, **kwargs):
    code = cb.data.split(":")[2]
    country = None if code == "all" else code
    lb = build_leaderboard(country_code=country, top_n=20)
    if not lb:
        await cb.answer("Reyting bo'sh", show_alert=True)
        return
    medals = {1: "🥇", 2: "🥈", 3: "🥉"}
    title = f"🌍 {code}" if code != "all" else "🌍 Barcha"
    lines = [f"{medals.get(e['rank'], str(e['rank'])+'.')} {e['full_name']} ({e['country_code']}) — <b>{e['points']}</b>"
             for e in lb]
    await cb.message.answer(f"🥇 <b>{title} reytingi</b>\n\n" + "\n".join(lines), parse_mode="HTML")
    await cb.answer()


# ── Manual points ────────────────────────────────────────────────────────────

@router.message(F.text == "💰 Ball berish")
async def admin_manual_points(message: Message, state: FSMContext, **kwargs):
    admin = _get_admin_info(message.from_user.id)
    if not admin:
        return
    await state.set_state(ManualPointsStates.employee_code)
    await state.update_data(admin_id=admin.get("admin_id", ""))
    await message.answer("🆔 Xodim kodini kiriting (masalan UZ-0001):",
                         reply_markup=ReplyKeyboardMarkup(
                             keyboard=[[KeyboardButton(text="❌ Bekor qilish")]], resize_keyboard=True))


@router.message(ManualPointsStates.employee_code)
async def mp_employee_code(message: Message, state: FSMContext, **kwargs):
    code = message.text.strip().upper()
    emp = get_employee_by_code(code)
    if not emp:
        await message.answer(f"❌ Xodim topilmadi: {code}\nQayta kiriting:")
        return
    await state.update_data(mp_employee_id=emp["employee_id"], mp_employee_code=emp["employee_code"],
                            mp_country=emp.get("country_code", ""))
    await message.answer(
        f"👤 {emp['full_name']} ({emp['employee_code']})\n\nBall miqdorini tanlang:",
        reply_markup=_manual_points_kb())


@router.callback_query(F.data.startswith("adm:mp:"))
async def cb_manual_points(cb: CallbackQuery, state: FSMContext, lang: str, **kwargs):
    data = await state.get_data()
    points = int(cb.data.split(":")[2])
    reason = "manual_bonus" if points > 0 else "manual_penalty"
    try:
        manual_adjust(
            employee_id=data["mp_employee_id"], employee_code=data["mp_employee_code"],
            points_delta=points, reason_code=reason, admin_id=data.get("admin_id", ""),
            country_code=data.get("mp_country", ""),
        )
        await cb.message.edit_reply_markup(reply_markup=None)
        await cb.message.answer(f"✅ {data['mp_employee_code']}: {points:+d} ball")
    except Exception as e:
        await cb.message.answer(f"❌ Xatolik: {e}")
    await state.clear()
    admin = _get_admin_info(cb.from_user.id)
    role = admin.get("role_code", "ga") if admin else "ga"
    await cb.message.answer("👑 Admin panel", reply_markup=_admin_keyboard(lang, role))
    await cb.answer()


# ── Employee status ──────────────────────────────────────────────────────────

@router.message(F.text == "🔒 Xodim statusi")
async def admin_emp_status(message: Message, state: FSMContext, **kwargs):
    admin = _get_admin_info(message.from_user.id)
    if not admin:
        return
    await state.set_state(EmployeeStatusStates.employee_code)
    await message.answer("🆔 Xodim kodini kiriting:",
                         reply_markup=ReplyKeyboardMarkup(
                             keyboard=[[KeyboardButton(text="❌ Bekor qilish")]], resize_keyboard=True))


@router.message(EmployeeStatusStates.employee_code)
async def es_employee_code(message: Message, state: FSMContext, **kwargs):
    code = message.text.strip().upper()
    emp = get_employee_by_code(code)
    if not emp:
        await message.answer(f"❌ Xodim topilmadi: {code}")
        return
    await state.update_data(es_employee_id=emp["employee_id"], es_employee_code=emp["employee_code"])
    await message.answer(
        f"👤 {emp['full_name']} ({emp['employee_code']})\n📌 Hozirgi status: {emp.get('status')}\n\nYangi status:",
        reply_markup=_status_kb())


@router.callback_query(F.data.startswith("adm:status:"))
async def cb_set_status(cb: CallbackQuery, state: FSMContext, lang: str, **kwargs):
    data = await state.get_data()
    new_status = cb.data.split(":")[2]
    update_employee_status(data["es_employee_id"], new_status)
    await cb.message.edit_reply_markup(reply_markup=None)
    await cb.message.answer(f"✅ {data['es_employee_code']} → {new_status}")
    await state.clear()
    admin = _get_admin_info(cb.from_user.id)
    role = admin.get("role_code", "ga") if admin else "ga"
    await cb.message.answer("👑 Admin panel", reply_markup=_admin_keyboard(lang, role))
    await cb.answer()


# ── Add admin ────────────────────────────────────────────────────────────────

@router.message(F.text == "➕ GA/Admin qo'shish")
async def admin_add_admin(message: Message, state: FSMContext, **kwargs):
    if not is_super_admin(message.from_user.id):
        await message.answer("⛔ Faqat Super Admin uchun.")
        return
    await state.set_state(AddAdminStates.tg_id)
    await message.answer("🆔 Yangi admin Telegram ID sini kiriting:",
                         reply_markup=ReplyKeyboardMarkup(
                             keyboard=[[KeyboardButton(text="❌ Bekor qilish")]], resize_keyboard=True))


@router.message(AddAdminStates.tg_id)
async def aa_tg_id(message: Message, state: FSMContext, **kwargs):
    tg_id = message.text.strip()
    if not tg_id.isdigit():
        await message.answer("❌ Faqat raqam kiriting (Telegram ID):")
        return
    await state.update_data(new_admin_tg_id=tg_id)
    await state.set_state(AddAdminStates.full_name)
    await message.answer("📛 Admin ismini kiriting:")


@router.message(AddAdminStates.full_name)
async def aa_name(message: Message, state: FSMContext, lang: str, **kwargs):
    data = await state.get_data()
    name = message.text.strip()
    try:
        admin = create_admin(
            telegram_user_id=data["new_admin_tg_id"], full_name=name,
            phone="", role_code="ga", created_by=str(message.from_user.id))
        await message.answer(f"✅ GA qo'shildi: {admin.get('admin_id')} — {name}")
    except Exception as e:
        await message.answer(f"❌ Xatolik: {e}")
    await state.clear()
    await message.answer("👑 Admin panel",
                         reply_markup=_admin_keyboard(lang, "super_admin"))
