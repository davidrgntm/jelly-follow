# 🍇 Jelly Follow

Instagram follower tracking system for Jelly employees.

---

## Tizim haqida

**Jelly Follow** — Jelly xodimlarining mijozlarni Instagram sahifalariga olib kelishini kuzatuvchi tizim.

- Xodim Telegram bot orqali ro'yxatdan o'tadi
- Unikal QR kod va short-link oladi
- Mijoz QR ni skanerlaydi → tizim loglar yig'adi → Instagram'ga yo'naltiradi
- Ball tizimi: 1 unique device = 1 ball
- 4 ta mamlakat: UZ, RU, KG, AZ
- 5 tilda bot: uz, ru, en, kg, az

---

## Stack

| Qatlam | Texnologiya |
|--------|-------------|
| Backend | Python 3.11 + FastAPI |
| Bot | aiogram 3.x |
| Storage | Google Sheets |
| QR | qrcode + Pillow |
| Server | Gunicorn + Uvicorn |
| Proxy | Nginx |

---

## Papka strukturasi

```
jelly-follow/
├── app/
│   ├── main.py              ← FastAPI app entry
│   ├── config.py            ← Settings (env)
│   ├── bootstrap/
│   │   └── sheets_init.py   ← Google Sheets auto-setup
│   ├── integrations/
│   │   ├── google_sheets.py ← Sheets client
│   │   └── qr_generator.py  ← QR generation
│   ├── services/
│   │   ├── employees_service.py
│   │   ├── admins_service.py
│   │   ├── events_service.py
│   │   ├── scans_service.py     ← Tracking core
│   │   ├── devices_service.py   ← Uniqueness logic
│   │   ├── points_service.py
│   │   ├── leaderboard_service.py
│   │   ├── qr_service.py
│   │   └── notifications_service.py
│   ├── routers/
│   │   ├── health.py
│   │   ├── tracking.py      ← /r/{code} redirect
│   │   ├── employees.py
│   │   ├── admins.py
│   │   ├── events.py
│   │   ├── qr.py
│   │   └── internal.py      ← Bootstrap endpoints
│   ├── bot/
│   │   ├── bot.py
│   │   ├── handlers/
│   │   │   ├── registration.py
│   │   │   ├── menu.py
│   │   │   └── admin.py
│   │   ├── keyboards/
│   │   │   └── main_keyboards.py
│   │   ├── middlewares/
│   │   │   └── lang_middleware.py
│   │   └── texts/
│   │       └── translations.py  ← 5-language system
│   └── utils/
│       ├── ids.py              ← ID generator
│       ├── fingerprint.py      ← Device fingerprint
│       ├── datetime_utils.py
│       └── validators.py
├── templates/
│   └── redirect.html       ← Tracking redirect page
├── static/qr/              ← Generated QR images
├── deploy/
│   ├── nginx.conf
│   ├── jelly-follow.service
│   └── deploy.sh
├── .env.example
├── requirements.txt
└── README.md
```

---

## O'rnatish

### 1. Talablar

- Python 3.11+
- Ubuntu 22.04 (yoki boshqa Linux)
- Google Cloud Service Account
- Telegram Bot Token

### 2. Reponi klonlash

```bash
git clone <repo_url> /home/jelly/jelly-follow
cd /home/jelly/jelly-follow
```

### 3. Virtual muhit

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 4. `.env` faylini sozlash

```bash
cp .env.example .env
nano .env
```

Majburiy o'zgaruvchilar:

```env
BOT_TOKEN=your_bot_token
SUPER_ADMIN_TELEGRAM_ID=your_telegram_id
GOOGLE_SERVICE_ACCOUNT_JSON_PATH=./credentials.json
SPREADSHEET_NAME=Jelly Follow - PROD
TRACKING_DOMAIN=https://go.jelly.uz
BASE_URL=https://api.follow.jelly.uz
INTERNAL_SECRET=very_strong_secret_here
INSTAGRAM_UZ_USERNAME=jelly.uz
INSTAGRAM_RU_USERNAME=jelly.russia
INSTAGRAM_KG_USERNAME=jelly.kg
INSTAGRAM_AZ_USERNAME=jelly.az
```

### 5. Google Service Account

1. [Google Cloud Console](https://console.cloud.google.com) ga kiring
2. Yangi project yarating: `jelly-follow`
3. **APIs & Services → Enable APIs**: Google Sheets API, Google Drive API
4. **IAM → Service Accounts**: yangi service account yarating
5. JSON key yuklab oling → `credentials.json` deb saqlang
6. Bu faylni server ga `/home/jelly/jelly-follow/credentials.json` ga qo'ying

### 6. Ishga tushirish (development)

```bash
source venv/bin/activate
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### 7. Production deploy

```bash
# Nginx o'rnatish
sudo apt install nginx certbot python3-certbot-nginx

# SSL sertifikat
sudo certbot --nginx -d go.jelly.uz -d api.follow.jelly.uz

# Nginx config
sudo cp deploy/nginx.conf /etc/nginx/sites-available/jelly-follow
sudo ln -s /etc/nginx/sites-available/jelly-follow /etc/nginx/sites-enabled/
sudo nginx -t && sudo systemctl reload nginx

# Systemd service
bash deploy/deploy.sh
```

---

## Google Sheets

Backend **birinchi ishga tushganda** avtomatik quyidagilarni qiladi:

- `Jelly Follow - PROD` spreadsheet yaratadi (yoki topadi)
- 14 ta sheet yaratadi
- Barcha headerlarni yozadi
- Dictionary ma'lumotlarni seed qiladi
- 4 ta mamlakatni seed qiladi
- Super admin yaratadi

**Qo'lda hech narsa sozlash shart emas.**

Spreadsheetni ko'rish uchun: service account email ni spreadsheet ga editor sifatida qo'shing.

---

## API Endpointlar

### Public

| Method | URL | Ta'rif |
|--------|-----|--------|
| `GET` | `/health` | Health check |
| `GET` | `/r/{employee_code}` | QR redirect |
| `POST` | `/api/tracking/client-log` | JS device log |

### Employees

| Method | URL | Ta'rif |
|--------|-----|--------|
| `POST` | `/api/employees/register` | Ro'yxatdan o'tish |
| `GET` | `/api/employees/{id}` | Profil |
| `GET` | `/api/employees/{id}/stats` | Statistika |
| `GET` | `/api/employees/{id}/leaderboard` | Reyting |

### Admin (Header: `X-Internal-Secret`)

| Method | URL | Ta'rif |
|--------|-----|--------|
| `POST` | `/api/admins/create` | Admin yaratish |
| `POST` | `/api/admins/employee-status` | Status o'zgartirish |
| `POST` | `/api/admins/manual-points` | Ball berish |
| `POST` | `/api/events/create` | Event yaratish |
| `POST` | `/api/events/{id}/activate` | Event faollashtirish |
| `POST` | `/api/events/{id}/pause` | Pause |
| `POST` | `/api/events/{id}/finish` | Yakunlash |
| `POST` | `/api/qr/generate/employee/{id}` | QR yaratish |

### Internal

| Method | URL | Ta'rif |
|--------|-----|--------|
| `POST` | `/internal/bootstrap-sheets` | Sheets bootstrap |
| `POST` | `/internal/sync-schema` | Schema sync |

---

## Telegram Bot

### Xodim buyruqlari

| Buyruq | Ta'rif |
|--------|--------|
| `/start` | Ro'yxatdan o'tish / Asosiy menyu |

### Admin buyruqlari

| Buyruq | Ta'rif |
|--------|--------|
| `/admin` | Admin panel |
| `/employees` | Xodimlar ro'yxati |
| `/events` | Eventlar |
| `/leaderboard [CC]` | Reyting |
| `/setstatus <code> <status>` | Status o'zgartirish |
| `/createevent` | Event yaratish (dialog) |
| `/activateevent <id>` | Event faollashtirish |
| `/pauseevent <id>` | Pause |
| `/finishevent <id>` | Yakunlash |
| `/manualpoints <code> <±N> [sabab]` | Ball berish |
| `/addadmin <tg_id> <ism> <rol>` | Admin qo'shish (super_admin) |

---

## ID Formatlari

| Tur | Format | Misol |
|-----|--------|-------|
| Admin | `ADM-NNNN` | `ADM-0001` |
| Employee | `EMP-NNNN` | `EMP-0001` |
| Employee code | `CC-NNNN` | `UZ-0001` |
| Event | `EVT-YYYYMMDD-NNN` | `EVT-20260401-001` |
| QR | `QR-NNNNNN` | `QR-000001` |
| Scan | `SCN-YYYYMMDD-NNNNNN` | `SCN-20260401-000001` |
| Point TX | `PTX-YYYYMMDD-NNNNNN` | `PTX-20260401-000001` |
| Log | `LOG-YYYYMMDD-NNNNNN` | `LOG-20260401-000001` |

---

## Ball logikasi

```
1 unique device = 1 ball (tizim bo'yicha global)

Device key = SHA256(fingerprint_id | os | browser | platform | screen | timezone | user_agent)

Agar device_key device_registry da yo'q → +1 ball, yozuv yaratiladi
Agar mavjud → 0 ball, total_scans oshiriladi, last_seen_at yangilanadi
```

---

## Xavfsizlik

- `.env` faylini hech qachon gitga qo'shmang
- `credentials.json` ni gitga qo'shmang
- `INTERNAL_SECRET` ni kuchli qiling (min 32 belgi)
- Admin endpointlar `X-Internal-Secret` header talab qiladi
- `/internal/*` endpointlar tashqi trafikdan Nginx orqali yopish mumkin

---

## Logs

```bash
# Systemd logs
journalctl -u jelly-follow -f

# Application logs
tail -f /var/log/jelly-follow/error.log

# Sheets bootstrap va scan loglar
# Google Sheets → system_logs sheet da ko'rish mumkin
```

---

## Muammolar va yechimlar

**Bootstrap ishlamayapti?**
```bash
# Credentials to'g'riligini tekshiring
python3 -c "from app.config import settings; print(settings.get_google_credentials())"
```

**Bot javob bermayapti?**
```bash
# Token to'g'riligini tekshiring
curl https://api.telegram.org/bot<TOKEN>/getMe
```

**QR rasm chiqmayapti?**
```bash
# static/qr papkasi mavjudligini tekshiring
ls -la static/qr/
```
