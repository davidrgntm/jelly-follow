"""All keyboards — fully button-based."""
from aiogram.types import (
    ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton,
)
from app.bot.texts.translations import t

ADMIN_PANEL_TEXT = "👑 Admin panel"


def admin_panel_text(lang="uz"):
    return t("admin.panel", lang)


def lang_select_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=t("lang.uz", "uz"), callback_data="setlang:uz"),
         InlineKeyboardButton(text=t("lang.ru", "uz"), callback_data="setlang:ru")],
        [InlineKeyboardButton(text=t("lang.en", "uz"), callback_data="setlang:en"),
         InlineKeyboardButton(text=t("lang.kg", "uz"), callback_data="setlang:kg")],
        [InlineKeyboardButton(text=t("lang.az", "uz"), callback_data="setlang:az")],
    ])


def phone_keyboard(lang="uz"):
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text=t("reg.send_phone_btn", lang), request_contact=True)]],
        resize_keyboard=True, one_time_keyboard=True,
    )


def country_keyboard(lang="uz"):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=t("country.UZ", lang), callback_data="setcountry:UZ"),
         InlineKeyboardButton(text=t("country.RU", lang), callback_data="setcountry:RU")],
        [InlineKeyboardButton(text=t("country.KG", lang), callback_data="setcountry:KG"),
         InlineKeyboardButton(text=t("country.AZ", lang), callback_data="setcountry:AZ")],
    ])


def main_menu_keyboard(lang="uz", is_admin=False):
    rows = [
        [KeyboardButton(text=t("menu.profile", lang)), KeyboardButton(text=t("menu.my_qr", lang))],
        [KeyboardButton(text=t("menu.my_link", lang)), KeyboardButton(text=t("menu.stats", lang))],
        [KeyboardButton(text=t("menu.events", lang)), KeyboardButton(text=t("menu.rating", lang))],
        [KeyboardButton(text=t("menu.change_lang", lang)), KeyboardButton(text=t("menu.help", lang))],
    ]
    if is_admin:
        rows.append([KeyboardButton(text=admin_panel_text(lang))])
    return ReplyKeyboardMarkup(keyboard=rows, resize_keyboard=True)


def qr_resend_keyboard(lang="uz"):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=t("qr.resend", lang), callback_data="qr:resend")],
    ])


def event_participate_keyboard(lang, event_id, current_status=""):
    buttons = []
    if current_status != "accepted":
        buttons.append(InlineKeyboardButton(text=t("events.join", lang), callback_data=f"event:join:{event_id}"))
    if current_status != "declined":
        buttons.append(InlineKeyboardButton(text=t("events.decline", lang), callback_data=f"event:decline:{event_id}"))
    if not buttons:
        return None
    return InlineKeyboardMarkup(inline_keyboard=[buttons])
