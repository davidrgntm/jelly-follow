"""Multi-language translation system. All bot texts managed here."""

TRANSLATIONS = {
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
    "reg.send_phone": {
        "uz": "📱 Telefon raqamingizni yuboring:", "ru": "📱 Отправьте ваш номер телефона:",
        "en": "📱 Please send your phone number:", "kg": "📱 Телефон номериңизди жөнөтүңүз:",
        "az": "📱 Telefon nömrənizi göndərin:",
    },
    "reg.send_phone_btn": {
        "uz": "📱 Raqamni yuborish", "ru": "📱 Отправить номер",
        "en": "📱 Share phone number", "kg": "📱 Номерди жөнөтүү", "az": "📱 Nömrəni göndər",
    },
    "reg.send_name": {
        "uz": "✍️ To'liq ismingizni kiriting (Familiya Ism):", "ru": "✍️ Введите ваше полное имя (Фамилия Имя):",
        "en": "✍️ Enter your full name (Last First):", "kg": "✍️ Толук атыңызды киргизиңиз:",
        "az": "✍️ Tam adınızı daxil edin:",
    },
    "reg.choose_country": {
        "uz": "🌍 Mamlakatingizni tanlang:", "ru": "🌍 Выберите вашу страну:",
        "en": "🌍 Choose your country:", "kg": "🌍 Өлкөңүздү тандаңыз:", "az": "🌍 Ölkənizi seçin:",
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
        "uz": "ℹ️ Siz allaqachon ro'yxatdan o'tgansiz.", "ru": "ℹ️ Вы уже зарегистрированы.",
        "en": "ℹ️ You are already registered.", "kg": "ℹ️ Сиз мурунтан катталгансыз.",
        "az": "ℹ️ Siz artıq qeydiyyatdan keçmisiniz.",
    },
    "menu.main": {"uz": "🏠 Asosiy menyu", "ru": "🏠 Главное меню", "en": "🏠 Main menu", "kg": "🏠 Башкы меню", "az": "🏠 Əsas menyu"},
    "menu.profile": {"uz": "👤 Profilim", "ru": "👤 Мой профиль", "en": "👤 My profile", "kg": "👤 Менин профилим", "az": "👤 Profilim"},
    "menu.my_qr": {"uz": "📱 QR kodim", "ru": "📱 Мой QR", "en": "📱 My QR code", "kg": "📱 QR кодум", "az": "📱 QR kodum"},
    "menu.my_link": {"uz": "🔗 Mening linkim", "ru": "🔗 Моя ссылка", "en": "🔗 My link", "kg": "🔗 Менин шилтемем", "az": "🔗 Linkim"},
    "menu.stats": {"uz": "📊 Statistikam", "ru": "📊 Статистика", "en": "📊 My stats", "kg": "📊 Статистикам", "az": "📊 Statistikam"},
    "menu.events": {"uz": "🏆 Eventlar", "ru": "🏆 События", "en": "🏆 Events", "kg": "🏆 Иш-чаралар", "az": "🏆 Tədbirlər"},
    "menu.rating": {"uz": "🥇 Reyting", "ru": "🥇 Рейтинг", "en": "🥇 Rating", "kg": "🥇 Рейтинг", "az": "🥇 Reytinq"},
    "menu.change_lang": {"uz": "🌐 Tilni almashtirish", "ru": "🌐 Сменить язык", "en": "🌐 Change language", "kg": "🌐 Тилди алмаштыруу", "az": "🌐 Dili dəyiş"},
    "menu.help": {"uz": "❓ Yordam", "ru": "❓ Помощь", "en": "❓ Help", "kg": "❓ Жардам", "az": "❓ Kömək"},
    "profile.info": {
        "uz": "👤 <b>Profil</b>\n\n📛 Ism: <b>{name}</b>\n📱 Telefon: {phone}\n🌍 Mamlakat: {country}\n🆔 Kod: <code>{code}</code>\n📌 Status: {status}\n⭐ Ballar: <b>{points}</b>",
        "ru": "👤 <b>Профиль</b>\n\n📛 Имя: <b>{name}</b>\n📱 Телефон: {phone}\n🌍 Страна: {country}\n🆔 Код: <code>{code}</code>\n📌 Статус: {status}\n⭐ Баллы: <b>{points}</b>",
        "en": "👤 <b>Profile</b>\n\n📛 Name: <b>{name}</b>\n📱 Phone: {phone}\n🌍 Country: {country}\n🆔 Code: <code>{code}</code>\n📌 Status: {status}\n⭐ Points: <b>{points}</b>",
        "kg": "👤 <b>Профил</b>\n\n📛 Аты: <b>{name}</b>\n📱 Телефон: {phone}\n🌍 Өлкө: {country}\n🆔 Код: <code>{code}</code>\n📌 Статус: {status}\n⭐ Упайлар: <b>{points}</b>",
        "az": "👤 <b>Profil</b>\n\n📛 Ad: <b>{name}</b>\n📱 Telefon: {phone}\n🌍 Ölkə: {country}\n🆔 Kod: <code>{code}</code>\n📌 Status: {status}\n⭐ Ballar: <b>{points}</b>",
    },
    "qr.caption": {
        "uz": "📱 <b>Sizning QR kodingiz</b>\n\n🔗 Link: {link}\n\nMijozlarga shu QR ni ko'rsating!", "ru": "📱 <b>Ваш QR код</b>\n\n🔗 Ссылка: {link}\n\nПокажите этот QR клиентам!",
        "en": "📱 <b>Your QR code</b>\n\n🔗 Link: {link}\n\nShow this QR to customers!", "kg": "📱 <b>Сиздин QR кодуңуз</b>\n\n🔗 Шилтеме: {link}\n\nКардарларга көрсөтүңүз!",
        "az": "📱 <b>QR kodunuz</b>\n\n🔗 Link: {link}\n\nMüştərilərə göstərin!",
    },
    "qr.resend": {"uz": "🔄 Qayta yuborish", "ru": "🔄 Отправить снова", "en": "🔄 Resend", "kg": "🔄 Кайра жөнөтүү", "az": "🔄 Yenidən göndər"},
    "stats.info": {
        "uz": "📊 <b>Statistika</b>\n\n⭐ Jami: <b>{total}</b>\n📅 Bugun: <b>{today}</b>\n📆 Hafta: <b>{week}</b>\n🗓 Oy: <b>{month}</b>\n\n📱 Unique: <b>{unique}</b>\n🔁 Takror: <b>{duplicate}</b>",
        "ru": "📊 <b>Статистика</b>\n\n⭐ Всего: <b>{total}</b>\n📅 Сегодня: <b>{today}</b>\n📆 Неделя: <b>{week}</b>\n🗓 Месяц: <b>{month}</b>\n\n📱 Уникальные: <b>{unique}</b>\n🔁 Повторные: <b>{duplicate}</b>",
        "en": "📊 <b>Statistics</b>\n\n⭐ Total: <b>{total}</b>\n📅 Today: <b>{today}</b>\n📆 Week: <b>{week}</b>\n🗓 Month: <b>{month}</b>\n\n📱 Unique: <b>{unique}</b>\n🔁 Duplicates: <b>{duplicate}</b>",
        "kg": "📊 <b>Статистика</b>\n\n⭐ Бардыгы: <b>{total}</b>\n📅 Бүгүн: <b>{today}</b>\n📆 Апта: <b>{week}</b>\n🗓 Ай: <b>{month}</b>\n\n📱 Уникалдуу: <b>{unique}</b>\n🔁 Кайталанган: <b>{duplicate}</b>",
        "az": "📊 <b>Statistika</b>\n\n⭐ Cəmi: <b>{total}</b>\n📅 Bu gün: <b>{today}</b>\n📆 Həftə: <b>{week}</b>\n🗓 Ay: <b>{month}</b>\n\n📱 Unikal: <b>{unique}</b>\n🔁 Təkrar: <b>{duplicate}</b>",
    },
    "events.list_empty": {
        "uz": "ℹ️ Hozircha faol eventlar yo'q.", "ru": "ℹ️ Активных событий пока нет.",
        "en": "ℹ️ No active events at the moment.", "kg": "ℹ️ Азырча иш-чаралар жок.", "az": "ℹ️ Hal-hazırda aktiv tədbir yoxdur.",
    },
    "events.join": {"uz": "✅ Qatnashaman", "ru": "✅ Участвую", "en": "✅ Join", "kg": "✅ Катышам", "az": "✅ Qatılıram"},
    "events.decline": {"uz": "❌ Qatnashmayman", "ru": "❌ Не участвую", "en": "❌ Decline", "kg": "❌ Катышпайм", "az": "❌ Qatılmıram"},
    "events.joined": {"uz": "✅ Qatnashishingiz tasdiqlandi!", "ru": "✅ Участие подтверждено!", "en": "✅ Participation confirmed!", "kg": "✅ Катышуу тастыкталды!", "az": "✅ İştirak təsdiqləndi!"},
    "events.declined": {"uz": "❌ Rad etildi", "ru": "❌ Отклонено", "en": "❌ Declined", "kg": "❌ Четке кагылды", "az": "❌ İmtina edildi"},
    "rating.title": {"uz": "🥇 <b>{country} reytingi</b>\n\n", "ru": "🥇 <b>Рейтинг {country}</b>\n\n", "en": "🥇 <b>{country} rating</b>\n\n", "kg": "🥇 <b>{country} рейтинги</b>\n\n", "az": "🥇 <b>{country} reytinqi</b>\n\n"},
    "rating.my_rank": {"uz": "\n\n📍 Sizning o'rningiz: <b>{rank}</b>", "ru": "\n\n📍 Ваше место: <b>{rank}</b>", "en": "\n\n📍 Your rank: <b>{rank}</b>", "kg": "\n\n📍 Сиздин ордуңуз: <b>{rank}</b>", "az": "\n\n📍 Sizin yeriniz: <b>{rank}</b>"},
    "rating.empty": {"uz": "ℹ️ Reyting hali bo'sh.", "ru": "ℹ️ Рейтинг пока пуст.", "en": "ℹ️ Rating is empty.", "kg": "ℹ️ Рейтинг бош.", "az": "ℹ️ Reytinq boşdur."},
    "generic.error": {"uz": "❌ Xatolik yuz berdi. Qayta urinib ko'ring.", "ru": "❌ Произошла ошибка.", "en": "❌ An error occurred.", "kg": "❌ Ката кетти.", "az": "❌ Xəta baş verdi."},
    "generic.not_registered": {"uz": "⚠️ Avval ro'yxatdan o'ting: /start", "ru": "⚠️ Сначала зарегистрируйтесь: /start", "en": "⚠️ Register first: /start", "kg": "⚠️ Биринчи катталыңыз: /start", "az": "⚠️ Əvvəlcə qeydiyyatdan keçin: /start"},
    "generic.lang_changed": {"uz": "✅ Til o'zgartirildi!", "ru": "✅ Язык изменён!", "en": "✅ Language changed!", "kg": "✅ Тил алмашты!", "az": "✅ Dil dəyişdirildi!"},
    "help.text": {
        "uz": "❓ <b>Yordam</b>\n\n1. QR kodingizni mijozlarga ko'rsating\n2. Mijoz QR ni skanerlaydi\n3. Instagram sahifasiga o'tadi\n4. Siz ball olasiz!\n\n1 unique qurilma = 1 ball",
        "ru": "❓ <b>Помощь</b>\n\n1. Покажите QR код клиентам\n2. Клиент сканирует QR\n3. Переходит на страницу Instagram\n4. Вы получаете балл!\n\n1 уникальное устройство = 1 балл",
        "en": "❓ <b>Help</b>\n\n1. Show your QR code to customers\n2. Customer scans the QR\n3. They go to Instagram page\n4. You earn a point!\n\n1 unique device = 1 point",
        "kg": "❓ <b>Жардам</b>\n\n1. QR кодуңузду кардарларга көрсөтүңүз\n2. Кардар QR ны скандайт\n3. Инстаграмга өтөт\n4. Сиз упай аласыз!\n\n1 уникалдуу түзүлүш = 1 упай",
        "az": "❓ <b>Kömək</b>\n\n1. QR kodunuzu müştərilərə göstərin\n2. Müştəri QR-ı skan edir\n3. Instagram səhifəsinə keçir\n4. Siz bal qazanırsınız!\n\n1 unikal cihaz = 1 bal",
    },
    "event.notification": {
        "uz": "🏆 <b>Yangi event!</b>\n\n📌 {event_name}\n📝 {description}\n\n📅 {start_at} — {end_at}\n📋 {rules}\n\n🎁 Mukofotlar:\n{rewards}",
        "ru": "🏆 <b>Новое событие!</b>\n\n📌 {event_name}\n📝 {description}\n\n📅 {start_at} — {end_at}\n📋 {rules}\n\n🎁 Призы:\n{rewards}",
        "en": "🏆 <b>New event!</b>\n\n📌 {event_name}\n📝 {description}\n\n📅 {start_at} — {end_at}\n📋 {rules}\n\n🎁 Rewards:\n{rewards}",
        "kg": "🏆 <b>Жаңы иш-чара!</b>\n\n📌 {event_name}\n📝 {description}\n\n📅 {start_at} — {end_at}\n📋 {rules}\n\n🎁 Сыйлыктар:\n{rewards}",
        "az": "🏆 <b>Yeni tədbir!</b>\n\n📌 {event_name}\n📝 {description}\n\n📅 {start_at} — {end_at}\n📋 {rules}\n\n🎁 Mükafatlar:\n{rewards}",
    },
    "event.pool": {
        "uz": "💰 Mukofot puli: <b>{amount} {currency}</b>", "ru": "💰 Призовой фонд: <b>{amount} {currency}</b>",
        "en": "💰 Reward pool: <b>{amount} {currency}</b>", "kg": "💰 Сыйлык пулу: <b>{amount} {currency}</b>",
        "az": "💰 Mükafat fondu: <b>{amount} {currency}</b>",
    },
    "event.qr_sent": {
        "uz": "📱 Event QR kodingiz yuborildi!", "ru": "📱 QR код события отправлен!",
        "en": "📱 Event QR code sent!", "kg": "📱 Иш-чара QR коду жөнөтүлдү!", "az": "📱 Tədbir QR kodu göndərildi!",
    },
    "admin.panel": {
        "uz": "👑 Admin panel", "ru": "👑 Панель админа", "en": "👑 Admin panel",
        "kg": "👑 Админ панели", "az": "👑 Admin paneli",
    },
}


def t(key, lang="uz"):
    entry = TRANSLATIONS.get(key, {})
    return entry.get(lang, entry.get("uz", f"[{key}]"))
