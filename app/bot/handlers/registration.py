"""Registration flow: /start -> language -> phone -> name -> country -> done."""
import logging

from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from app.bot.texts.translations import t
from app.bot.keyboards.main_keyboards import (
    lang_select_keyboard,
    phone_keyboard,
    country_keyboard,
    main_menu_keyboard,
)
from app.services.employees_service import register_employee
from app.services.admins_service import is_admin
from app.services.qr_service import generate_employee_qr
from app.utils.validators import normalize_phone
from app.config import settings

logger = logging.getLogger(__name__)
router = Router()


def _qr_webapp_url(user_id):
    base = f"{str(settings.BASE_URL).rstrip('/')}/miniapp/qr"
    return f"{base}?tg_id={user_id}"


class RegStates(StatesGroup):
    choosing_lang = State()
    sending_phone = State()
    sending_name = State()
    choosing_country = State()


@router.message(F.text == "/start")
async def cmd_start(message: Message, state: FSMContext, employee: dict, lang: str):
    await state.clear()

    admin_mode = is_admin(message.from_user.id)

    if employee and employee.get("status") == "active":
        await message.answer(
            t("reg.already", lang),
            reply_markup=main_menu_keyboard(
                lang,
                is_admin=admin_mode,
                qr_webapp_url=_qr_webapp_url(message.from_user.id),
            ),
        )
        return

    # MUHIM:
    # Admin bo'lsa ham employee bo'lmasa registratsiyani BLOK qilmaymiz
    await state.set_state(RegStates.choosing_lang)
    await message.answer(
        t("start.choose_lang", "uz"),
        reply_markup=lang_select_keyboard(),
    )


@router.callback_query(F.data.startswith("setlang:"), RegStates.choosing_lang)
async def cb_set_lang(cb: CallbackQuery, state: FSMContext):
    lang = cb.data.split(":", 1)[1]
    await state.update_data(lang=lang)
    await state.set_state(RegStates.sending_phone)

    try:
        await cb.message.edit_reply_markup(reply_markup=None)
    except Exception:
        pass

    await cb.message.answer(
        t("reg.send_phone", lang),
        reply_markup=phone_keyboard(lang),
    )
    await cb.answer()


@router.message(RegStates.sending_phone, F.contact)
async def handle_phone_contact(message: Message, state: FSMContext):
    data = await state.get_data()
    lang = data.get("lang", "uz")

    phone = normalize_phone(message.contact.phone_number)
    await state.update_data(phone=phone)
    await state.set_state(RegStates.sending_name)

    await message.answer(t("reg.send_name", lang))


@router.message(RegStates.sending_phone, F.text)
async def handle_phone_text(message: Message, state: FSMContext):
    data = await state.get_data()
    lang = data.get("lang", "uz")

    phone = normalize_phone(message.text)
    if len(phone) < 7:
        await message.answer(
            t("reg.send_phone", lang),
            reply_markup=phone_keyboard(lang),
        )
        return

    await state.update_data(phone=phone)
    await state.set_state(RegStates.sending_name)

    await message.answer(t("reg.send_name", lang))


@router.message(RegStates.sending_name, F.text)
async def handle_name(message: Message, state: FSMContext):
    data = await state.get_data()
    lang = data.get("lang", "uz")

    name = (message.text or "").strip()
    if len(name) < 2:
        await message.answer(t("reg.send_name", lang))
        return

    await state.update_data(name=name)
    await state.set_state(RegStates.choosing_country)

    await message.answer(
        t("reg.choose_country", lang),
        reply_markup=country_keyboard(lang),
    )


@router.callback_query(F.data.startswith("setcountry:"), RegStates.choosing_country)
async def cb_set_country(cb: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    lang = data.get("lang", "uz")
    country_code = cb.data.split(":", 1)[1]
    tg_user = cb.from_user

    try:
        emp = register_employee(
            telegram_user_id=str(tg_user.id),
            telegram_username=tg_user.username or "",
            full_name=data.get("name", ""),
            phone=data.get("phone", ""),
            country_code=country_code,
            language_code=lang,
        )

        generate_employee_qr(
            emp["employee_id"],
            emp["employee_code"],
            country_code,
        )

    except Exception as e:
        logger.exception("Registration error: %s", e)
        await cb.message.answer(t("generic.error", lang))
        await cb.answer()
        return

    await state.clear()

    try:
        await cb.message.edit_reply_markup(reply_markup=None)
    except Exception:
        pass

    await cb.message.answer(
        t("reg.success", lang).format(
            name=emp["full_name"],
            code=emp["employee_code"],
        ),
        reply_markup=main_menu_keyboard(
            lang,
            is_admin=is_admin(cb.from_user.id),
            qr_webapp_url=_qr_webapp_url(cb.from_user.id),
        ),
        parse_mode="HTML",
    )
    await cb.answer()
