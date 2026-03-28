"""
Admin / GA bot interface.
- /admin opens reply-keyboard panel
- super_admin can add GA/admin from bot
- GA/admin can create and manage events from bot
- handlers are wrapped with try/except to avoid webhook 500
"""
import asyncio
import logging
from aiogram import Router, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove

from app.bot.keyboards.main_keyboards import main_menu_keyboard
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

BTN_ADMIN_PANEL = "👑 Admin panel"
BTN_EMPLOYEES = "👥 Xodimlar"
BTN_EVENTS = "🏆 Eventlar"
BTN_CREATE_EVENT = "➕ Event yaratish"
BTN_ACTIVATE_EVENT = "▶️ Eventni ishga tushirish"
BTN_PAUSE_EVENT = "⏸ Eventni pauza qilish"
BTN_FINISH_EVENT = "🏁 Eventni yakunlash"
BTN_LEADERBOARD = "🥇 Reyting"
BTN_MANUAL_POINTS = "💰 Qo'lda ball berish"
BTN_SET_STATUS = "🔒 Xodim statusi"
BTN_SYSTEM_STATS = "📊 Tizim statistikasi"
BTN_ADD_ADMIN = "➕ GA/Admin qo'shish"
BTN_BACK_TO_EMPLOYEE = "⬅️ Xodim menyusi"
BTN_CANCEL = "❌ Bekor qilish"


class AddAdminStates(StatesGroup):
    tg_id = State()
    full_name = State()
    role = State()


class EventCreateStates(StatesGroup):
    name = State()
    description = State()
    start_at = State()
    end_at = State()
    rules = State()
    countries = State()
    rewards = State()


class ManualPointsStates(StatesGroup):
    employee_code = State()
    delta = State()
    reason = State()


class EmployeeStatusStates(StatesGroup):
    employee_code = State()
    status = State()


class EventStatusStates(StatesGroup):
    action = State()
    event_id = State()


class LeaderboardStates(StatesGroup):
    country = State()
    period = State()


def _admin_keyboard(role: str) -> ReplyKeyboardMarkup:
    rows = [
        [KeyboardButton(text=BTN_EMPLOYEES), KeyboardButton(text=BTN_EVENTS)],
        [KeyboardButton(text=BTN_CREATE_EVENT), KeyboardButton(text=BTN_LEADERBOARD)],
        [KeyboardButton(text=BTN_ACTIVATE_EVENT), KeyboardButton(text=BTN_PAUSE_EVENT)],
        [KeyboardButton(text=BTN_FINISH_EVENT), KeyboardButton(text=BTN_MANUAL_POINTS)],
        [KeyboardButton(text=BTN_SET_STATUS), KeyboardButton(text=BTN_SYSTEM_STATS)],
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


def _is_admin(user_id: int) -> bool:
    return is_admin(user_id)


def _is_super_admin(user_id: int) -> bool:
    return is_super_admin(user_id)


async def _show_admin_panel(message: Message):
    admin = get_admin_by_telegram_id(message.from_user.id)
    if not admin:
        await message.answer("❌ Siz admin emassiz.")
        return
    role = admin.get("role_code", "")
    text = (
        "👑 <b>Admin panel</b>\n\n"
        f"Rol: <b>{role}</b>\n\n"
        "Pastdagi tugmalar orqali boshqarishingiz mumkin.\n"
        "Kerak bo'lsa eski slash komandalar ham ishlaydi."
    )
    await message.answer(text, parse_mode="HTML", reply_markup=_admin_keyboard(role))


@router.message(Command("admin"))
@router.message(F.text == BTN_ADMIN_PANEL)
async def cmd_admin(message: Message, state: FSMContext):
    try:
        await state.clear()
        if not _is_admin(message.from_user.id):
            await message.answer("❌ Sizda admin huquqi yo'q.")
            return
        await _show_admin_panel(message)
    except Exception:
        logger.exception("/admin failed")
        await message.answer("❌ Admin panelni ochishda xatolik bo'ldi.")


@router.message(F.text == BTN_BACK_TO_EMPLOYEE)
async def back_to_employee(message: Message, employee: dict, lang: str, state: FSMContext):
    await state.clear()
    if employee:
        await message.answer("🏠 Xodim menyusi", reply_markup=main_menu_keyboard(lang))
    else:
        await message.answer("✅ Admin panel yopildi.", reply_markup=ReplyKeyboardRemove())


@router.message(F.text == BTN_CANCEL)
async def cancel_any_state(message: Message, state: FSMContext):
    await state.clear()
    admin = get_admin_by_telegram_id(message.from_user.id)
    if admin:
        await message.answer("❌ Amal bekor qilindi.", reply_markup=_admin_keyboard(admin.get("role_code", "ga")))
    else:
        await message.answer("❌ Bekor qilindi.", reply_markup=ReplyKeyboardRemove())


@router.message(Command("employees"))
@router.message(F.text == BTN_EMPLOYEES)
async def cmd_employees(message: Message):
    try:
        if not _is_admin(message.from_user.id):
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
        logger.exception("employees failed")
        await message.answer("❌ Xodimlarni olishda xatolik bo'ldi.")


@router.message(Command("events"))
@router.message(F.text == BTN_EVENTS)
async def cmd_events(message: Message):
    try:
        if not _is_admin(message.from_user.id):
            await message.answer("❌ Sizda admin huquqi yo'q.")
            return
        events = get_all_events()
        if not events:
            await message.answer("📭 Eventlar yo'q.")
            return
        lines = []
        for e in events:
            countries = e.get("countries", []) or []
            lines.append(
                f"• <code>{e.get('event_id')}</code> <b>{e.get('event_name')}</b> [{e.get('status')}]\n"
                f"  {e.get('start_at')} — {e.get('end_at')}\n"
                f"  Mamlakatlar: {', '.join(countries) or '-'}"
            )
        await message.answer("🏆 <b>Eventlar</b>\n\n" + "\n".join(lines), parse_mode="HTML")
    except Exception:
        logger.exception("events failed")
        await message.answer("❌ Eventlarni olishda xatolik bo'ldi.")


@router.message(Command("createevent"))
@router.message(F.text == BTN_CREATE_EVENT)
async def cmd_createevent(message: Message, state: FSMContext):
    if not _is_admin(message.from_user.id):
        await message.answer("❌ Sizda admin huquqi yo'q.")
        return
    await state.clear()
    await state.set_state(EventCreateStates.name)
    await message.answer("🏆 Event nomini kiriting:", reply_markup=_cancel_keyboard())


@router.message(EventCreateStates.name)
async def evt_name(message: Message, state: FSMContext):
    await state.update_data(name=message.text.strip())
    await state.set_state(EventCreateStates.description)
    await message.answer("📝 Tavsif kiriting:", reply_markup=_cancel_keyboard())


@router.message(EventCreateStates.description)
async def evt_desc(message: Message, state: FSMContext):
    await state.update_data(description=message.text.strip())
    await state.set_state(EventCreateStates.start_at)
    await message.answer("📅 Boshlanish vaqti (YYYY-MM-DD HH:MM):", reply_markup=_cancel_keyboard())


@router.message(EventCreateStates.start_at)
async def evt_start(message: Message, state: FSMContext):
    await state.update_data(start_at=message.text.strip())
    await state.set_state(EventCreateStates.end_at)
    await message.answer("⏰ Tugash vaqti (YYYY-MM-DD HH:MM):", reply_markup=_cancel_keyboard())


@router.message(EventCreateStates.end_at)
async def evt_end(message: Message, state: FSMContext):
    await state.update_data(end_at=message.text.strip())
    await state.set_state(EventCreateStates.rules)
    await message.answer("📋 Shartlar matnini kiriting:", reply_markup=_cancel_keyboard())


@router.message(EventCreateStates.rules)
async def evt_rules(message: Message, state: FSMContext):
    await state.update_data(rules=message.text.strip())
    await state.set_state(EventCreateStates.countries)
    await message.answer("🌍 Mamlakatlar (vergul bilan): UZ,RU,KG,AZ", reply_markup=_cancel_keyboard())


@router.message(EventCreateStates.countries)
async def evt_countries(message: Message, state: FSMContext):
    codes = [c.strip().upper() for c in message.text.split(",") if c.strip()]
    await state.update_data(countries=codes)
    await state.set_state(EventCreateStates.rewards)
    await message.answer(
        "🎁 Mukofotlar (har biri yangi qatorda):\n"
        "Format: 1|Birinchi o'rin|1000000|UZS\n"
        "Mukofot bo'lmasa: ok",
        reply_markup=_cancel_keyboard(),
    )


@router.message(EventCreateStates.rewards)
async def evt_rewards(message: Message, state: FSMContext):
    try:
        data = await state.get_data()
        rewards = []
        if message.text.strip().lower() != "ok":
            for line in message.text.strip().splitlines():
                parts = [p.strip() for p in line.split("|")]
                if len(parts) >= 3:
                    rewards.append(
                        {
                            "place_number": int(parts[0]),
                            "reward_title": parts[1],
                            "reward_amount": parts[2],
                            "currency_code": parts[3] if len(parts) > 3 else "UZS",
                        }
                    )
        admin = get_admin_by_telegram_id(message.from_user.id)
        event = create_event(
            event_name=data["name"],
            description=data["description"],
            start_at=data["start_at"],
            end_at=data["end_at"],
            rules_text=data["rules"],
            country_codes=data["countries"],
            rewards=rewards,
            created_by_admin_id=admin["admin_id"],
        )
        await state.clear()
        await message.answer(
            f"✅ Event yaratildi!\n🆔 <code>{event['event_id']}</code>\n\n"
            f"Ishga tushirish uchun: {BTN_ACTIVATE_EVENT} tugmasini bosing yoki /activateevent {event['event_id']}",
            parse_mode="HTML",
            reply_markup=_admin_keyboard(admin.get("role_code", "ga")),
        )
    except Exception:
        logger.exception("create event failed")
        await state.clear()
        admin = get_admin_by_telegram_id(message.from_user.id)
        await message.answer(
            "❌ Event yaratishda xatolik bo'ldi.",
            reply_markup=_admin_keyboard(admin.get("role_code", "ga")) if admin else ReplyKeyboardRemove(),
        )


@router.message(Command("activateevent"))
async def cmd_activateevent_command(message: Message):
    await _event_status_by_command(message, "active")


@router.message(Command("pauseevent"))
async def cmd_pauseevent_command(message: Message):
    await _event_status_by_command(message, "paused")


@router.message(Command("finishevent"))
async def cmd_finishevent_command(message: Message):
    await _event_status_by_command(message, "finished")


async def _event_status_by_command(message: Message, status: str):
    try:
        if not _is_admin(message.from_user.id):
            await message.answer("❌ Sizda admin huquqi yo'q.")
            return
        parts = message.text.split()
        if len(parts) < 2:
            await message.answer("Event ID yuboring. Masalan: /activateevent EVT-0001")
            return
        await _change_event_status(message, parts[1], status)
    except Exception:
        logger.exception("event status command failed")
        await message.answer("❌ Event statusini o'zgartirishda xatolik bo'ldi.")


@router.message(F.text == BTN_ACTIVATE_EVENT)
async def ask_activate_event(message: Message, state: FSMContext):
    if not _is_admin(message.from_user.id):
        await message.answer("❌ Sizda admin huquqi yo'q.")
        return
    await state.clear()
    await state.update_data(action="active")
    await state.set_state(EventStatusStates.event_id)
    await message.answer("▶️ Qaysi eventni ishga tushiramiz? Event ID yuboring.", reply_markup=_cancel_keyboard())


@router.message(F.text == BTN_PAUSE_EVENT)
async def ask_pause_event(message: Message, state: FSMContext):
    if not _is_admin(message.from_user.id):
        await message.answer("❌ Sizda admin huquqi yo'q.")
        return
    await state.clear()
    await state.update_data(action="paused")
    await state.set_state(EventStatusStates.event_id)
    await message.answer("⏸ Qaysi eventni pauza qilamiz? Event ID yuboring.", reply_markup=_cancel_keyboard())


@router.message(F.text == BTN_FINISH_EVENT)
async def ask_finish_event(message: Message, state: FSMContext):
    if not _is_admin(message.from_user.id):
        await message.answer("❌ Sizda admin huquqi yo'q.")
        return
    await state.clear()
    await state.update_data(action="finished")
    await state.set_state(EventStatusStates.event_id)
    await message.answer("🏁 Qaysi eventni yakunlaymiz? Event ID yuboring.", reply_markup=_cancel_keyboard())


@router.message(EventStatusStates.event_id)
async def apply_event_status_from_state(message: Message, state: FSMContext):
    data = await state.get_data()
    status = data.get("action")
    event_id = message.text.strip()
    await state.clear()
    await _change_event_status(message, event_id, status)


async def _change_event_status(message: Message, event_id: str, status: str):
    try:
        set_event_status(event_id, status)
        text_map = {
            "active": "✅ Event ishga tushirildi.",
            "paused": "⏸ Event pauza qilindi.",
            "finished": "🏁 Event yakunlandi.",
        }
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
            await message.answer(
                f"{text_map[status]}\n{len(relevant)} xodimga xabar yuborilmoqda.",
                reply_markup=_admin_keyboard(get_admin_by_telegram_id(message.from_user.id).get("role_code", "ga")),
            )
            return
        await message.answer(
            text_map.get(status, "✅ Tayyor."),
            reply_markup=_admin_keyboard(get_admin_by_telegram_id(message.from_user.id).get("role_code", "ga")),
        )
    except Exception as e:
        logger.exception("change event status failed")
        admin = get_admin_by_telegram_id(message.from_user.id)
        await message.answer(
            f"❌ Event statusini o'zgartirib bo'lmadi: {e}",
            reply_markup=_admin_keyboard(admin.get("role_code", "ga")) if admin else ReplyKeyboardRemove(),
        )


@router.message(Command("leaderboard"))
@router.message(F.text == BTN_LEADERBOARD)
async def cmd_leaderboard(message: Message, state: FSMContext):
    if not _is_admin(message.from_user.id):
        await message.answer("❌ Sizda admin huquqi yo'q.")
        return

    parts = message.text.split()
    if message.text.startswith("/leaderboard") and len(parts) >= 3:
        await _send_leaderboard(message, parts[1], parts[2])
        return

    await state.clear()
    await state.set_state(LeaderboardStates.country)
    await message.answer(
        "🥇 Mamlakat kodini yuboring (UZ/RU/KG/AZ).\nHammasi uchun: ALL",
        reply_markup=_cancel_keyboard(),
    )


@router.message(LeaderboardStates.country)
async def lb_country(message: Message, state: FSMContext):
    country = message.text.strip().upper()
    await state.update_data(country=country)
    await state.set_state(LeaderboardStates.period)
    await message.answer("Period yuboring: all / today / week / month", reply_markup=_cancel_keyboard())


@router.message(LeaderboardStates.period)
async def lb_period(message: Message, state: FSMContext):
    data = await state.get_data()
    country = data.get("country", "ALL")
    period = message.text.strip().lower()
    await state.clear()
    await _send_leaderboard(message, country, period)


async def _send_leaderboard(message: Message, country: str, period: str):
    try:
        country_code = None if country in {"ALL", "*", "-"} else country
        period = period if period in {"all", "today", "week", "month"} else "all"
        lb = build_leaderboard(country_code=country_code, period=period, top_n=15)
        if not lb:
            await message.answer("📭 Reyting bo'yicha ma'lumot yo'q.")
            return
        medals = {1: "🥇", 2: "🥈", 3: "🥉"}
        lines = []
        for e in lb:
            m = medals.get(e["rank"], f"{e['rank']}.")
            lines.append(f"{m} {e['full_name']} [{e['country_code']}] — <b>{e['points']}</b>")
        title = country_code or "ALL"
        admin = get_admin_by_telegram_id(message.from_user.id)
        await message.answer(
            f"🥇 <b>Reyting</b> ({title}, {period})\n\n" + "\n".join(lines),
            parse_mode="HTML",
            reply_markup=_admin_keyboard(admin.get("role_code", "ga")) if admin else None,
        )
    except Exception:
        logger.exception("leaderboard failed")
        await message.answer("❌ Reytingni chiqarishda xatolik bo'ldi.")


@router.message(Command("manualpoints"))
@router.message(F.text == BTN_MANUAL_POINTS)
async def cmd_manual_points(message: Message, state: FSMContext):
    if not _is_admin(message.from_user.id):
        await message.answer("❌ Sizda admin huquqi yo'q.")
        return

    parts = message.text.split(maxsplit=3)
    if message.text.startswith("/manualpoints") and len(parts) >= 3:
        code = parts[1]
        try:
            delta = int(parts[2])
        except ValueError:
            await message.answer("❌ Ball noto'g'ri format (+10 yoki -5)")
            return
        reason = parts[3] if len(parts) > 3 else ("manual_bonus" if delta > 0 else "manual_penalty")
        await _apply_manual_points(message, code, delta, reason)
        return

    await state.clear()
    await state.set_state(ManualPointsStates.employee_code)
    await message.answer("💰 Xodim kodini yuboring:", reply_markup=_cancel_keyboard())


@router.message(ManualPointsStates.employee_code)
async def mp_code(message: Message, state: FSMContext):
    await state.update_data(employee_code=message.text.strip())
    await state.set_state(ManualPointsStates.delta)
    await message.answer("Nechta ball? Masalan: 10 yoki -5", reply_markup=_cancel_keyboard())


@router.message(ManualPointsStates.delta)
async def mp_delta(message: Message, state: FSMContext):
    try:
        delta = int(message.text.strip())
    except ValueError:
        await message.answer("❌ Raqam yuboring. Masalan: 10 yoki -5")
        return
    await state.update_data(delta=delta)
    await state.set_state(ManualPointsStates.reason)
    await message.answer("Sabab kiriting. Bo'sh qoldirmang.", reply_markup=_cancel_keyboard())


@router.message(ManualPointsStates.reason)
async def mp_reason(message: Message, state: FSMContext):
    data = await state.get_data()
    await state.clear()
    reason = message.text.strip() or ("manual_bonus" if int(data["delta"]) > 0 else "manual_penalty")
    await _apply_manual_points(message, data["employee_code"], int(data["delta"]), reason)


async def _apply_manual_points(message: Message, code: str, delta: int, reason: str):
    try:
        emp = get_employee_by_code(code)
        if not emp:
            await message.answer(f"❌ Xodim topilmadi: {code}")
            return
        admin = get_admin_by_telegram_id(message.from_user.id)
        manual_adjust(
            employee_id=emp["employee_id"],
            employee_code=emp["employee_code"],
            points_delta=delta,
            reason_code=reason,
            admin_id=admin["admin_id"],
        )
        await message.answer(
            f"✅ {code} ga {delta:+d} ball berildi.\nSabab: {reason}",
            reply_markup=_admin_keyboard(admin.get("role_code", "ga")),
        )
    except Exception:
        logger.exception("manual points failed")
        await message.answer("❌ Qo'lda ball berishda xatolik bo'ldi.")


@router.message(Command("setstatus"))
@router.message(F.text == BTN_SET_STATUS)
async def cmd_setstatus(message: Message, state: FSMContext):
    if not _is_admin(message.from_user.id):
        await message.answer("❌ Sizda admin huquqi yo'q.")
        return

    parts = message.text.split()
    if message.text.startswith("/setstatus") and len(parts) >= 3:
        await _apply_status_change(message, parts[1], parts[2])
        return

    await state.clear()
    await state.set_state(EmployeeStatusStates.employee_code)
    await message.answer("🔒 Xodim kodini yuboring:", reply_markup=_cancel_keyboard())


@router.message(EmployeeStatusStates.employee_code)
async def status_code(message: Message, state: FSMContext):
    await state.update_data(employee_code=message.text.strip())
    await state.set_state(EmployeeStatusStates.status)
    await message.answer("Status yuboring: active / inactive / blocked", reply_markup=_cancel_keyboard())


@router.message(EmployeeStatusStates.status)
async def status_apply(message: Message, state: FSMContext):
    data = await state.get_data()
    await state.clear()
    await _apply_status_change(message, data["employee_code"], message.text.strip())


async def _apply_status_change(message: Message, code: str, status: str):
    try:
        status = status.lower()
        if status not in {"active", "inactive", "blocked"}:
            await message.answer("Status: active | inactive | blocked")
            return
        emp = get_employee_by_code(code)
        if not emp:
            await message.answer(f"❌ Xodim topilmadi: {code}")
            return
        admin = get_admin_by_telegram_id(message.from_user.id)
        update_employee_status(emp["employee_id"], status, updated_by=admin["admin_id"])
        await message.answer(
            f"✅ {code} → {status}",
            reply_markup=_admin_keyboard(admin.get("role_code", "ga")),
        )
    except Exception:
        logger.exception("set status failed")
        await message.answer("❌ Statusni o'zgartirishda xatolik bo'ldi.")


@router.message(Command("systemstats"))
@router.message(F.text == BTN_SYSTEM_STATS)
async def cmd_systemstats(message: Message):
    try:
        if not _is_admin(message.from_user.id):
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
            f"⭐ Jami ball: <b>{stats['points_total']}</b>"
        )
        await message.answer(text, parse_mode="HTML")
    except Exception:
        logger.exception("system stats failed")
        await message.answer("❌ Tizim statistikasini olishda xatolik bo'ldi.")


@router.message(Command("addadmin"))
@router.message(F.text == BTN_ADD_ADMIN)
async def cmd_addadmin(message: Message, state: FSMContext):
    if not _is_super_admin(message.from_user.id):
        await message.answer("❌ Faqat super admin uchun.")
        return

    parts = message.text.split(maxsplit=3)
    if message.text.startswith("/addadmin") and len(parts) >= 4:
        await _apply_add_admin(message, parts[1], parts[2], parts[3])
        return

    await state.clear()
    await state.set_state(AddAdminStates.tg_id)
    await message.answer("➕ Yangi admin/GA Telegram ID sini yuboring:", reply_markup=_cancel_keyboard())


@router.message(AddAdminStates.tg_id)
async def addadmin_tg_id(message: Message, state: FSMContext):
    await state.update_data(tg_id=message.text.strip())
    await state.set_state(AddAdminStates.full_name)
    await message.answer("Ism-familiyasini yuboring:", reply_markup=_cancel_keyboard())


@router.message(AddAdminStates.full_name)
async def addadmin_name(message: Message, state: FSMContext):
    await state.update_data(full_name=message.text.strip())
    await state.set_state(AddAdminStates.role)
    await message.answer("Rol yuboring: ga yoki super_admin", reply_markup=_cancel_keyboard())


@router.message(AddAdminStates.role)
async def addadmin_role(message: Message, state: FSMContext):
    data = await state.get_data()
    await state.clear()
    await _apply_add_admin(message, data["tg_id"], data["full_name"], message.text.strip())


async def _apply_add_admin(message: Message, tg_id: str, full_name: str, role: str):
    try:
        role = role.strip().lower()
        if role not in {"ga", "super_admin"}:
            await message.answer("Rol: ga yoki super_admin")
            return
        creator = get_admin_by_telegram_id(message.from_user.id)
        new_admin = create_admin(
            telegram_user_id=tg_id,
            full_name=full_name,
            phone="",
            role_code=role,
            created_by=creator["admin_id"],
        )
        await message.answer(
            f"✅ Admin yaratildi.\nID: <code>{new_admin['admin_id']}</code>\nRol: <b>{role}</b>",
            parse_mode="HTML",
            reply_markup=_admin_keyboard(creator.get("role_code", "super_admin")),
        )
    except Exception:
        logger.exception("add admin failed")
        await message.answer("❌ Admin qo'shishda xatolik bo'ldi.")