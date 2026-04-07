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
    "qr.choose_type": {
        "uz": "📱 Kerakli QR turini tanlang:", "ru": "📱 Выберите нужный тип QR:",
        "en": "📱 Choose which QR to send:", "kg": "📱 Кайсы QR керек экенин тандаңыз:",
        "az": "📱 Hansı QR lazım olduğunu seçin:"
    },
    "qr.personal": {
        "uz": "📱 Shaxsiy QR", "ru": "📱 Личный QR",
        "en": "📱 Personal QR", "kg": "📱 Жеке QR", "az": "📱 Şəxsi QR"
    },
    "qr.event_prefix": {
        "uz": "🏆 Event", "ru": "🏆 Событие",
        "en": "🏆 Event", "kg": "🏆 Event", "az": "🏆 Event"
    },
    "qr.event_caption": {
        "uz": "🏆 <b>Event uchun QR kod</b>\n\n📌 Event: <b>{event_name}</b>\n🔗 Link: {link}",
        "ru": "🏆 <b>QR код для события</b>\n\n📌 Событие: <b>{event_name}</b>\n🔗 Ссылка: {link}",
        "en": "🏆 <b>Event QR code</b>\n\n📌 Event: <b>{event_name}</b>\n🔗 Link: {link}",
        "kg": "🏆 <b>Event үчүн QR код</b>\n\n📌 Event: <b>{event_name}</b>\n🔗 Шилтеме: {link}",
        "az": "🏆 <b>Event üçün QR kod</b>\n\n📌 Event: <b>{event_name}</b>\n🔗 Link: {link}"
    },
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
        "uz": "🏆 <b>Yangi event!</b>\n\n📌 <b>{event_name}</b>\n📅 <b>{start_at}</b> — <b>{end_at}</b>\n📝 {description}\n📋 {rules}\n\n🎁 Mukofotlar:\n{rewards}",
        "ru": "🏆 <b>Новое событие!</b>\n\n📌 <b>{event_name}</b>\n📅 <b>{start_at}</b> — <b>{end_at}</b>\n📝 {description}\n📋 {rules}\n\n🎁 Призы:\n{rewards}",
        "en": "🏆 <b>New event!</b>\n\n📌 <b>{event_name}</b>\n📅 <b>{start_at}</b> — <b>{end_at}</b>\n📝 {description}\n📋 {rules}\n\n🎁 Rewards:\n{rewards}",
        "kg": "🏆 <b>Жаңы иш-чара!</b>\n\n📌 <b>{event_name}</b>\n📅 <b>{start_at}</b> — <b>{end_at}</b>\n📝 {description}\n📋 {rules}\n\n🎁 Сыйлыктар:\n{rewards}",
        "az": "🏆 <b>Yeni tədbir!</b>\n\n📌 <b>{event_name}</b>\n📅 <b>{start_at}</b> — <b>{end_at}</b>\n📝 {description}\n📋 {rules}\n\n🎁 Mükafatlar:\n{rewards}",
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

    # ── Scan notification messages ──────────────────────────────────
    "scan.notify.unique": {
        "uz": "✅ <b>+1 ball!</b> Yangi qurilma aniqlandi.\n\n⭐ Jami ballaringiz: <b>{total}</b>\n🏆 Reytingdagi o'rningiz: <b>{rank}</b>",
        "ru": "✅ <b>+1 балл!</b> Обнаружено новое устройство.\n\n⭐ Ваши баллы: <b>{total}</b>\n🏆 Ваше место в рейтинге: <b>{rank}</b>",
        "en": "✅ <b>+1 point!</b> New device detected.\n\n⭐ Your total points: <b>{total}</b>\n🏆 Your rank: <b>{rank}</b>",
        "kg": "✅ <b>+1 упай!</b> Жаңы түзүлүш аныкталды.\n\n⭐ Жалпы упайларыңыз: <b>{total}</b>\n🏆 Рейтингдеги ордуңуз: <b>{rank}</b>",
        "az": "✅ <b>+1 bal!</b> Yeni cihaz aşkarlandı.\n\n⭐ Ümumi ballarınız: <b>{total}</b>\n🏆 Reytinqdəki yeriniz: <b>{rank}</b>",
    },
    "scan.notify.unique_event": {
        "uz": "✅ <b>+1 ball!</b> Yangi qurilma aniqlandi.\n\n📌 Event: <b>{event_name}</b>\n⭐ Event ballari: <b>{event_points}</b>\n⭐ Jami ballaringiz: <b>{total}</b>\n🏆 Reytingdagi o'rningiz: <b>{rank}</b>",
        "ru": "✅ <b>+1 балл!</b> Обнаружено новое устройство.\n\n📌 Событие: <b>{event_name}</b>\n⭐ Баллы события: <b>{event_points}</b>\n⭐ Ваши баллы: <b>{total}</b>\n🏆 Ваше место в рейтинге: <b>{rank}</b>",
        "en": "✅ <b>+1 point!</b> New device detected.\n\n📌 Event: <b>{event_name}</b>\n⭐ Event points: <b>{event_points}</b>\n⭐ Your total points: <b>{total}</b>\n🏆 Your rank: <b>{rank}</b>",
        "kg": "✅ <b>+1 упай!</b> Жаңы түзүлүш аныкталды.\n\n📌 Иш-чара: <b>{event_name}</b>\n⭐ Иш-чара упайлары: <b>{event_points}</b>\n⭐ Жалпы упайларыңыз: <b>{total}</b>\n🏆 Рейтингдеги ордуңуз: <b>{rank}</b>",
        "az": "✅ <b>+1 bal!</b> Yeni cihaz aşkarlandı.\n\n📌 Tədbir: <b>{event_name}</b>\n⭐ Tədbir balları: <b>{event_points}</b>\n⭐ Ümumi ballarınız: <b>{total}</b>\n🏆 Reytinqdəki yeriniz: <b>{rank}</b>",
    },
    "scan.notify.duplicate": {
        "uz": "🔁 Bu qurilma avval skanerlangan.\n\nBall berilmadi. Yangi qurilmadan skanerlab ko'ring!\n⭐ Jami ballaringiz: <b>{total}</b>",
        "ru": "🔁 Это устройство уже сканировало.\n\nБалл не начислен. Попробуйте с нового устройства!\n⭐ Ваши баллы: <b>{total}</b>",
        "en": "🔁 This device already scanned.\n\nNo point awarded. Try with a new device!\n⭐ Your total points: <b>{total}</b>",
        "kg": "🔁 Бул түзүлүш мурун скандалган.\n\nУпай берилген жок. Жаңы түзүлүш менен аракет кылыңыз!\n⭐ Жалпы упайларыңыз: <b>{total}</b>",
        "az": "🔁 Bu cihaz artıq skan edilib.\n\nBal verilmədi. Yeni cihazdan sınayın!\n⭐ Ümumi ballarınız: <b>{total}</b>",
    },
    "scan.notify.suspicious": {
        "uz": "⚠️ Shubhali skan aniqlandi.\n\nBu urinish hisoblanmadi. Agar xatolik bo'lsa, adminga murojaat qiling.",
        "ru": "⚠️ Обнаружено подозрительное сканирование.\n\nЭта попытка не засчитана. Если ошибка — обратитесь к администратору.",
        "en": "⚠️ Suspicious scan detected.\n\nThis attempt was not counted. If this is an error, contact admin.",
        "kg": "⚠️ Шектүү скан аныкталды.\n\nБул аракет эсептелген жок. Ката болсо, админге кайрылыңыз.",
        "az": "⚠️ Şübhəli skan aşkarlandı.\n\nBu cəhd sayılmadı. Xəta olarsa, adminə müraciət edin.",
    },
    "scan.notify.retry": {
        "uz": "🔄 Skan qayta ishlandi.\n\n⭐ Jami ballaringiz: <b>{total}</b>",
        "ru": "🔄 Скан повторно обработан.\n\n⭐ Ваши баллы: <b>{total}</b>",
        "en": "🔄 Scan reprocessed.\n\n⭐ Your total points: <b>{total}</b>",
        "kg": "🔄 Скан кайра иштелди.\n\n⭐ Жалпы упайларыңыз: <b>{total}</b>",
        "az": "🔄 Skan yenidən işləndi.\n\n⭐ Ümumi ballarınız: <b>{total}</b>",
    },

    "admin.panel": {
        "uz": "👑 Admin panel", "ru": "👑 Панель админа", "en": "👑 Admin panel",
        "kg": "👑 Админ панели", "az": "👑 Admin paneli",
    },
}


ADMIN_TRANSLATIONS = {
    "admin.panel.open_hint": {
        "uz": "Pastdagi tugma orqali admin panelni oching.",
        "ru": "Откройте панель администратора кнопкой ниже.",
        "en": "Open the admin panel using the button below.",
        "kg": "Төмөнкү баскыч аркылуу админ панелин ачыңыз.",
        "az": "Aşağıdakı düymə ilə admin panelini açın.",
    },
    "admin.menu.events": {"uz": "🏆 Event boshqaruvi", "ru": "🏆 Управление событиями", "en": "🏆 Event management", "kg": "🏆 Иш-чараларды башкаруу", "az": "🏆 Tədbir idarəsi"},
    "admin.menu.create_event": {"uz": "➕ Yangi event", "ru": "➕ Новое событие", "en": "➕ New event", "kg": "➕ Жаңы иш-чара", "az": "➕ Yeni tədbir"},
    "admin.menu.employees": {"uz": "👥 Xodimlar", "ru": "👥 Сотрудники", "en": "👥 Employees", "kg": "👥 Кызматкерлер", "az": "👥 İşçilər"},
    "admin.menu.leaderboard": {"uz": "🥇 Event reytingi", "ru": "🥇 Рейтинг event'ов", "en": "🥇 Event leaderboard", "kg": "🥇 Event рейтинги", "az": "🥇 Event reytinqi"},
    "admin.menu.manual_points": {"uz": "💰 Ball berish", "ru": "💰 Выдать баллы", "en": "💰 Manual points", "kg": "💰 Упай берүү", "az": "💰 Bal vermək"},
    "admin.menu.employee_status": {"uz": "🔒 Xodim statusi", "ru": "🔒 Статус сотрудника", "en": "🔒 Employee status", "kg": "🔒 Кызматкер статусу", "az": "🔒 İşçi statusu"},
    "admin.menu.stats": {"uz": "📊 Tizim statistikasi", "ru": "📊 Статистика системы", "en": "📊 System statistics", "kg": "📊 Система статистикасы", "az": "📊 Sistem statistikası"},
    "admin.menu.broadcast": {"uz": "📣 Xabar yuborish (barchaga)", "ru": "📣 Отправить сообщение (всем)", "en": "📣 Send message (to all)", "kg": "📣 Билдирүү жөнөтүү (баарына)", "az": "📣 Mesaj göndər (hamıya)"},
    "admin.menu.send_update": {"uz": "📢 Yangilanish xabari", "ru": "📢 Сообщение об обновлении", "en": "📢 Update message", "kg": "📢 Жаңыртуу билдирүүсү", "az": "📢 Yenilənmə mesajı"},
    "admin.menu.language": {"uz": "🌐 Til", "ru": "🌐 Язык", "en": "🌐 Language", "kg": "🌐 Тил", "az": "🌐 Dil"},
    "admin.menu.add_admin": {"uz": "➕ GA/Admin qo'shish", "ru": "➕ Добавить GA/Admin", "en": "➕ Add GA/Admin", "kg": "➕ GA/Admin кошуу", "az": "➕ GA/Admin əlavə et"},
    "admin.menu.back_employee": {"uz": "⬅️ Xodim menyusi", "ru": "⬅️ Меню сотрудника", "en": "⬅️ Employee menu", "kg": "⬅️ Кызматкер менюсу", "az": "⬅️ İşçi menyusu"},
    "admin.cancel": {"uz": "❌ Bekor qilish", "ru": "❌ Отмена", "en": "❌ Cancel", "kg": "❌ Жокко чыгаруу", "az": "❌ Ləğv et"},
    "admin.continue": {"uz": "✅ Davom etish", "ru": "✅ Продолжить", "en": "✅ Continue", "kg": "✅ Улантуу", "az": "✅ Davam et"},
    "admin.create": {"uz": "✅ Yaratish", "ru": "✅ Создать", "en": "✅ Create", "kg": "✅ Түзүү", "az": "✅ Yarat"},
    "admin.no_permission": {"uz": "⛔ Sizda admin huquqi yo'q.", "ru": "⛔ У вас нет прав администратора.", "en": "⛔ You do not have admin access.", "kg": "⛔ Сизде админ укугу жок.", "az": "⛔ Sizin admin icazəniz yoxdur."},
    "admin.super_admin_only": {"uz": "⛔ Faqat Super Admin uchun.", "ru": "⛔ Только для Super Admin.", "en": "⛔ Super Admin only.", "kg": "⛔ Super Admin үчүн гана.", "az": "⛔ Yalnız Super Admin üçün."},
    "admin.cancelled": {"uz": "❌ Bekor qilindi", "ru": "❌ Отменено", "en": "❌ Cancelled", "kg": "❌ Жокко чыгарылды", "az": "❌ Ləğv edildi"},
    "admin.panel.title": {"uz": "👑 Admin panel", "ru": "👑 Панель администратора", "en": "👑 Admin panel", "kg": "👑 Админ панели", "az": "👑 Admin paneli"},
    "admin.language.choose": {"uz": "🌐 Tilni tanlang:", "ru": "🌐 Выберите язык:", "en": "🌐 Choose language:", "kg": "🌐 Тилди тандаңыз:", "az": "🌐 Dili seçin:"},
    "admin.stats.title": {"uz": "📊 <b>Tizim statistikasi</b>", "ru": "📊 <b>Статистика системы</b>", "en": "📊 <b>System statistics</b>", "kg": "📊 <b>Системалык статистика</b>", "az": "📊 <b>Sistem statistikası</b>"},
    "admin.stats.employees": {"uz": "👥 Xodimlar: {active}/{total}", "ru": "👥 Сотрудники: {active}/{total}", "en": "👥 Employees: {active}/{total}", "kg": "👥 Кызматкерлер: {active}/{total}", "az": "👥 İşçilər: {active}/{total}"},
    "admin.stats.admins": {"uz": "👑 Adminlar: {total}", "ru": "👑 Админы: {total}", "en": "👑 Admins: {total}", "kg": "👑 Админдер: {total}", "az": "👑 Adminlər: {total}"},
    "admin.stats.events": {"uz": "🏆 Eventlar: {active} faol / {total} jami", "ru": "🏆 События: {active} активных / {total} всего", "en": "🏆 Events: {active} active / {total} total", "kg": "🏆 Иш-чаралар: {active} активдүү / {total} жалпы", "az": "🏆 Tədbirlər: {active} aktiv / {total} ümumi"},
    "admin.stats.scans": {"uz": "📱 Skanlar: {total}", "ru": "📱 Сканов: {total}", "en": "📱 Scans: {total}", "kg": "📱 Скан: {total}", "az": "📱 Skanlar: {total}"},
    "admin.stats.unique": {"uz": "✅ Unique: {total}", "ru": "✅ Уникальные: {total}", "en": "✅ Unique: {total}", "kg": "✅ Уникалдуу: {total}", "az": "✅ Unikal: {total}"},
    "admin.stats.duplicate": {"uz": "🔁 Takror: {total}", "ru": "🔁 Повторные: {total}", "en": "🔁 Duplicates: {total}", "kg": "🔁 Кайталанган: {total}", "az": "🔁 Təkrar: {total}"},
    "admin.stats.suspicious": {"uz": "⚠️ Shubhali: {total}", "ru": "⚠️ Подозрительные: {total}", "en": "⚠️ Suspicious: {total}", "kg": "⚠️ Шектүү: {total}", "az": "⚠️ Şübhəli: {total}"},
    "admin.stats.points": {"uz": "⭐ Jami ball: {total}", "ru": "⭐ Всего баллов: {total}", "en": "⭐ Total points: {total}", "kg": "⭐ Жалпы упай: {total}", "az": "⭐ Ümumi bal: {total}"},
    "admin.stats.countries": {"uz": "🌍 Mamlakatlar:", "ru": "🌍 Страны:", "en": "🌍 Countries:", "kg": "🌍 Өлкөлөр:", "az": "🌍 Ölkələr:"},
    "admin.employees.title": {"uz": "👥 <b>Xodimlar</b> ({active} faol / {total} jami)", "ru": "👥 <b>Сотрудники</b> ({active} активных / {total} всего)", "en": "👥 <b>Employees</b> ({active} active / {total} total)", "kg": "👥 <b>Кызматкерлер</b> ({active} активдүү / {total} жалпы)", "az": "👥 <b>İşçilər</b> ({active} aktiv / {total} ümumi)"},
    "admin.employees.empty": {"uz": "ℹ️ Xodimlar yo'q.", "ru": "ℹ️ Сотрудников нет.", "en": "ℹ️ No employees yet.", "kg": "ℹ️ Кызматкерлер жок.", "az": "ℹ️ İşçi yoxdur."},
    "admin.events.empty": {"uz": "ℹ️ Eventlar yo'q.", "ru": "ℹ️ Событий нет.", "en": "ℹ️ No events yet.", "kg": "ℹ️ Иш-чаралар жок.", "az": "ℹ️ Tədbir yoxdur."},
    "admin.events.title": {"uz": "🥇 <b>Event reytingi</b>", "ru": "🥇 <b>Рейтинг события</b>", "en": "🥇 <b>Event leaderboard</b>", "kg": "🥇 <b>Иш-чара рейтинги</b>", "az": "🥇 <b>Tədbir reytinqi</b>"},
    "admin.event.action.activate": {"uz": "▶️ Boshlash (active)", "ru": "▶️ Запустить (active)", "en": "▶️ Activate", "kg": "▶️ Баштоо", "az": "▶️ Aktiv et"},
    "admin.event.action.pause": {"uz": "⏸ Pauza", "ru": "⏸ Пауза", "en": "⏸ Pause", "kg": "⏸ Тыныгуу", "az": "⏸ Pauza"},
    "admin.event.action.finish": {"uz": "🏁 Tugatish", "ru": "🏁 Завершить", "en": "🏁 Finish", "kg": "🏁 Аяктоо", "az": "🏁 Bitir"},
    "admin.event.action.resume": {"uz": "▶️ Davom", "ru": "▶️ Продолжить", "en": "▶️ Resume", "kg": "▶️ Улантуу", "az": "▶️ Davam et"},
    "admin.event.action.leaderboard": {"uz": "🥇 Reyting", "ru": "🥇 Рейтинг", "en": "🥇 Leaderboard", "kg": "🥇 Рейтинг", "az": "🥇 Reytinq"},
    "admin.event.status_changed": {"uz": "✅ Event → {status}", "ru": "✅ Событие → {status}", "en": "✅ Event → {status}", "kg": "✅ Иш-чара → {status}", "az": "✅ Tədbir → {status}"},
    "admin.event.name_prompt": {"uz": "📝 Event nomini kiriting:", "ru": "📝 Введите название события:", "en": "📝 Enter the event name:", "kg": "📝 Иш-чаранын атын киргизиңиз:", "az": "📝 Tədbirin adını daxil edin:"},
    "admin.event.name_short": {"uz": "⚠️ Nomi juda qisqa. Qayta kiriting:", "ru": "⚠️ Название слишком короткое. Введите снова:", "en": "⚠️ Name is too short. Enter again:", "kg": "⚠️ Ат өтө кыска. Кайра жазыңыз:", "az": "⚠️ Ad çox qısadır. Yenidən daxil edin:"},
    "admin.event.description_prompt": {"uz": "📝 Event tavsifini kiriting:", "ru": "📝 Введите описание события:", "en": "📝 Enter the event description:", "kg": "📝 Иш-чаранын сүрөттөмөсүн киргизиңиз:", "az": "📝 Tədbirin təsvirini daxil edin:"},
    "admin.event.rules_prompt": {"uz": "📋 Event shartlarini kiriting:", "ru": "📋 Введите условия события:", "en": "📋 Enter the event rules:", "kg": "📋 Иш-чаранын шарттарын киргизиңиз:", "az": "📋 Tədbir qaydalarını daxil edin:"},
    "admin.event.countries_prompt": {"uz": "🌍 Mamlakatlarni tanlang:", "ru": "🌍 Выберите страны:", "en": "🌍 Choose countries:", "kg": "🌍 Өлкөлөрдү тандаңыз:", "az": "🌍 Ölkələri seçin:"},
    "admin.event.select_one_country": {"uz": "Kamida 1 mamlakat tanlang!", "ru": "Выберите хотя бы 1 страну!", "en": "Select at least 1 country!", "kg": "Кеминде 1 өлкөнү тандаңыз!", "az": "Ən azı 1 ölkə seçin!"},
    "admin.event.start_date": {"uz": "📅 Boshlanish sanasi:", "ru": "📅 Дата начала:", "en": "📅 Start date:", "kg": "📅 Башталыш күнү:", "az": "📅 Başlanğıc tarixi:"},
    "admin.event.start_hour": {"uz": "📅 Boshlanish: {date}\n⏰ Soatni tanlang:", "ru": "📅 Начало: {date}\n⏰ Выберите час:", "en": "📅 Start: {date}\n⏰ Choose hour:", "kg": "📅 Башталышы: {date}\n⏰ Саатты тандаңыз:", "az": "📅 Başlanğıc: {date}\n⏰ Saat seçin:"},
    "admin.event.end_date": {"uz": "📅 Tugash sanasi:", "ru": "📅 Дата окончания:", "en": "📅 End date:", "kg": "📅 Аяктоо күнү:", "az": "📅 Bitiş tarixi:"},
    "admin.event.end_hour": {"uz": "📅 Tugash: {date}\n⏰ Soatni tanlang:", "ru": "📅 Окончание: {date}\n⏰ Выберите час:", "en": "📅 End: {date}\n⏰ Choose hour:", "kg": "📅 Аягы: {date}\n⏰ Саатты тандаңыз:", "az": "📅 Bitiş: {date}\n⏰ Saat seçin:"},
    "admin.event.pool_prompt": {"uz": "💰 Mukofot puli (umumiy summa):", "ru": "💰 Призовой фонд (общая сумма):", "en": "💰 Reward pool (total amount):", "kg": "💰 Байге фонду (жалпы сумма):", "az": "💰 Mükafat fondu (ümumi məbləğ):"},
    "admin.event.currency_prompt": {"uz": "💰 Summa: {amount}\n💱 Valyutani tanlang:", "ru": "💰 Сумма: {amount}\n💱 Выберите валюту:", "en": "💰 Amount: {amount}\n💱 Choose currency:", "kg": "💰 Сумма: {amount}\n💱 Валютаны тандаңыз:", "az": "💰 Məbləğ: {amount}\n💱 Valyutanı seçin:"},
    "admin.event.reward_count_prompt": {"uz": "🎁 Nechta o'rin uchun mukofot?", "ru": "🎁 Для скольких мест будет награда?", "en": "🎁 How many rewarded places?", "kg": "🎁 Канча орунга сыйлык болот?", "az": "🎁 Neçə yer üçün mükafat olacaq?"},
    "admin.event.reward_none": {"uz": "Mukofot yo'q", "ru": "Без наград", "en": "No rewards", "kg": "Сыйлык жок", "az": "Mükafat yoxdur"},
    "admin.event.reward_top3": {"uz": "Top 3 (3 o'rin)", "ru": "Top 3 (3 места)", "en": "Top 3", "kg": "Top 3", "az": "Top 3"},
    "admin.event.reward_top5": {"uz": "Top 5 (5 o'rin)", "ru": "Top 5 (5 мест)", "en": "Top 5", "kg": "Top 5", "az": "Top 5"},
    "admin.event.reward_top10": {"uz": "Top 10 (10 o'rin)", "ru": "Top 10 (10 мест)", "en": "Top 10", "kg": "Top 10", "az": "Top 10"},
    "admin.event.reward_place_prompt": {"uz": "🎁 <b>{place}-o'rin</b> mukofot summasini kiriting ({currency}):\n\nRaqam kiriting yoki 0 bosing:", "ru": "🎁 <b>{place}-е место</b>: введите сумму награды ({currency}):\n\nВведите число или 0:", "en": "🎁 <b>Place {place}</b>: enter reward amount ({currency}):\n\nEnter a number or 0:", "kg": "🎁 <b>{place}-орун</b> үчүн сыйлык суммасын киргизиңиз ({currency}):\n\nСан же 0 жазыңыз:", "az": "🎁 <b>{place}-ci yer</b> üçün mükafat məbləğini daxil edin ({currency}):\n\nRəqəm və ya 0 daxil edin:"},
    "admin.only_number": {"uz": "⚠️ Faqat raqam kiriting:", "ru": "⚠️ Введите только число:", "en": "⚠️ Enter numbers only:", "kg": "⚠️ Сан гана киргизиңиз:", "az": "⚠️ Yalnız rəqəm daxil edin:"},
    "admin.event.confirm_title": {"uz": "📝 <b>Event tekshiruv</b>", "ru": "📝 <b>Проверка события</b>", "en": "📝 <b>Review event</b>", "kg": "📝 <b>Иш-чараны текшерүү</b>", "az": "📝 <b>Tədbiri yoxla</b>"},
    "admin.event.confirm_name": {"uz": "📌 Nomi: <b>{value}</b>", "ru": "📌 Название: <b>{value}</b>", "en": "📌 Name: <b>{value}</b>", "kg": "📌 Аты: <b>{value}</b>", "az": "📌 Adı: <b>{value}</b>"},
    "admin.event.confirm_description": {"uz": "📝 Tavsif: {value}", "ru": "📝 Описание: {value}", "en": "📝 Description: {value}", "kg": "📝 Сүрөттөмө: {value}", "az": "📝 Təsvir: {value}"},
    "admin.event.confirm_rules": {"uz": "📋 Shartlar: {value}", "ru": "📋 Условия: {value}", "en": "📋 Rules: {value}", "kg": "📋 Шарттар: {value}", "az": "📋 Qaydalar: {value}"},
    "admin.event.confirm_countries": {"uz": "🌍 Mamlakatlar: {value}", "ru": "🌍 Страны: {value}", "en": "🌍 Countries: {value}", "kg": "🌍 Өлкөлөр: {value}", "az": "🌍 Ölkələr: {value}"},
    "admin.event.confirm_dates": {"uz": "📅 {start} — {end}", "ru": "📅 {start} — {end}", "en": "📅 {start} — {end}", "kg": "📅 {start} — {end}", "az": "📅 {start} — {end}"},
    "admin.event.confirm_pool": {"uz": "💰 Mukofot puli: {amount} {currency}", "ru": "💰 Призовой фонд: {amount} {currency}", "en": "💰 Reward pool: {amount} {currency}", "kg": "💰 Сыйлык фонду: {amount} {currency}", "az": "💰 Mükafat fondu: {amount} {currency}"},
    "admin.event.confirm_rewards": {"uz": "🎁 Mukofotlar:", "ru": "🎁 Награды:", "en": "🎁 Rewards:", "kg": "🎁 Сыйлыктар:", "az": "🎁 Mükafatlar:"},
    "admin.event.confirm_ask": {"uz": "Tasdiqlaysizmi?", "ru": "Подтверждаете?", "en": "Confirm?", "kg": "Тастыктайсызбы?", "az": "Təsdiqləyirsiniz?"},
    "admin.event.created": {"uz": "✅ Event yaratildi!\n\n🆔 <code>{event_id}</code>\n📌 Status: active", "ru": "✅ Событие создано!\n\n🆔 <code>{event_id}</code>\n📌 Статус: active", "en": "✅ Event created!\n\n🆔 <code>{event_id}</code>\n📌 Status: active", "kg": "✅ Иш-чара түзүлдү!\n\n🆔 <code>{event_id}</code>\n📌 Статус: active", "az": "✅ Tədbir yaradıldı!\n\n🆔 <code>{event_id}</code>\n📌 Status: active"},
    "admin.event.choose_country": {"uz": "🌍 Mamlakatni tanlang:", "ru": "🌍 Выберите страну:", "en": "🌍 Choose country:", "kg": "🌍 Өлкөнү тандаңыз:", "az": "🌍 Ölkəni seçin:"},
    "admin.leaderboard.empty": {"uz": "Reyting bo'sh", "ru": "Рейтинг пуст", "en": "Leaderboard is empty", "kg": "Рейтинг бош", "az": "Reytinq boşdur"},
    "admin.broadcast.prompt": {"uz": "📣 <b>Barchaga yuboriladigan xabarni yuboring</b>\n\nHTML format ishlaydi. Masalan:\n&lt;b&gt;Muhim&lt;/b&gt; xabar", "ru": "📣 <b>Отправьте сообщение для всех</b>\n\nМожно использовать HTML. Например:\n&lt;b&gt;Важное&lt;/b&gt; сообщение", "en": "📣 <b>Send the message for everyone</b>\n\nHTML formatting works. Example:\n&lt;b&gt;Important&lt;/b&gt; message", "kg": "📣 <b>Баарына жөнөтүлө турган билдирүүнү жазыңыз</b>\n\nHTML иштейт. Мисалы:\n&lt;b&gt;Маанилүү&lt;/b&gt; билдирүү", "az": "📣 <b>Hamıya göndəriləcək mesajı yazın</b>\n\nHTML işləyir. Məsələn:\n&lt;b&gt;Vacib&lt;/b&gt; mesaj"},
    "admin.broadcast.empty": {"uz": "❌ Xabar bo'sh bo'lmasligi kerak.", "ru": "❌ Сообщение не должно быть пустым.", "en": "❌ Message cannot be empty.", "kg": "❌ Билдирүү бош болбошу керек.", "az": "❌ Mesaj boş ola bilməz."},
    "admin.broadcast.done": {"uz": "✅ Xabar yuborildi.\n\n📨 Yuborildi: <b>{sent}</b>\n❌ Xatolik: <b>{failed}</b>\n👥 Jami: <b>{total}</b>", "ru": "✅ Сообщение отправлено.\n\n📨 Отправлено: <b>{sent}</b>\n❌ Ошибки: <b>{failed}</b>\n👥 Всего: <b>{total}</b>", "en": "✅ Message sent.\n\n📨 Sent: <b>{sent}</b>\n❌ Failed: <b>{failed}</b>\n👥 Total: <b>{total}</b>", "kg": "✅ Билдирүү жөнөтүлдү.\n\n📨 Жөнөтүлдү: <b>{sent}</b>\n❌ Ката: <b>{failed}</b>\n👥 Жалпы: <b>{total}</b>", "az": "✅ Mesaj göndərildi.\n\n📨 Göndərildi: <b>{sent}</b>\n❌ Xəta: <b>{failed}</b>\n👥 Cəmi: <b>{total}</b>"},
    "admin.manual_points.enter_code": {"uz": "🆔 Xodim kodini kiriting (masalan UZ-0001):", "ru": "🆔 Введите код сотрудника (например UZ-0001):", "en": "🆔 Enter employee code (for example UZ-0001):", "kg": "🆔 Кызматкер кодун киргизиңиз (мисалы UZ-0001):", "az": "🆔 İşçi kodunu daxil edin (məsələn UZ-0001):"},
    "admin.employee_status.enter_code": {"uz": "🆔 Xodim kodini kiriting:", "ru": "🆔 Введите код сотрудника:", "en": "🆔 Enter employee code:", "kg": "🆔 Кызматкер кодун киргизиңиз:", "az": "🆔 İşçi kodunu daxil edin:"},
    "admin.employee.not_found": {"uz": "❌ Xodim topilmadi: {code}", "ru": "❌ Сотрудник не найден: {code}", "en": "❌ Employee not found: {code}", "kg": "❌ Кызматкер табылган жок: {code}", "az": "❌ İşçi tapılmadı: {code}"},
    "admin.manual_points.choose_amount": {"uz": "👤 {name} ({code})\n\nBall miqdorini tanlang:", "ru": "👤 {name} ({code})\n\nВыберите количество баллов:", "en": "👤 {name} ({code})\n\nChoose point amount:", "kg": "👤 {name} ({code})\n\nУпай санын тандаңыз:", "az": "👤 {name} ({code})\n\nBal miqdarını seçin:"},
    "admin.manual_points.done": {"uz": "✅ {code}: {points:+d} ball", "ru": "✅ {code}: {points:+d} баллов", "en": "✅ {code}: {points:+d} points", "kg": "✅ {code}: {points:+d} упай", "az": "✅ {code}: {points:+d} bal"},
    "admin.employee_status.choose": {"uz": "👤 {name} ({code})\n📌 Hozirgi: {status}\n\nYangi status:", "ru": "👤 {name} ({code})\n📌 Текущий: {status}\n\nНовый статус:", "en": "👤 {name} ({code})\n📌 Current: {status}\n\nNew status:", "kg": "👤 {name} ({code})\n📌 Азыркы: {status}\n\nЖаңы статус:", "az": "👤 {name} ({code})\n📌 Cari: {status}\n\nYeni status:"},
    "admin.employee_status.done": {"uz": "✅ {code} → {status}", "ru": "✅ {code} → {status}", "en": "✅ {code} → {status}", "kg": "✅ {code} → {status}", "az": "✅ {code} → {status}"},
    "admin.add_admin.enter_tg": {"uz": "🆔 Yangi admin Telegram ID sini kiriting:", "ru": "🆔 Введите Telegram ID нового админа:", "en": "🆔 Enter new admin Telegram ID:", "kg": "🆔 Жаңы админдин Telegram IDсин киргизиңиз:", "az": "🆔 Yeni admin Telegram ID-ni daxil edin:"},
    "admin.add_admin.only_digits": {"uz": "❌ Faqat raqam kiriting (Telegram ID):", "ru": "❌ Введите только цифры (Telegram ID):", "en": "❌ Enter digits only (Telegram ID):", "kg": "❌ Сан гана киргизиңиз (Telegram ID):", "az": "❌ Yalnız rəqəm daxil edin (Telegram ID):"},
    "admin.add_admin.enter_name": {"uz": "📛 Admin ismini kiriting:", "ru": "📛 Введите имя админа:", "en": "📛 Enter admin name:", "kg": "📛 Админдин атын киргизиңиз:", "az": "📛 Admin adını daxil edin:"},
    "admin.add_admin.done": {"uz": "✅ GA qo'shildi: {admin_id} — {name}", "ru": "✅ GA добавлен: {admin_id} — {name}", "en": "✅ GA added: {admin_id} — {name}", "kg": "✅ GA кошулду: {admin_id} — {name}", "az": "✅ GA əlavə olundu: {admin_id} — {name}"},
    "admin.web.login_request": {"uz": "🌐 Web login so'rovi\n\nQurilma: {device}\nKod: <code>{code}</code>\n\nTasdiqlaysizmi?", "ru": "🌐 Запрос на вход в веб\n\nУстройство: {device}\nКод: <code>{code}</code>\n\nПодтвердить?", "en": "🌐 Web login request\n\nDevice: {device}\nCode: <code>{code}</code>\n\nApprove?", "kg": "🌐 Веб кирүү сурамы\n\nТүзмөк: {device}\nКод: <code>{code}</code>\n\nТастыктайсызбы?", "az": "🌐 Web giriş sorğusu\n\nCihaz: {device}\nKod: <code>{code}</code>\n\nTəsdiqləyirsiniz?"},
    "admin.web.approve": {"uz": "✅ Tasdiqlash", "ru": "✅ Подтвердить", "en": "✅ Approve", "kg": "✅ Тастыктоо", "az": "✅ Təsdiqlə"},
    "admin.web.approved": {"uz": "✅ Web login tasdiqlandi.", "ru": "✅ Вход в веб подтвержден.", "en": "✅ Web login approved.", "kg": "✅ Веб кирүү тастыкталды.", "az": "✅ Web giriş təsdiqləndi."},
    "admin.web.approve_missing": {"uz": "❌ Login so'rovi topilmadi yoki eskirgan.", "ru": "❌ Запрос входа не найден или истёк.", "en": "❌ Login request not found or expired.", "kg": "❌ Кирүү сурамы табылган жок же мөөнөтү өттү.", "az": "❌ Giriş sorğusu tapılmadı və ya vaxtı keçib."},
}

TRANSLATIONS.update(ADMIN_TRANSLATIONS)


def t(key, lang="uz"):
    entry = TRANSLATIONS.get(key, {})
    return entry.get(lang, entry.get("uz", f"[{key}]"))



def normalize_text(value: str) -> str:
    return " ".join((value or "").strip().lower().split())


def variants_for_key(key: str) -> list[str]:
    entry = TRANSLATIONS.get(key, {})
    seen = []
    for value in entry.values():
        if not isinstance(value, str):
            continue
        normalized = normalize_text(value)
        if normalized and normalized not in seen:
            seen.append(normalized)
    return seen
