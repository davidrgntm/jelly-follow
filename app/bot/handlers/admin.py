"""
Simple Uzbek-only Admin / GA interface.
- Enter with /admin or 👑 Admin panel button
- Mostly button-based flow
- Event creation: only event name typed, all other fields chosen with buttons
- Event leaderboard counts only points earned after event start
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
    Message,
    CallbackQuery,
    ReplyKeyboardMarkup,
    KeyboardButton,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    ReplyKeyboardRemove,
)

from app.bot.keyboards.main_keyboards import ADMIN_PANEL_TEXT, main_menu_keyboard
from app.services.admins_service import (
    get_admin_by_telegram_id,
    is_admin,
    is_super_admin,
    create_admin,
    get_system_stats,
)
from app.services.employees_service import (
    get_all_employees,
    update_employee_status,
    get_employee_by_code,
)
from app.services.events_service import (
    create_event,
    set_event_status,
    get_all_events,
    get_event_by_id,
    get_event_countries,
    get_event_rewards,
)
from app.services.points_service import manual_adjust
from app.services.leaderboard_service import build_leaderboard
from app.services.notifications_service import notify_event_started

logger = logging.getLogger(__name__)
router = Router()

BTN_EMPLOYEES = "👥 Xodimlar"
BTN_EVENTS = "🏆 Eventlar"
BTN_CREATE_EVENT = "➕ Yangi event"
BTN_LEADERBOARD = "🥇 Reyting"
BTN_MANUAL_POINTS = "💰 Ball berish"
BTN_SET_STATUS = "🔒 Xodim statusi"
BTN_SYSTEM_STATS = "📊 Statistika"
BTN_ADD_ADMIN = "➕ GA/Admin qo'shish"
BTN_BACK_TO_EMPLOYEE = "⬅️ Xodim menyusi"
BTN_CANCEL = "❌ Bekor qilish"

COUNTRY_LABELS = {
    "UZ": "🇺🇿 UZ",
    "RU": "🇷🇺 RU",
    "KG": "🇰🇬 KG",
    "AZ": "🇦🇿 AZ",
}


class EventCreateStates(StatesGroup):
    name = State()
    countries = State()
    start_date = State()
    start_hour = State()
    end_date = State()
    end_hour = State()
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


class CalendarStates(StatesGroup):
    pass


# ---------- keyboards ----------

def _admin_keyboard(role: str) -> ReplyKeyboardMarkup:
    rows = [
        [KeyboardButton(text=BTN_EVENTS), KeyboardButton(text=BTN_CREATE_EVENT)],
        [KeyboardButton(text=BTN_EMPLOYEES), KeyboardButton(text=BTN_LEADERBOARD)],
        [KeyboardButton(text=BTN_MANUAL_POINTS), KeyboardButton(text=BTN_SET_STATUS)],
        [KeyboardButton(text=BTN_SYSTEM_STATS)],
    ]
    if role == "super_admin":
        rows.append([KeyboardButton(text=BTN_ADD_ADMIN)])
    rows.append([KeyboardButton(text=BTN_BACK_TO_EMPLOYEE)])
    return ReplyKeyboardMarkup(keyboard=rows, resize_keyboard=True)


def _cancel_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text=BTN_CANCEL)]],
        resize_keyboard=True,
        one_time_keyboard=True,
    )


def _countries_keyboard(selected: set[str]) -> InlineKeyboardMarkup:
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
    rows.append([InlineKeyboardButton(text=BTN_CANCEL, callback_data="adm:cancel")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def _hours_keyboard(prefix: str) -> InlineKeyboardMarkup:
    rows = []
    row = []
    for h in range(0, 24):
        row.append(InlineKeyboardButton(text=f"{h:02d}:00", callback_data=f"adm:hour:{prefix}:{h:02d}"))
        if len(row) == 4:
            rows.append(row)
            row = []
    if row:
        rows.append(row)
    rows.append([InlineKeyboardButton(text=BTN_CANCEL, callback_data="adm:cancel")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def _reward_template_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Mukofot yo'q", callback_data="adm:reward:none")],
            [InlineKeyboardButton(text="Top 3", callback_data="adm:reward:top3")],
            [InlineKeyboardButton(text="Top 5", callback_data="adm:reward:top5")],
            [InlineKeyboardButton(text=BTN_CANCEL, callback_data="adm:cancel")],
        ]
    )


def _confirm_event_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="✅ Yaratish", callback_data="adm:event:save")],
            [InlineKeyboardButton(text=BTN_CANCEL, callback_data="adm:cancel")],
        ]
    )


def _status_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="✅ active", callback_data="adm:status:active")],
            [InlineKeyboardButton(text="⏸ inactive", callback_data="adm:status:inactive")],
            [InlineKeyboardButton(text="⛔ blocked", callback_data="adm:status:blocked")],
            [InlineKeyboardButton(text=BTN_CANCEL, callback_data="adm:cancel")],
        ]
    )


def _manual_points_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="+1", callback_data="adm:mp:1"),
                InlineKeyboardButton(text="+5", callback_data="adm:mp:5"),
                InlineKeyboardButton(text="+10", callback_data="adm:mp:10"),
            ],
            [
                InlineKeyboardButton(text="-1", callback_data="adm:mp:-1"),
                InlineKeyboardButton(text="-5", callback_data="adm:mp:-5"),
                InlineKeyboardButton(text="-10", callback_data="adm:mp:-10"),
            ],
            [InlineKeyboardButton(text=BTN_CANCEL, callback_data="adm:cancel")],
        ]
    )


def _add_admin_role_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="GA", callback_data="adm:add:ga")],
            [InlineKeyboardButton(text="Super admin", callback_data="adm:add:super_admin")],
            [InlineKeyboardButton(text=BTN_CANCEL, callback_data="adm:cancel")],
        ]
    )


def _leaderboard_country_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="ALL", callback_data="adm:lb:country:ALL")],
            [
                InlineKeyboardButton(text="UZ", callback_data="adm:lb:country:UZ"),
                InlineKeyboardButton(text="RU", callback_data="adm:lb:country:RU"),
            ],
            [
                InlineKeyboardButton(text="KG", callback_data="adm:lb:country:KG"),
                InlineKeyboardButton(text="AZ", callback_data="adm:lb:country:AZ"),
            ],
            [InlineKeyboardButton(text=BTN_CANCEL, callback_data="adm:cancel")],
        ]
    )


def _leaderboard_period_keyboard(country: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Umumiy", callback_data=f"adm:lb:period:{country}:all")],
            [
                InlineKeyboardButton(text="Bugun", callback_data=f"adm:lb:period:{country}:today"),
                InlineKeyboardButton(text="Hafta", callback_data=f"adm:lb:period:{country}:week"),
            ],
            [InlineKeyboardButton(text="Oy", callback_data=f"adm:lb:period:{country}:month")],
            [InlineKeyboardButton(text=BTN_CANCEL, callback_data="adm:cancel")],
        ]
    )


def _event_actions_keyboard(event: dict) -> InlineKeyboardMarkup:
    event_id = event.get("event_id", "")
    status = event.get("status", "draft")
    rows = []
    if status == "draft":
        rows.append([InlineKeyboardButton(text="▶️ Ishga tushirish", callback_data=f"adm:event:status:{event_id}:active")])
    elif status == "active":
        rows.append([
            InlineKeyboardButton(text="⏸ Pauza", callback_data=f"adm:event:status:{event_id}:paused"),
            InlineKeyboardButton(text="🏁 Yakunlash", callback_data=f"adm:event:status:{event_id}:finished"),
        ])
    elif status == "paused":
        rows.append([
            InlineKeyboardButton(text="▶️ Davom ettirish", callback_data=f"adm:event:status:{event_id}:active"),
            InlineKeyboardButton(text="🏁 Yakunlash", callback_data=f"adm:event:status:{event_id}:finished"),
        ])
    rows.append([InlineKeyboardButton(text="🥇 Event reytingi", callback_data=f"adm:event:lb:{event_id}")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def _render_calendar(year: int, month: int, field_name: str) -> InlineKeyboardMarkup:
    month_names = [
        "Yanvar", "Fevral", "Mart", "Aprel", "May", "Iyun",
        "Iyul", "Avgust", "Sentyabr", "Oktyabr", "Noyabr", "Dekabr",
    ]
    rows = [
        [
            InlineKeyboardButton(text="◀️", callback_data=f"adm:calnav:{field_name}:{year}:{month}:prev"),
            InlineKeyboardButton(text=f"{month_names[month-1]} {year}", callback_data="adm:noop"),
            InlineKeyboardButton(text="▶️", callback_data=f"adm:calnav:{field_name}:{year}:{month}:next"),
        ],
        [
            InlineKeyboardButton(text="Du", callback_data="adm:noop"),
            InlineKeyboardButton(text="Se", callback_data="adm:noop"),
            InlineKeyboardButton(text="Ch", callback_data="adm:noop"),
            InlineKeyboardButton(text="Pa", callback_data="adm:noop"),
            InlineKeyboardButton(text="Ju", callback_data="adm:noop"),
            InlineKeyboardButton(text="Sh", callback_data="adm:noop"),
            InlineKeyboardButton(text="Ya", callback_data="adm:noop"),
        ],
    ]
    cal = calendar.monthcalendar(year, month)
    for week in cal:
        row = []
        for day in week:
            if day == 0:
                row.append(InlineKeyboardButton(text=" ", callback_data="adm:noop"))
            else:
                row.append(
                    InlineKeyboardButton(
                        text=str(day),
                        callback_data=f"adm:calpick:{field_name}:{year}-{month:02d}-{day:02d}",
                    )
                )
        rows.append(row)
    rows.append([InlineKeyboardButton(text=BTN_CANCEL, callback_data="adm:cancel")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


# ---------- helpers ----------

def _admin_check(tg_id: int) -> bool:
    return is_admin(tg_id)


def _super_check(tg_id: int) -> bool:
    return is_super_admin(tg_id)


def _current_admin_role(tg_id: int) -> str:
    admin = get_admin_by_telegram_id(tg_id)
    return admin.get("role_code", "ga") if admin else "ga"


def _event_default_rewards(template_code: str) -> list[dict]:
    if template_code == "top3":
        return [
            {"place_number": 1, "reward_title": "1-o'rin", "reward_amount": "", "currency_code": ""},
            {"place_number": 2, "reward_title": "2-o'rin", "reward_amount": "", "currency_code": ""},
            {"place_number": 3, "reward_title": "3-o'rin", "reward_amount": "", "currency_code": ""},
        ]
    if template_code == "top5":
        return [
            {"place_number": 1, "reward_title": "1-o'rin", "reward_amount": "", "currency_code": ""},
            {"place_number": 2, "reward_title": "2-o'rin", "reward_amount": "", "currency_code": ""},
            {"place_number": 3, "reward_title": "3-o'rin", "reward_amount": "", "currency_code": ""},
            {"place_number": 4, "reward_title": "4-o'rin", "reward_amount": "", "currency_code": ""},
            {"place_number": 5, "reward_title": "5-o'rin", "reward_amount": "", "currency_code": ""},
        ]
    return []


def _compose_event_dt(date_str: str, hour_str: str) -> str:
    return f"{date_str} {hour_str}:00"


def _event_summary(data: dict) -> str:
    return (
        "🏆 <b>Yangi event</b>\n\n"
        f"Nomi: <b>{data.get('name','')}</b>\n"
        f"Mamlakatlar: <b>{', '.join(data.get('countries', []))}</b>\n"
        f"Boshlanish: <b>{data.get('start_at','')}</b>\n"
        f"Tugash: <b>{data.get('end_at','')}</b>\n"
        f"Mukofot shabloni: <b>{data.get('reward_template_label','Mukofot yo\'q')}</b>\n\n"
        "Barcha event ballari event boshlanganidan keyin hisoblanadi.\n"
        "Umumiy ballar alohida saqlanadi."
    )


async def _show_admin_panel(message: Message):
    admin = get_admin_by_telegram_id(message.from_user.id)
    if not admin:
        await message.answer("❌ Siz admin emassiz.")
        return
    role = admin.get("role_code", "ga")
    text = (
        "👑 <b>Admin panel</b>\n\n"
        f"Rol: <b>{role}</b>\n"
        "Hammasi maksimal osonlashtirilgan. Pastdagi tugmalardan foydalaning."
    )
    await message.answer(text, parse_mode="HTML", reply_markup=_admin_keyboard(role))


async def _back_to_employee_menu(message: Message, employee: dict, lang: str):
    if employee:
        await message.answer(
            "🏠 Xodim menyusi",
            reply_markup=main_menu_keyboard(lang, is_admin=is_admin(message.from_user.id)),
        )
    else:
        await message.answer("✅ Admin panel yopildi.", reply_markup=ReplyKeyboardRemove())


# ---------- entry / common ----------
@router.message(Command("admin"))
@router.message(F.text == ADMIN_PANEL_TEXT)
async def cmd_admin(message: Message, state: FSMContext):
    try:
        await state.clear()
        if not _admin_check(message.from_user.id):
            await message.answer("❌ Sizda admin huquqi yo'q.")
            return
        await _show_admin_panel(message)
    except Exception:
        logger.exception("admin panel open failed")
        await message.answer("❌ Admin panelni ochishda xatolik bo'ldi.")


@router.message(F.text == BTN_BACK_TO_EMPLOYEE)
async def back_to_employee(message: Message, employee: dict, lang: str, state: FSMContext):
    await state.clear()
    await _back_to_employee_menu(message, employee, lang)


@router.message(F.text == BTN_CANCEL)
async def cancel_text(message: Message, state: FSMContext):
    await state.clear()
    if _admin_check(message.from_user.id):
        await message.answer("❌ Amal bekor qilindi.", reply_markup=_admin_keyboard(_current_admin_role(message.from_user.id)))
    else:
        await message.answer("❌ Bekor qilindi.", reply_markup=ReplyKeyboardRemove())


@router.callback_query(F.data == "adm:cancel")
async def cancel_callback(cb: CallbackQuery, state: FSMContext, employee: dict, lang: str):
    await state.clear()
    await cb.message.edit_reply_markup(reply_markup=None)
    await cb.answer("Bekor qilindi")
    if _admin_check(cb.from_user.id):
        await cb.message.answer("❌ Amal bekor qilindi.", reply_markup=_admin_keyboard(_current_admin_role(cb.from_user.id)))
    else:
        if employee:
            await cb.message.answer("🏠 Xodim menyusi", reply_markup=main_menu_keyboard(lang, is_admin=is_admin(cb.from_user.id)))


@router.callback_query(F.data == "adm:noop")
async def noop(cb: CallbackQuery):
    await cb.answer()


# ---------- employees / stats ----------
@router.message(F.text == BTN_EMPLOYEES)
async def employees_list(message: Message):
    try:
        if not _admin_check(message.from_user.id):
            await message.answer("❌ Sizda admin huquqi yo'q.")
            return
        employees = get_all_employees()
        if not employees:
            await message.answer("📭 Xodimlar yo'q.")
            return
        lines = []
        for e in employees[:30]:
            lines.append(
                f"• <code>{e.get('employee_code')}</code> {e.get('full_name')} [{e.get('country_code')}] — {e.get('status')}"
            )
        text = f"👥 <b>Xodimlar ({len(employees)} ta)</b>\n\n" + "\n".join(lines)
        if len(employees) > 30:
            text += f"\n\n... va yana {len(employees) - 30} ta"
        await message.answer(text, parse_mode="HTML")
    except Exception:
        logger.exception("employees list failed")
        await message.answer("❌ Xodimlar ro'yxatini chiqarib bo'lmadi.")


@router.message(F.text == BTN_SYSTEM_STATS)
async def system_stats(message: Message):
    try:
        if not _admin_check(message.from_user.id):
            await message.answer("❌ Sizda admin huquqi yo'q.")
            return
        stats = get_system_stats()
        text = (
            "📊 <b>Tizim statistikasi</b>\n\n"
            f"👥 Xodimlar: <b>{stats['employees_total']}</b>\n"
            f"✅ Faol xodimlar: <b>{stats['employees_active']}</b>\n"
            f"👑 Adminlar: <b>{stats['admins_total']}</b>\n"
            f"🏆 Eventlar: <b>{stats['events_total']}</b>\n"
            f"🟢 Faol eventlar: <b>{stats['events_active']}</b>\n"
            f"📱 Skanlar: <b>{stats['scans_total']}</b>\n"
            f"✨ Unique award: <b>{stats['unique_awards']}</b>\n"
            f"🔁 Duplicate scans: <b>{stats['duplicate_scans']}</b>\n"
            f"⭐ Umumiy ball: <b>{stats['points_total']}</b>"
        )
        await message.answer(text, parse_mode="HTML")
    except Exception:
        logger.exception("system stats failed")
        await message.answer("❌ Statistika olinmadi.")


# ---------- leaderboard ----------
@router.message(F.text == BTN_LEADERBOARD)
async def leaderboard_start(message: Message, state: FSMContext):
    if not _admin_check(message.from_user.id):
        await message.answer("❌ Sizda admin huquqi yo'q.")
        return
    await state.set_state(LeaderboardStates.choose_country)
    await message.answer("🥇 Qaysi mamlakat reytingi kerak?", reply_markup=ReplyKeyboardRemove())
    await message.answer("Mamlakatni tanlang:", reply_markup=_leaderboard_country_keyboard())


@router.callback_query(F.data.startswith("adm:lb:country:"))
async def leaderboard_choose_period(cb: CallbackQuery, state: FSMContext):
    country = cb.data.split(":")[-1]
    await state.update_data(lb_country=country)
    await cb.message.edit_text(f"Mamlakat: <b>{country}</b>\nEndi periodni tanlang:", parse_mode="HTML", reply_markup=_leaderboard_period_keyboard(country))
    await cb.answer()


@router.callback_query(F.data.startswith("adm:lb:period:"))
async def leaderboard_show(cb: CallbackQuery, state: FSMContext):
    try:
        _, _, _, country, period = cb.data.split(":")
        country_code = None if country == "ALL" else country
        lb = build_leaderboard(country_code=country_code, period=period, top_n=20)
        if not lb:
            await cb.message.edit_text("📭 Reyting bo'yicha ma'lumot yo'q.")
            await cb.answer()
            return
        medals = {1: "🥇", 2: "🥈", 3: "🥉"}
        lines = []
        for e in lb:
            medal = medals.get(e["rank"], f"{e['rank']}.")
            lines.append(f"{medal} {e['full_name']} [{e['country_code']}] — <b>{e['points']}</b>")
        title = country if country_code else "ALL"
        await cb.message.edit_text(
            f"🥇 <b>Reyting</b> ({title}, {period})\n\n" + "\n".join(lines),
            parse_mode="HTML",
        )
        await state.clear()
        await cb.answer()
    except Exception:
        logger.exception("leaderboard failed")
        await cb.answer("Xatolik", show_alert=True)


# ---------- event list / event actions ----------
@router.message(F.text == BTN_EVENTS)
async def events_list(message: Message):
    try:
        if not _admin_check(message.from_user.id):
            await message.answer("❌ Sizda admin huquqi yo'q.")
            return
        events = get_all_events()
        if not events:
            await message.answer("📭 Eventlar yo'q.")
            return
        await message.answer("🏆 Eventlar ro'yxati:")
        for e in events:
            countries = e.get("countries", []) or []
            rewards = get_event_rewards(e.get("event_id", ""))
            reward_info = f"\nMukofotlar: {len(rewards)} ta" if rewards else "\nMukofotlar: yo'q"
            await message.answer(
                f"<b>{e.get('event_name')}</b>\n"
                f"ID: <code>{e.get('event_id')}</code>\n"
                f"Status: <b>{e.get('status')}</b>\n"
                f"{e.get('start_at')} — {e.get('end_at')}\n"
                f"Mamlakatlar: {', '.join(countries) or '-'}{reward_info}",
                parse_mode="HTML",
                reply_markup=_event_actions_keyboard(e),
            )
    except Exception:
        logger.exception("events list failed")
        await message.answer("❌ Eventlarni chiqarib bo'lmadi.")


@router.callback_query(F.data.startswith("adm:event:status:"))
async def event_change_status(cb: CallbackQuery):
    try:
        _, _, _, event_id, status = cb.data.split(":")
        set_event_status(event_id, status)

        if status == "active":
            event = get_event_by_id(event_id)
            countries = get_event_countries(event_id)
            rewards = get_event_rewards(event_id)
            all_emps = get_all_employees()
            relevant = [
                e for e in all_emps
                if e.get("country_code", "").upper() in [c.upper() for c in countries]
                and e.get("status") == "active"
            ]
            asyncio.create_task(notify_event_started(relevant, event, rewards))
            await cb.answer(f"Event ishga tushdi. {len(relevant)} xodimga xabar yuborilyapti.", show_alert=True)
        else:
            await cb.answer("Event statusi yangilandi.", show_alert=True)

        event = get_event_by_id(event_id)
        countries = get_event_countries(event_id)
        rewards = get_event_rewards(event_id)
        reward_info = f"\nMukofotlar: {len(rewards)} ta" if rewards else "\nMukofotlar: yo'q"
        await cb.message.edit_text(
            f"<b>{event.get('event_name')}</b>\n"
            f"ID: <code>{event.get('event_id')}</code>\n"
            f"Status: <b>{event.get('status')}</b>\n"
            f"{event.get('start_at')} — {event.get('end_at')}\n"
            f"Mamlakatlar: {', '.join(countries) or '-'}{reward_info}",
            parse_mode="HTML",
            reply_markup=_event_actions_keyboard(event),
        )
    except Exception as e:
        logger.exception("event status change failed")
        await cb.answer(f"Xatolik: {e}", show_alert=True)


@router.callback_query(F.data.startswith("adm:event:lb:"))
async def event_leaderboard(cb: CallbackQuery):
    try:
        event_id = cb.data.split(":")[-1]
        event = get_event_by_id(event_id)
        if not event:
            await cb.answer("Event topilmadi", show_alert=True)
            return
        lb = build_leaderboard(event_id=event_id, period="all", top_n=20)
        if not lb:
            await cb.message.answer(f"🏆 {event.get('event_name')} bo'yicha hozircha ball yo'q.")
            await cb.answer()
            return
        medals = {1: "🥇", 2: "🥈", 3: "🥉"}
        lines = []
        for e in lb:
            medal = medals.get(e["rank"], f"{e['rank']}.")
            lines.append(f"{medal} {e['full_name']} [{e['country_code']}] — <b>{e['points']}</b>")
        await cb.message.answer(
            f"🏆 <b>{event.get('event_name')}</b>\n"
            f"Faqat event boshlanganidan keyingi ballar hisoblangan.\n\n"
            + "\n".join(lines),
            parse_mode="HTML",
        )
        await cb.answer()
    except Exception:
        logger.exception("event leaderboard failed")
        await cb.answer("Xatolik", show_alert=True)


# ---------- create event ----------
@router.message(F.text == BTN_CREATE_EVENT)
async def create_event_start(message: Message, state: FSMContext):
    if not _admin_check(message.from_user.id):
        await message.answer("❌ Sizda admin huquqi yo'q.")
        return
    await state.clear()
    await state.set_state(EventCreateStates.name)
    await message.answer(
        "🏆 Yangi event nomini yozing.\n\n"
        "Qolgan hamma narsani knopka bilan tanlaysiz.",
        reply_markup=_cancel_keyboard(),
    )


@router.message(EventCreateStates.name)
async def create_event_name(message: Message, state: FSMContext):
    name = (message.text or "").strip()
    if len(name) < 2:
        await message.answer("Event nomi juda qisqa. Qayta kiriting.")
        return
    await state.update_data(name=name, countries=[])
    await state.set_state(EventCreateStates.countries)
    await message.answer(
        "🌍 Event mamlakatlarini tanlang:",
        reply_markup=ReplyKeyboardRemove(),
    )
    await message.answer("Bir yoki bir nechta mamlakat tanlashingiz mumkin:", reply_markup=_countries_keyboard(set()))


@router.callback_query(F.data.startswith("adm:evt:ctry:"))
async def create_event_countries(cb: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    selected = set(data.get("countries", []))
    picked = cb.data.split(":")[-1]

    if picked == "done":
        if not selected:
            await cb.answer("Kamida bitta mamlakat tanlang", show_alert=True)
            return
        today = datetime.utcnow().date()
        await state.update_data(countries=sorted(selected))
        await state.set_state(EventCreateStates.start_date)
        await cb.message.edit_text("📅 Event boshlanish sanasini tanlang:", reply_markup=_render_calendar(today.year, today.month, "start"))
        await cb.answer()
        return

    if picked in selected:
        selected.remove(picked)
    else:
        selected.add(picked)
    await state.update_data(countries=sorted(selected))
    await cb.message.edit_reply_markup(reply_markup=_countries_keyboard(selected))
    await cb.answer()


@router.callback_query(F.data.startswith("adm:calnav:"))
async def calendar_nav(cb: CallbackQuery):
    _, _, field_name, year, month, direction = cb.data.split(":")
    year = int(year)
    month = int(month)
    current = datetime(year, month, 1)
    if direction == "prev":
        current = (current.replace(day=1) - timedelta(days=1)).replace(day=1)
    else:
        if month == 12:
            current = datetime(year + 1, 1, 1)
        else:
            current = datetime(year, month + 1, 1)
    await cb.message.edit_reply_markup(reply_markup=_render_calendar(current.year, current.month, field_name))
    await cb.answer()


@router.callback_query(F.data.startswith("adm:calpick:"))
async def calendar_pick(cb: CallbackQuery, state: FSMContext):
    _, _, field_name, date_str = cb.data.split(":")
    if field_name == "start":
        await state.update_data(start_date=date_str)
        await state.set_state(EventCreateStates.start_hour)
        await cb.message.edit_text(f"⏰ Boshlanish soatini tanlang:\n<b>{date_str}</b>", parse_mode="HTML", reply_markup=_hours_keyboard("start"))
    else:
        await state.update_data(end_date=date_str)
        await state.set_state(EventCreateStates.end_hour)
        await cb.message.edit_text(f"⏰ Tugash soatini tanlang:\n<b>{date_str}</b>", parse_mode="HTML", reply_markup=_hours_keyboard("end"))
    await cb.answer()


@router.callback_query(F.data.startswith("adm:hour:start:"))
async def choose_start_hour(cb: CallbackQuery, state: FSMContext):
    hour = cb.data.split(":")[-1]
    data = await state.get_data()
    start_at = _compose_event_dt(data.get("start_date"), hour)
    await state.update_data(start_hour=hour, start_at=start_at)
    today = datetime.utcnow().date()
    await state.set_state(EventCreateStates.end_date)
    await cb.message.edit_text(
        f"Boshlanish: <b>{start_at}</b>\n\nEndi tugash sanasini tanlang:",
        parse_mode="HTML",
        reply_markup=_render_calendar(today.year, today.month, "end"),
    )
    await cb.answer()


@router.callback_query(F.data.startswith("adm:hour:end:"))
async def choose_end_hour(cb: CallbackQuery, state: FSMContext):
    hour = cb.data.split(":")[-1]
    data = await state.get_data()
    end_at = _compose_event_dt(data.get("end_date"), hour)
    await state.update_data(end_hour=hour, end_at=end_at)
    await state.set_state(EventCreateStates.reward_template)
    await cb.message.edit_text(
        f"Tugash: <b>{end_at}</b>\n\nEndi mukofot shablonini tanlang:",
        parse_mode="HTML",
        reply_markup=_reward_template_keyboard(),
    )
    await cb.answer()


@router.callback_query(F.data.startswith("adm:reward:"))
async def choose_reward_template(cb: CallbackQuery, state: FSMContext):
    template_code = cb.data.split(":")[-1]
    labels = {"none": "Mukofot yo'q", "top3": "Top 3", "top5": "Top 5"}
    await state.update_data(
        reward_template=template_code,
        reward_template_label=labels.get(template_code, "Mukofot yo'q"),
    )
    data = await state.get_data()
    await state.set_state(EventCreateStates.confirm)
    await cb.message.edit_text(_event_summary(data), parse_mode="HTML", reply_markup=_confirm_event_keyboard())
    await cb.answer()


@router.callback_query(F.data == "adm:event:save")
async def save_event(cb: CallbackQuery, state: FSMContext):
    try:
        data = await state.get_data()
        admin = get_admin_by_telegram_id(cb.from_user.id)
        rewards = _event_default_rewards(data.get("reward_template", "none"))
        event = create_event(
            event_name=data.get("name", ""),
            description=data.get("name", ""),
            start_at=data.get("start_at", ""),
            end_at=data.get("end_at", ""),
            rules_text="Event boshidan yig'ilgan ballar hisoblanadi.",
            country_codes=data.get("countries", []),
            rewards=rewards,
            created_by_admin_id=admin["admin_id"],
        )
        await state.clear()
        await cb.message.edit_text(
            f"✅ Event yaratildi!\n\n"
            f"Nomi: <b>{event.get('event_name')}</b>\n"
            f"ID: <code>{event.get('event_id')}</code>\n"
            f"Status: <b>{event.get('status')}</b>\n\n"
            f"Endi Eventlar bo'limidan uni ishga tushirishingiz mumkin.",
            parse_mode="HTML",
        )
        await cb.message.answer("Admin panelga qaytdingiz.", reply_markup=_admin_keyboard(_current_admin_role(cb.from_user.id)))
        await cb.answer("Saqlandi")
    except Exception as e:
        logger.exception("save event failed")
        await cb.answer(f"Xatolik: {e}", show_alert=True)


# ---------- manual points ----------
@router.message(F.text == BTN_MANUAL_POINTS)
async def manual_points_start(message: Message, state: FSMContext):
    if not _admin_check(message.from_user.id):
        await message.answer("❌ Sizda admin huquqi yo'q.")
        return
    await state.clear()
    await state.set_state(ManualPointsStates.employee_code)
    await message.answer(
        "💰 Qaysi xodimga ball bermoqchisiz?\nXodim kodini yozing. Masalan: UZ-001",
        reply_markup=_cancel_keyboard(),
    )


@router.message(ManualPointsStates.employee_code)
async def manual_points_code(message: Message, state: FSMContext):
    code = (message.text or "").strip().upper()
    emp = get_employee_by_code(code)
    if not emp:
        await message.answer("❌ Bunday xodim topilmadi. Kodni qayta yuboring.")
        return
    await state.update_data(employee_code=code)
    await message.answer(
        f"Xodim: <b>{emp.get('full_name')}</b>\nEndi nechta ball berishni tanlang:",
        parse_mode="HTML",
        reply_markup=ReplyKeyboardRemove(),
    )
    await message.answer("Ballni tanlang:", reply_markup=_manual_points_keyboard())


@router.callback_query(F.data.startswith("adm:mp:"))
async def manual_points_apply(cb: CallbackQuery, state: FSMContext):
    try:
        delta = int(cb.data.split(":")[-1])
        data = await state.get_data()
        code = data.get("employee_code", "")
        emp = get_employee_by_code(code)
        admin = get_admin_by_telegram_id(cb.from_user.id)
        reason = "manual_bonus" if delta > 0 else "manual_penalty"
        manual_adjust(
            employee_id=emp["employee_id"],
            employee_code=emp["employee_code"],
            points_delta=delta,
            reason_code=reason,
            admin_id=admin["admin_id"],
        )
        await state.clear()
        await cb.message.edit_text(
            f"✅ <b>{emp.get('full_name')}</b> ga <b>{delta:+d}</b> ball berildi.",
            parse_mode="HTML",
        )
        await cb.message.answer("Admin panelga qaytdingiz.", reply_markup=_admin_keyboard(_current_admin_role(cb.from_user.id)))
        await cb.answer("Tayyor")
    except Exception:
        logger.exception("manual points failed")
        await cb.answer("Xatolik", show_alert=True)


# ---------- set employee status ----------
@router.message(F.text == BTN_SET_STATUS)
async def set_status_start(message: Message, state: FSMContext):
    if not _admin_check(message.from_user.id):
        await message.answer("❌ Sizda admin huquqi yo'q.")
        return
    await state.clear()
    await state.set_state(EmployeeStatusStates.employee_code)
    await message.answer(
        "🔒 Qaysi xodim statusini o'zgartirasiz?\nXodim kodini yozing. Masalan: UZ-001",
        reply_markup=_cancel_keyboard(),
    )


@router.message(EmployeeStatusStates.employee_code)
async def set_status_code(message: Message, state: FSMContext):
    code = (message.text or "").strip().upper()
    emp = get_employee_by_code(code)
    if not emp:
        await message.answer("❌ Xodim topilmadi. Kodni qayta yuboring.")
        return
    await state.update_data(employee_code=code)
    await message.answer(
        f"Xodim: <b>{emp.get('full_name')}</b>\nYangi statusni tanlang:",
        parse_mode="HTML",
        reply_markup=ReplyKeyboardRemove(),
    )
    await message.answer("Statusni tanlang:", reply_markup=_status_keyboard())


@router.callback_query(F.data.startswith("adm:status:"))
async def set_status_apply(cb: CallbackQuery, state: FSMContext):
    try:
        status = cb.data.split(":")[-1]
        data = await state.get_data()
        code = data.get("employee_code", "")
        emp = get_employee_by_code(code)
        admin = get_admin_by_telegram_id(cb.from_user.id)
        update_employee_status(emp["employee_id"], status, updated_by=admin["admin_id"])
        await state.clear()
        await cb.message.edit_text(
            f"✅ <b>{emp.get('full_name')}</b> statusi <b>{status}</b> qilindi.",
            parse_mode="HTML",
        )
        await cb.message.answer("Admin panelga qaytdingiz.", reply_markup=_admin_keyboard(_current_admin_role(cb.from_user.id)))
        await cb.answer("Tayyor")
    except Exception:
        logger.exception("set status failed")
        await cb.answer("Xatolik", show_alert=True)


# ---------- add admin / GA ----------
@router.message(F.text == BTN_ADD_ADMIN)
async def add_admin_start(message: Message, state: FSMContext):
    if not _super_check(message.from_user.id):
        await message.answer("❌ Faqat super admin uchun.")
        return
    await state.clear()
    await state.set_state(AddAdminStates.tg_id)
    await message.answer(
        "➕ Yangi GA/Admin Telegram ID sini yozing:",
        reply_markup=_cancel_keyboard(),
    )


@router.message(AddAdminStates.tg_id)
async def add_admin_tg(message: Message, state: FSMContext):
    await state.update_data(tg_id=(message.text or "").strip())
    await state.set_state(AddAdminStates.full_name)
    await message.answer("Ismini yozing:", reply_markup=_cancel_keyboard())


@router.message(AddAdminStates.full_name)
async def add_admin_name(message: Message, state: FSMContext):
    await state.update_data(full_name=(message.text or "").strip())
    await message.answer("Rolni tanlang:", reply_markup=ReplyKeyboardRemove())
    await message.answer("Rol:", reply_markup=_add_admin_role_keyboard())


@router.callback_query(F.data.startswith("adm:add:"))
async def add_admin_apply(cb: CallbackQuery, state: FSMContext):
    try:
        role = cb.data.split(":")[-1]
        data = await state.get_data()
        creator = get_admin_by_telegram_id(cb.from_user.id)
        new_admin = create_admin(
            telegram_user_id=data.get("tg_id", ""),
            full_name=data.get("full_name", ""),
            phone="",
            role_code=role,
            created_by=creator["admin_id"],
        )
        await state.clear()
        await cb.message.edit_text(
            f"✅ Admin yaratildi.\n\nID: <code>{new_admin.get('admin_id')}</code>\nRol: <b>{role}</b>",
            parse_mode="HTML",
        )
        await cb.message.answer("Admin panelga qaytdingiz.", reply_markup=_admin_keyboard(_current_admin_role(cb.from_user.id)))
        await cb.answer("Tayyor")
    except Exception:
        logger.exception("add admin failed")
        await cb.answer("Xatolik", show_alert=True)
