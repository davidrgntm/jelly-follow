"""
Multi-language translation system.
All bot texts managed here. No hardcoded strings in handlers.
"""

TRANSLATIONS: dict[str, dict[str, str]] = {
    # ── Language select ──────────────────────────────────────────────────────
    "start.choose_lang": {
        "uz": "🌐 Tilni tanlang / Выберите язык / Choose language:",
        "ru": "🌐 Tilni tanlang / Выберите язык / Choose language:",
        "en": "🌐 Tilni tanlang / Выберите язык / Choose language:",
        "kg": "🌐 Tilni tanlang / Выберите язык / Choose language:",
        "az": "🌐 Tilni tanlang / Выберите язык / Choose language:",
    },
    "lang.uz": {"uz": "🇺🇿 O'zbekcha", "ru": "🇺🇿 O'zbekcha", "en": "🇺🇿 O'zbekcha", "kg": "🇺🇿 O'zbekcha", "az": "🇺🇿 O'zbekcha"},
    "lang.ru": {"uz": "🇷🇺 Русский", "ru": "🇷🇺 Русский", "en": "🇷🇺 Русский", "kg": "🇷🇺 Русский", "az": "🇷🇺 Русский"},
    "lang.en": {"uz": "🇬🇧 English", "ru": "🇬🇧 English", "en": "🇬🇧 English", "kg": "🇬🇧 English", "az": "🇬🇧 English"},
    "lang.kg": {"uz": "🇰🇬 Кыргызча", "ru": "🇰🇬 Кыргызча", "en": "🇰🇬 Кыргызча", "kg": "🇰🇬 Кыргызча", "az": "🇰🇬 Кыргызча"},
    "lang.az": {"uz": "🇦🇿 Azərbaycanca", "ru": "🇦🇿 Azərbaycanca", "en": "🇦🇿 Azərbaycanca", "kg": "🇦🇿 Azərbaycanca", "az": "🇦🇿 Azərbaycanca"},

    # ── Registration ─────────────────────────────────────────────────────────
    "reg.send_phone": {
        "uz": "📱 Telefon raqamingizni yuboring:",
        "ru": "📱 Отправьте ваш номер телефона:",
        "en": "📱 Please send your phone number:",
        "kg": "📱 Телефон номериңизди жөнөтүңүз:",
        "az": "📱 Telefon nömrənizi göndərin:",
    },
    "reg.send_phone_btn": {
        "uz": "📱 Raqamni yuborish",
        "ru": "📱 Отправить номер",
        "en": "📱 Share phone number",
        "kg": "📱 Номерди жөнөтүү",
        "az": "📱 Nömrəni göndər",
    },
    "reg.send_name": {
        "uz": "✍️ To'liq ismingizni kiriting (Familiya Ism):",
        "ru": "✍️ Введите ваше полное имя (Фамилия Имя):",
        "en": "✍️ Enter your full name (Last First):",
        "kg": "✍️ Толук атыңызды киргизиңиз:",
        "az": "✍️ Tam adınızı daxil edin:",
    },
    "reg.choose_country": {
        "uz": "🌍 Mamlakatingizni tanlang:",
        "ru": "🌍 Выберите вашу страну:",
        "en": "🌍 Choose your country:",
        "kg": "🌍 Өлкөңүздү тандаңыз:",
        "az": "🌍 Ölkənizi seçin:",
    },
    "country.UZ": {"uz": "🇺🇿 O'zbekiston", "ru": "🇺🇿 Узбекистан", "en": "🇺🇿 Uzbekistan", "kg": "🇺🇿 Өзбекстан", "az": "🇺🇿 Özbəkistan"},
    "country.RU": {"uz": "🇷🇺 Rossiya", "ru": "🇷🇺 Россия", "en": "🇷🇺 Russia", "kg": "🇷🇺 Россия", "az": "🇷🇺 Rusiya"},
    "country.KG": {"uz": "🇰🇬 Qirg'iziston", "ru": "🇰🇬 Кыргызстан", "en": "🇰🇬 Kyrgyzstan", "kg": "🇰🇬 Кыргызстан", "az": "🇰🇬 Qırğızstan"},
    "country.AZ": {"uz": "🇦🇿 Ozarbayjon", "ru": "🇦🇿 Азербайджан", "en": "🇦🇿 Azerbaijan", "kg": "🇦🇿 Азербайжан", "az": "🇦🇿 Azərbaycan"},

    "reg.success": {
        "uz": "✅ Ro'yxatdan o'tish muvaffaqiyatli!\n\n👤 Xush kelibsiz, <b>{name}</b>!\n🆔 Sizning kodingiz: <code>{code}</code>",
        "ru": "✅ Регистрация прошла успешно!\n\n👤 Добро пожаловать, <b>{name}</b>!\n🆔 Ваш код: <code>{code}</code>",
        "en": "✅ Registration successful!\n\n👤 Welcome, <b>{name}</b>!\n🆔 Your code: <code>{code}</code>",
        "kg": "✅ Каттоо ийгиликтүү!\n\n👤 Кош келиңиз, <b>{name}</b>!\n🆔 Сиздин кодуңуз: <code>{code}</code>",
        "az": "✅ Qeydiyyat uğurlu oldu!\n\n👤 Xoş gəldiniz, <b>{name}</b>!\n🆔 Sizin kodunuz: <code>{code}</code>",
    },
    "reg.already": {
        "uz": "ℹ️ Siz allaqachon ro'yxatdan o'tgansiz.",
        "ru": "ℹ️ Вы уже зарегистрированы.",
        "en": "ℹ️ You are already registered.",
        "kg": "ℹ️ Сиз мурунтан катталгансыз.",
        "az": "ℹ️ Siz artıq qeydiyyatdan keçmisiniz.",
    },

    # ── Main menu ────────────────────────────────────────────────────────────
    "menu.main": {
        "uz": "🏠 Asosiy menyu",
        "ru": "🏠 Главное меню",
        "en": "🏠 Main menu",
        "kg": "🏠 Башкы меню",
        "az": "🏠 Əsas menyu",
    },
    "menu.profile": {
        "uz": "👤 Profilim",
        "ru": "👤 Мой профиль",
        "en": "👤 My Profile",
        "kg": "👤 Менин профилим",
        "az": "👤 Profilim",
    },
    "menu.my_qr": {
        "uz": "📱 Mening QR kodim",
        "ru": "📱 Мой QR-код",
        "en": "📱 My QR Code",
        "kg": "📱 Менин QR кодум",
        "az": "📱 Mənim QR kodum",
    },
    "menu.my_link": {
        "uz": "🔗 Mening linkim",
        "ru": "🔗 Моя ссылка",
        "en": "🔗 My Link",
        "kg": "🔗 Менин шилтемем",
        "az": "🔗 Mənim linkım",
    },
    "menu.stats": {
        "uz": "📊 Mening statistikam",
        "ru": "📊 Моя статистика",
        "en": "📊 My Stats",
        "kg": "📊 Менин статистикам",
        "az": "📊 Statistikam",
    },
    "menu.events": {
        "uz": "🏆 Eventlar",
        "ru": "🏆 Мероприятия",
        "en": "🏆 Events",
        "kg": "🏆 Иш-чаралар",
        "az": "🏆 Tədbirlər",
    },
    "menu.rating": {
        "uz": "🥇 Reyting",
        "ru": "🥇 Рейтинг",
        "en": "🥇 Rating",
        "kg": "🥇 Рейтинг",
        "az": "🥇 Reytinq",
    },
    "menu.change_lang": {
        "uz": "🌐 Tilni almashtirish",
        "ru": "🌐 Сменить язык",
        "en": "🌐 Change Language",
        "kg": "🌐 Тилди алмаштыруу",
        "az": "🌐 Dili dəyiş",
    },
    "menu.help": {
        "uz": "❓ Yordam",
        "ru": "❓ Помощь",
        "en": "❓ Help",
        "kg": "❓ Жардам",
        "az": "❓ Kömək",
    },

    # ── Profile ──────────────────────────────────────────────────────────────
    "profile.info": {
        "uz": (
            "👤 <b>Mening profilim</b>\n\n"
            "📛 Ism: <b>{name}</b>\n"
            "📱 Telefon: <b>{phone}</b>\n"
            "🌍 Mamlakat: <b>{country}</b>\n"
            "🆔 Kod: <code>{code}</code>\n"
            "📊 Status: <b>{status}</b>\n"
            "⭐ Jami ball: <b>{points}</b>"
        ),
        "ru": (
            "👤 <b>Мой профиль</b>\n\n"
            "📛 Имя: <b>{name}</b>\n"
            "📱 Телефон: <b>{phone}</b>\n"
            "🌍 Страна: <b>{country}</b>\n"
            "🆔 Код: <code>{code}</code>\n"
            "📊 Статус: <b>{status}</b>\n"
            "⭐ Всего очков: <b>{points}</b>"
        ),
        "en": (
            "👤 <b>My Profile</b>\n\n"
            "📛 Name: <b>{name}</b>\n"
            "📱 Phone: <b>{phone}</b>\n"
            "🌍 Country: <b>{country}</b>\n"
            "🆔 Code: <code>{code}</code>\n"
            "📊 Status: <b>{status}</b>\n"
            "⭐ Total points: <b>{points}</b>"
        ),
        "kg": (
            "👤 <b>Менин профилим</b>\n\n"
            "📛 Ат: <b>{name}</b>\n"
            "📱 Телефон: <b>{phone}</b>\n"
            "🌍 Өлкө: <b>{country}</b>\n"
            "🆔 Код: <code>{code}</code>\n"
            "📊 Статус: <b>{status}</b>\n"
            "⭐ Бардык балл: <b>{points}</b>"
        ),
        "az": (
            "👤 <b>Profilim</b>\n\n"
            "📛 Ad: <b>{name}</b>\n"
            "📱 Telefon: <b>{phone}</b>\n"
            "🌍 Ölkə: <b>{country}</b>\n"
            "🆔 Kod: <code>{code}</code>\n"
            "📊 Status: <b>{status}</b>\n"
            "⭐ Ümumi bal: <b>{points}</b>"
        ),
    },

    # ── Stats ─────────────────────────────────────────────────────────────────
    "stats.info": {
        "uz": (
            "📊 <b>Mening statistikam</b>\n\n"
            "⭐ Jami ball: <b>{total}</b>\n"
            "📅 Bugun: <b>{today}</b>\n"
            "📆 Bu hafta: <b>{week}</b>\n"
            "🗓 Bu oy: <b>{month}</b>\n\n"
            "📱 Unique qurilmalar: <b>{unique}</b>\n"
            "🔄 Takror skanlar: <b>{duplicate}</b>"
        ),
        "ru": (
            "📊 <b>Моя статистика</b>\n\n"
            "⭐ Всего: <b>{total}</b>\n"
            "📅 Сегодня: <b>{today}</b>\n"
            "📆 На этой неделе: <b>{week}</b>\n"
            "🗓 В этом месяце: <b>{month}</b>\n\n"
            "📱 Уникальных устройств: <b>{unique}</b>\n"
            "🔄 Повторных сканов: <b>{duplicate}</b>"
        ),
        "en": (
            "📊 <b>My Stats</b>\n\n"
            "⭐ Total: <b>{total}</b>\n"
            "📅 Today: <b>{today}</b>\n"
            "📆 This week: <b>{week}</b>\n"
            "🗓 This month: <b>{month}</b>\n\n"
            "📱 Unique devices: <b>{unique}</b>\n"
            "🔄 Duplicate scans: <b>{duplicate}</b>"
        ),
        "kg": (
            "📊 <b>Менин статистикам</b>\n\n"
            "⭐ Баары: <b>{total}</b>\n"
            "📅 Бүгүн: <b>{today}</b>\n"
            "📆 Бул жума: <b>{week}</b>\n"
            "🗓 Бул ай: <b>{month}</b>\n\n"
            "📱 Уникалдуу түзмөктөр: <b>{unique}</b>\n"
            "🔄 Кайталанган скандар: <b>{duplicate}</b>"
        ),
        "az": (
            "📊 <b>Statistikam</b>\n\n"
            "⭐ Cəmi: <b>{total}</b>\n"
            "📅 Bu gün: <b>{today}</b>\n"
            "📆 Bu həftə: <b>{week}</b>\n"
            "🗓 Bu ay: <b>{month}</b>\n\n"
            "📱 Unikal cihazlar: <b>{unique}</b>\n"
            "🔄 Təkrar skanlar: <b>{duplicate}</b>"
        ),
    },

    # ── QR ───────────────────────────────────────────────────────────────────
    "qr.caption": {
        "uz": "📱 <b>Sizning QR kodingiz</b>\n\n🔗 Link: {link}\n\nMijozga shu QR ni ko'rsating!",
        "ru": "📱 <b>Ваш QR-код</b>\n\n🔗 Ссылка: {link}\n\nПокажите этот QR клиенту!",
        "en": "📱 <b>Your QR Code</b>\n\n🔗 Link: {link}\n\nShow this QR to your customer!",
        "kg": "📱 <b>Сиздин QR кодуңуз</b>\n\n🔗 Шилтеме: {link}\n\nБул QR кодду кардарга көрсөтүңүз!",
        "az": "📱 <b>Sizin QR kodunuz</b>\n\n🔗 Link: {link}\n\nBu QR kodu müştəriyə göstərin!",
    },
    "qr.resend": {
        "uz": "🔄 Qayta yuborish",
        "ru": "🔄 Отправить снова",
        "en": "🔄 Resend",
        "kg": "🔄 Кайра жөнөтүү",
        "az": "🔄 Yenidən göndər",
    },

    # ── Events ───────────────────────────────────────────────────────────────
    "events.list_empty": {
        "uz": "📭 Hozircha faol eventlar yo'q.",
        "ru": "📭 Активных мероприятий пока нет.",
        "en": "📭 No active events at the moment.",
        "kg": "📭 Азырынча жигердүү иш-чаралар жок.",
        "az": "📭 Hazırda aktiv tədbir yoxdur.",
    },
    "events.join": {
        "uz": "✅ Qatnashaman",
        "ru": "✅ Участвую",
        "en": "✅ I'll join",
        "kg": "✅ Катышам",
        "az": "✅ Qatılıram",
    },
    "events.decline": {
        "uz": "❌ Qatnashmayman",
        "ru": "❌ Не участвую",
        "en": "❌ I'll pass",
        "kg": "❌ Катышпайм",
        "az": "❌ Qatılmıram",
    },
    "events.joined": {
        "uz": "✅ Siz eventga ro'yxatdan o'tdingiz!",
        "ru": "✅ Вы зарегистрировались на мероприятие!",
        "en": "✅ You joined the event!",
        "kg": "✅ Сиз иш-чарага катталдыңыз!",
        "az": "✅ Siz tədbirə qeydiyyatdan keçdiniz!",
    },
    "events.declined": {
        "uz": "❌ Siz eventdan voz kechdingiz.",
        "ru": "❌ Вы отказались от участия.",
        "en": "❌ You declined the event.",
        "kg": "❌ Сиз иш-чарадан баш тарттыңыз.",
        "az": "❌ Siz tədbirə qatılmamağı seçdiniz.",
    },

    # ── Event notification ───────────────────────────────────────────────────
    "event.notification": {
        "uz": (
            "🏆 <b>Yangi event boshlandi!</b>\n\n"
            "📌 <b>{event_name}</b>\n"
            "{description}\n\n"
            "📅 Boshlanish: {start_at}\n"
            "⏰ Tugash: {end_at}\n\n"
            "📋 <b>Shartlar:</b>\n{rules}\n\n"
            "🎁 <b>Mukofotlar:</b>\n{rewards}"
        ),
        "ru": (
            "🏆 <b>Новое мероприятие!</b>\n\n"
            "📌 <b>{event_name}</b>\n"
            "{description}\n\n"
            "📅 Начало: {start_at}\n"
            "⏰ Конец: {end_at}\n\n"
            "📋 <b>Условия:</b>\n{rules}\n\n"
            "🎁 <b>Призы:</b>\n{rewards}"
        ),
        "en": (
            "🏆 <b>New Event Started!</b>\n\n"
            "📌 <b>{event_name}</b>\n"
            "{description}\n\n"
            "📅 Start: {start_at}\n"
            "⏰ End: {end_at}\n\n"
            "📋 <b>Rules:</b>\n{rules}\n\n"
            "🎁 <b>Rewards:</b>\n{rewards}"
        ),
        "kg": (
            "🏆 <b>Жаңы иш-чара башталды!</b>\n\n"
            "📌 <b>{event_name}</b>\n"
            "{description}\n\n"
            "📅 Башталышы: {start_at}\n"
            "⏰ Аяктоо: {end_at}\n\n"
            "📋 <b>Шарттар:</b>\n{rules}\n\n"
            "🎁 <b>Сыйлыктар:</b>\n{rewards}"
        ),
        "az": (
            "🏆 <b>Yeni Tədbir Başlandı!</b>\n\n"
            "📌 <b>{event_name}</b>\n"
            "{description}\n\n"
            "📅 Başlanğıc: {start_at}\n"
            "⏰ Bitmə: {end_at}\n\n"
            "📋 <b>Şərtlər:</b>\n{rules}\n\n"
            "🎁 <b>Mükafatlar:</b>\n{rewards}"
        ),
    },

    # ── Rating ───────────────────────────────────────────────────────────────
    "rating.title": {
        "uz": "🥇 <b>Reyting — {country}</b>\n\n",
        "ru": "🥇 <b>Рейтинг — {country}</b>\n\n",
        "en": "🥇 <b>Rating — {country}</b>\n\n",
        "kg": "🥇 <b>Рейтинг — {country}</b>\n\n",
        "az": "🥇 <b>Reytinq — {country}</b>\n\n",
    },
    "rating.my_rank": {
        "uz": "\n\n📍 Sizning o'rningiz: <b>{rank}</b>",
        "ru": "\n\n📍 Ваше место: <b>{rank}</b>",
        "en": "\n\n📍 Your rank: <b>{rank}</b>",
        "kg": "\n\n📍 Сиздин орун: <b>{rank}</b>",
        "az": "\n\n📍 Sizin yeriniz: <b>{rank}</b>",
    },
    "rating.empty": {
        "uz": "📭 Hali reyting ma'lumotlari yo'q.",
        "ru": "📭 Данных рейтинга пока нет.",
        "en": "📭 No rating data yet.",
        "kg": "📭 Рейтинг маалыматтары жок.",
        "az": "📭 Hələ reytinq məlumatı yoxdur.",
    },

    # ── Help ─────────────────────────────────────────────────────────────────
    "help.text": {
        "uz": (
            "❓ <b>Yordam</b>\n\n"
            "Bu bot Jelly xodimlariga mijozlarni Instagram sahifasiga olib kelishni kuzatadi.\n\n"
            "1️⃣ QR kodingizni mijozga ko'rsating\n"
            "2️⃣ Mijoz skanerlaydi va Instagram'ga o'tadi\n"
            "3️⃣ Siz ball to'playsiz\n\n"
            "Muammo bo'lsa adminizga murojaat qiling."
        ),
        "ru": (
            "❓ <b>Помощь</b>\n\n"
            "Этот бот помогает сотрудникам Jelly отслеживать привлечение клиентов в Instagram.\n\n"
            "1️⃣ Покажите QR-код клиенту\n"
            "2️⃣ Клиент сканирует и переходит в Instagram\n"
            "3️⃣ Вы набираете очки\n\n"
            "При проблемах обратитесь к своему администратору."
        ),
        "en": (
            "❓ <b>Help</b>\n\n"
            "This bot helps Jelly employees track Instagram followers.\n\n"
            "1️⃣ Show your QR code to a customer\n"
            "2️⃣ Customer scans and goes to Instagram\n"
            "3️⃣ You earn points\n\n"
            "Contact your admin if you have any issues."
        ),
        "kg": (
            "❓ <b>Жардам</b>\n\n"
            "Бул бот Jelly кызматкерлерине кардарларды Instagram'га тартууну байкоого жардам берет.\n\n"
            "1️⃣ QR кодду кардарга көрсөтүңүз\n"
            "2️⃣ Кардар скандайт жана Instagram'га өтөт\n"
            "3️⃣ Сиз балл топтойсуз\n\n"
            "Көйгөй болсо администраторуңузга кайрылыңыз."
        ),
        "az": (
            "❓ <b>Kömək</b>\n\n"
            "Bu bot Jelly işçilərinə müştəriləri Instagram səhifəsinə cəlb etməyi izləməyə kömək edir.\n\n"
            "1️⃣ QR kodu müştəriyə göstərin\n"
            "2️⃣ Müştəri skan edir və Instagram'a keçir\n"
            "3️⃣ Siz bal toplayırsınız\n\n"
            "Problem olsa admininizdə əlaqə saxlayın."
        ),
    },

    # ── Generic ──────────────────────────────────────────────────────────────
    "generic.not_registered": {
        "uz": "⚠️ Siz ro'yxatdan o'tmagansiz. /start bosing.",
        "ru": "⚠️ Вы не зарегистрированы. Нажмите /start.",
        "en": "⚠️ You are not registered. Press /start.",
        "kg": "⚠️ Сиз катталган эмессиз. /start басыңыз.",
        "az": "⚠️ Qeydiyyatdan keçməmisiniz. /start basın.",
    },
    "generic.error": {
        "uz": "❌ Xatolik yuz berdi. Iltimos qaytadan urinib ko'ring.",
        "ru": "❌ Произошла ошибка. Попробуйте ещё раз.",
        "en": "❌ An error occurred. Please try again.",
        "kg": "❌ Ката кетти. Кайра аракет кылыңыз.",
        "az": "❌ Xəta baş verdi. Yenidən cəhd edin.",
    },
    "generic.back": {
        "uz": "◀️ Orqaga",
        "ru": "◀️ Назад",
        "en": "◀️ Back",
        "kg": "◀️ Артка",
        "az": "◀️ Geri",
    },
    "generic.lang_changed": {
        "uz": "✅ Til o'zgartirildi!",
        "ru": "✅ Язык изменён!",
        "en": "✅ Language changed!",
        "kg": "✅ Тил өзгөртүлдү!",
        "az": "✅ Dil dəyişdirildi!",
    },
}

FALLBACK_LANG = "uz"


def t(key: str, lang: str = "uz") -> str:
    """Get translation for key in given language."""
    lang = lang.lower() if lang else FALLBACK_LANG
    entry = TRANSLATIONS.get(key)
    if entry is None:
        return key  # Return key itself if missing
    return entry.get(lang) or entry.get(FALLBACK_LANG) or key
