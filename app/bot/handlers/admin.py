"""
Admin handlers.
Commands only accessible to admins/super_admins.
"""
import logging
from aiogram import Router
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.filters import Command

from app.services.admins_service import (
    get_admin_by_telegram_id,
    is_admin,
    is_super_admin,
    create_admin,
    get_system_stats,
)
from app.services.employees_service import get_all_employees, update_employee_status, get_employee_by_code
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


def _admin_check(tg_id) -> bool:
    return is_admin(tg_id)


def _super_check(tg_id) -> bool:
    return is_super_admin(tg_id)


@router.message(Command("admin"))
async def cmd_admin(message: Message):
    tg_id = message.from_user.id
    if not _admin_check(tg_id):
        await message.answer("❌ Sizda admin huquqi yo'q.")
        return

    admin = get_admin_by_telegram_id(tg_id)
    role = admin.get("role_code", "")
    text = (
        f"👑 <b>Admin panel</b>\n\n"
        f"Rol: <b>{role}</b>\n\n"
        f"Buyruqlar:\n"
        f"/employees — xodimlar ro'yxati\n"
        f"/events — eventlar\n"
        f"/leaderboard [CC] [all|today|week|month] — reyting\n"
        f"/eventleaderboard <event_id> [all|today|week|month] — event reytingi\n"
        f"/manualpoints — ball berish\n"
        f"/systemstats — umumiy statistika\n"
    )
    if _super_check(tg_id):
        text += f"/addadmin — yangi admin qo'shish\n"
    await message.answer(text, parse_mode="HTML")


@router.message(Command("employees"))
async def cmd_employees(message: Message):
    if not _admin_check(message.from_user.id):
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


@router.message(Command("setstatus"))
async def cmd_setstatus(message: Message):
    if not _admin_check(message.from_user.id):
        return
    parts = message.text.split()
    if len(parts) < 3:
        await message.answer("Foydalanish: /setstatus <code> <status>\nStatus: active | inactive | blocked")
        return
    code, status = parts[1], parts[2]
    if status not in ("active", "inactive", "blocked"):
        await message.answer("Status: active | inactive | blocked")
        return
    emp = get_employee_by_code(code)
    if not emp:
        await message.answer(f"❌ Xodim topilmadi: {code}")
        return
    admin = get_admin_by_telegram_id(message.from_user.id)
    update_employee_status(emp["employee_id"], status, updated_by=admin["admin_id"])
    await message.answer(f"✅ {code} → {status}")


@router.message(Command("events"))
async def cmd_events(message: Message):
    if not _admin_check(message.from_user.id):
        return
    events = get_all_events()
    if not events:
        await message.answer("📭 Eventlar yo'q.")
        return
    lines = []
    for e in events:
        lines.append(
            f"• <code>{e.get('event_id')}</code> <b>{e.get('event_name')}</b> [{e.get('status')}]\n"
            f"  {e.get('start_at')} — {e.get('end_at')}\n"
            f"  Mamlakatlar: {', '.join(e.get('countries', [])) or '-'}"
        )
    await message.answer("🏆 <b>Eventlar</b>\n\n" + "\n".join(lines), parse_mode="HTML")


class EventCreateStates(StatesGroup):
    name = State()
    description = State()
    start_at = State()
    end_at = State()
    rules = State()
    countries = State()
    rewards = State()


@router.message(Command("createevent"))
async def cmd_createevent(message: Message, state: FSMContext):
    if not _admin_check(message.from_user.id):
        return
    await state.set_state(EventCreateStates.name)
    await message.answer("🏆 Event nomi kiriting:")


@router.message(EventCreateStates.name)
async def evt_name(message: Message, state: FSMContext):
    await state.update_data(name=message.text.strip())
    await state.set_state(EventCreateStates.description)
    await message.answer("📝 Tavsif kiriting:")


@router.message(EventCreateStates.description)
async def evt_desc(message: Message, state: FSMContext):
    await state.update_data(description=message.text.strip())
    await state.set_state(EventCreateStates.start_at)
    await message.answer("📅 Boshlanish vaqti (YYYY-MM-DD HH:MM):")


@router.message(EventCreateStates.start_at)
async def evt_start(message: Message, state: FSMContext):
    await state.update_data(start_at=message.text.strip())
    await state.set_state(EventCreateStates.end_at)
    await message.answer("⏰ Tugash vaqti (YYYY-MM-DD HH:MM):")


@router.message(EventCreateStates.end_at)
async def evt_end(message: Message, state: FSMContext):
    await state.update_data(end_at=message.text.strip())
    await state.set_state(EventCreateStates.rules)
    await message.answer("📋 Shartlar matnini kiriting:")


@router.message(EventCreateStates.rules)
async def evt_rules(message: Message, state: FSMContext):
    await state.update_data(rules=message.text.strip())
    await state.set_state(EventCreateStates.countries)
    await message.answer("🌍 Mamlakatlar (vergul bilan): UZ,RU,KG,AZ")


@router.message(EventCreateStates.countries)
async def evt_countries(message: Message, state: FSMContext):
    codes = [c.strip().upper() for c in message.text.split(",") if c.strip()]
    await state.update_data(countries=codes)
    await state.set_state(EventCreateStates.rewards)
    await message.answer(
        "🎁 Mukofotlar (har biri yangi qatorda):\n"
        "Format: 1|Birinchi o'rin|1000000|UZS\n"
        "Tugagach 'ok' yozing."
    )


@router.message(EventCreateStates.rewards)
async def evt_rewards(message: Message, state: FSMContext):
    data = await state.get_data()
    rewards = []
    if message.text.strip().lower() != "ok":
        for line in message.text.strip().splitlines():
            parts = line.split("|")
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
        f"✅ Event yaratildi!\n🆔 <code>{event['event_id']}</code>\nFaollashtirish: /activateevent {event['event_id']}",
        parse_mode="HTML",
    )


@router.message(Command("activateevent"))
async def cmd_activate_event(message: Message):
    if not _admin_check(message.from_user.id):
        return
    parts = message.text.split()
    if len(parts) < 2:
        await message.answer("Foydalanish: /activateevent <event_id>")
        return
    event_id = parts[1]
    try:
        set_event_status(event_id, "active")
    except ValueError as e:
        await message.answer(f"❌ {e}")
        return

    from app.services.employees_service import get_all_employees

    event = get_event_by_id(event_id)
    countries = get_event_countries(event_id)
    rewards = get_event_rewards(event_id)
    all_emps = get_all_employees()
    relevant = [
        e
        for e in all_emps
        if e.get("country_code", "").upper() in [c.upper() for c in countries] and e.get("status") == "active"
    ]
    import asyncio

    asyncio.create_task(notify_event_started(relevant, event, rewards))
    await message.answer(f"✅ Event faollashtirildi! {len(relevant)} xodimga xabar yuborilmoqda.")


@router.message(Command("pauseevent"))
async def cmd_pause_event(message: Message):
    if not _admin_check(message.from_user.id):
        return
    parts = message.text.split()
    if len(parts) < 2:
        await message.answer("Foydalanish: /pauseevent <event_id>")
        return
    set_event_status(parts[1], "paused")
    await message.answer("⏸ Event to'xtatildi.")


@router.message(Command("finishevent"))
async def cmd_finish_event(message: Message):
    if not _admin_check(message.from_user.id):
        return
    parts = message.text.split()
    if len(parts) < 2:
        await message.answer("Foydalanish: /finishevent <event_id>")
        return
    set_event_status(parts[1], "finished")
    await message.answer("🏁 Event yakunlandi.")


@router.message(Command("leaderboard"))
async def cmd_leaderboard(message: Message):
    if not _admin_check(message.from_user.id):
        return
    parts = message.text.split()
    country = parts[1].upper() if len(parts) > 1 and parts[1].upper() in {"UZ", "RU", "KG", "AZ"} else None
    period = parts[2] if len(parts) > 2 else "all"
    lb = build_leaderboard(country_code=country, period=period, top_n=20)
    if not lb:
        await message.answer("📭 Ma'lumot yo'q.")
        return
    medals = {1: "🥇", 2: "🥈", 3: "🥉"}
    lines = []
    for e in lb:
        m = medals.get(e["rank"], f"{e['rank']}.")
        lines.append(f"{m} {e['full_name']} [{e['country_code']}] — <b>{e['points']}</b>")
    header = f"🥇 Reyting{' — ' + country if country else ''} ({period})\n\n"
    await message.answer(header + "\n".join(lines), parse_mode="HTML")


@router.message(Command("eventleaderboard"))
async def cmd_event_leaderboard(message: Message):
    if not _admin_check(message.from_user.id):
        return
    parts = message.text.split()
    if len(parts) < 2:
        await message.answer("Foydalanish: /eventleaderboard <event_id> [all|today|week|month]")
        return
    event_id = parts[1]
    period = parts[2] if len(parts) > 2 else "all"
    event = get_event_by_id(event_id)
    if not event:
        await message.answer("❌ Event topilmadi")
        return
    lb = build_leaderboard(event_id=event_id, period=period, top_n=20)
    if not lb:
        await message.answer("📭 Event bo'yicha ma'lumot yo'q.")
        return
    medals = {1: "🥇", 2: "🥈", 3: "🥉"}
    lines = []
    for e in lb:
        m = medals.get(e["rank"], f"{e['rank']}.")
        lines.append(f"{m} {e['full_name']} [{e['country_code']}] — <b>{e['points']}</b>")
    await message.answer(f"🏆 <b>{event.get('event_name')}</b> ({period})\n\n" + "\n".join(lines), parse_mode="HTML")


@router.message(Command("manualpoints"))
async def cmd_manual_points(message: Message):
    if not _admin_check(message.from_user.id):
        return
    parts = message.text.split()
    if len(parts) < 3:
        await message.answer("Foydalanish: /manualpoints <code> <+/-N> [sabab]")
        return
    code = parts[1]
    try:
        delta = int(parts[2])
    except ValueError:
        await message.answer("❌ Ball noto'g'ri format (+10 yoki -5)")
        return
    reason = parts[3] if len(parts) > 3 else ("manual_bonus" if delta > 0 else "manual_penalty")
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
    await message.answer(f"✅ {code} ga {delta:+d} ball ({reason})")


@router.message(Command("systemstats"))
async def cmd_systemstats(message: Message):
    if not _admin_check(message.from_user.id):
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


@router.message(Command("addadmin"))
async def cmd_add_admin(message: Message):
    if not _super_check(message.from_user.id):
        await message.answer("❌ Faqat super admin uchun.")
        return
    parts = message.text.split(maxsplit=3)
    if len(parts) < 4:
        await message.answer("Foydalanish: /addadmin <tg_id> <ism> <ga|super_admin>")
        return
    tg_id, name, role = parts[1], parts[2], parts[3]
    if role not in ("ga", "super_admin"):
        await message.answer("Rol: ga yoki super_admin")
        return
    admin = get_admin_by_telegram_id(message.from_user.id)
    new_admin = create_admin(
        telegram_user_id=tg_id,
        full_name=name,
        phone="",
        role_code=role,
        created_by=admin["admin_id"],
    )
    await message.answer(f"✅ Admin yaratildi: {new_admin['admin_id']} ({role})")
