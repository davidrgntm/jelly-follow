"""
Keyboards for Telegram bot.
"""
from aiogram.types import (
    ReplyKeyboardMarkup, KeyboardButton,
    InlineKeyboardMarkup, InlineKeyboardButton,
    ReplyKeyboardRemove,
)
from aiogram.utils.keyboard import ReplyKeyboardBuilder, InlineKeyboardBuilder
from app.bot.texts.translations import t

ADMIN_PANEL_TEXT = "👑 Admin panel"


def lang_select_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    langs = [
        ("uz", "🇺🇿 O'zbekcha"),
        ("ru", "🇷🇺 Русский"),
        ("en", "🇬🇧 English"),
        ("kg", "🇰🇬 Кыргызча"),
        ("az", "🇦🇿 Azərbaycanca"),
    ]
    for code, label in langs:
        builder.button(text=label, callback_data=f"setlang:{code}")
    builder.adjust(2)
    return builder.as_markup()


def phone_keyboard(lang: str) -> ReplyKeyboardMarkup:
    builder = ReplyKeyboardBuilder()
    builder.button(text=t("reg.send_phone_btn", lang), request_contact=True)
    return builder.as_markup(resize_keyboard=True, one_time_keyboard=True)


def country_keyboard(lang: str) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    countries = ["UZ", "RU", "KG", "AZ"]
    for cc in countries:
        builder.button(text=t(f"country.{cc}", lang), callback_data=f"setcountry:{cc}")
    builder.adjust(2)
    return builder.as_markup()


def main_menu_keyboard(lang: str, is_admin: bool = False) -> ReplyKeyboardMarkup:
    builder = ReplyKeyboardBuilder()
    buttons = [
        t("menu.profile", lang),
        t("menu.my_qr", lang),
        t("menu.my_link", lang),
        t("menu.stats", lang),
        t("menu.events", lang),
        t("menu.rating", lang),
        t("menu.change_lang", lang),
        t("menu.help", lang),
    ]
    for b in buttons:
        builder.button(text=b)
    if is_admin:
        builder.button(text=ADMIN_PANEL_TEXT)
        builder.adjust(2, 2, 2, 2, 1)
    else:
        builder.adjust(2)
    return builder.as_markup(resize_keyboard=True)


def qr_resend_keyboard(lang: str) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text=t("qr.resend", lang), callback_data="qr:resend")
    return builder.as_markup()


def event_participate_keyboard(lang: str, event_id: str, current_status: str = "") -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    if current_status != "accepted":
        builder.button(text=t("events.join", lang), callback_data=f"event:join:{event_id}")
    if current_status != "declined":
        builder.button(text=t("events.decline", lang), callback_data=f"event:decline:{event_id}")
    builder.adjust(2)
    return builder.as_markup()


def back_keyboard(lang: str) -> ReplyKeyboardMarkup:
    builder = ReplyKeyboardBuilder()
    builder.button(text=t("generic.back", lang))
    return builder.as_markup(resize_keyboard=True, one_time_keyboard=True)


def remove_keyboard() -> ReplyKeyboardRemove:
    return ReplyKeyboardRemove()
