# 🍇 Jelly Follow

Instagram follower tracking system for Jelly employees.

---

## Tizim haqida

**Jelly Follow** — Jelly xodimlarining mijozlarni Instagram sahifalariga olib kelishini kuzatuvchi tizim.

- Xodim Telegram bot orqali ro'yxatdan o'tadi
- Unikal QR kod va short-link oladi
- Mijoz QR ni skanerlaydi → tizim loglar yig'adi → Instagram'ga yo'naltiradi
- Ball tizimi: 1 unique device = 1 ball (butun tizim bo'yicha)
- 4 ta mamlakat: UZ, RU, KG, AZ
- 5 tilda bot: uz, ru, en, kg, az
- Event tizimi: mukofot puli, leaderboard, notification
- Web admin panel: real-time dashboard

---

## Stack

| Qatlam | Texnologiya |
|--------|-------------|
| Backend | Python 3.11+ FastAPI |
| Bot | aiogram 3.x |
| Storage | Google Sheets |
| QR | qrcode + Pillow |
| Server | Gunicorn + Uvicorn |
| Proxy | Nginx |
| Cache | In-memory TTL Cache |

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
│   │   ├── google_sheets.py ← Sheets client + retry
│   │   └── qr_generator.py  ← QR generation
│   ├── services/
│   │   ├── employees_service.py
│   │   ├── admins_service.py
│   │   ├── events_service.py
│   │   ├── scans_service.py     ← Tracking core + pre-log
│   │   ├── devices_service.py   ← Uniqueness + anti-abuse
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
│   │   ├── internal.py
│   │   └── admin_web.py     ← Web admin panel
│   ├── bot/
│   │   ├── bot.py
│   │   ├── handlers/
│   │   │   ├── registration.py
│   │   │   ├── menu.py
│   │   │   └── admin.py
│   │   ├── keyboards/
│   │   ├── middlewares/
│   │   └── texts/
│   │       └── translations.py
│   └── utils/
│       ├── ids.py
│       ├── datetime_utils.py
│       ├── fingerprint.py
│       ├── validators.py
│       ├── cache.py          ← TTL cache
│       └── anti_abuse.py     ← Rate limiting
├── templates/
│   ├── redirect.html         ← Tracking page
│   └── admin_panel.html      ← Web dashboard
├── static/qr/
├── deploy/
│   ├── deploy.sh
│   ├── jelly-follow.service
│   └── nginx.conf
├── requirements.txt
├── Procfile
└── nixpacks.toml
```

---

## O'rnatish

### 1. Google Cloud sozlash

1. [Google Cloud Console](https://console.cloud.google.com/) ochiladi
2. Yangi project yaratiladi
3. Google Sheets API yoqiladi
4. Service Account yaratiladi
5. JSON key yuklab olinadi

### 2. Telegram Bot

1. [@BotFather](https://t.me/BotFather) orqali bot yaratiladi
2. Bot token olinadi

### 3. Loyihani o'rnatish

```bash
git clone <repo-url> jelly-follow
cd jelly-follow
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# .env fayli yaratish
cp .env.example .env
# .env ni to'ldirish (pastga qarang)
```

### 4. Birinchi ishga tushirish

```bash
# Bootstrap — Google Sheets yaratadi
export BOOTSTRAP_ON_START=true
export SEED_SUPER_ADMIN_ON_START=true

# Development mode (polling)
export APP_ENV=development
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### 5. Production deploy

```bash
bash deploy/deploy.sh
```

---

## Muhim environment o'zgaruvchilari

| O'zgaruvchi | Tavsif | Misol |
|-------------|--------|-------|
| `BOT_TOKEN` | Telegram bot token | `123456:ABC...` |
| `BASE_URL` | Backend URL | `https://api.follow.jelly.uz` |
| `TRACKING_DOMAIN` | QR redirect domain | `https://go.jelly.uz` |
| `GOOGLE_SERVICE_ACCOUNT_JSON` | SA JSON (string) | `{"type":"service_account",...}` |
| `SPREADSHEET_NAME` | Spreadsheet nomi | `Jelly Follow - PROD` |
| `SUPER_ADMIN_TELEGRAM_ID` | Admin Telegram ID | `123456789` |
| `INTERNAL_SECRET` | API himoya kaliti | `random_secret_here` |
| `ADMIN_WEB_SECRET` | Web panel kaliti | `another_secret` |
| `APP_ENV` | production / development | `production` |
| `BOOTSTRAP_ON_START` | Sheets auto-setup | `true` |
| `SEED_SUPER_ADMIN_ON_START` | Admin auto-seed | `true` |

---

## Web Admin Panel

Brauzerda ochish:
```
https://your-domain.com/admin?key=YOUR_ADMIN_WEB_SECRET
```

Dashboard, xodimlar, eventlar, reyting va skanlar — barchasini web orqali ko'rish.

---

## Domen sozlash (Nginx)

`deploy/nginx.conf` faylini ko'ring. 3 ta domen tavsiya etiladi:

- `follow.jelly.uz` — web admin panel
- `go.jelly.uz` — tracking redirect
- `api.follow.jelly.uz` — backend API

Nginx'ni sozlash:

```bash
sudo cp deploy/nginx.conf /etc/nginx/sites-available/jelly-follow
sudo ln -s /etc/nginx/sites-available/jelly-follow /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

SSL uchun:
```bash
sudo certbot --nginx -d follow.jelly.uz -d go.jelly.uz -d api.follow.jelly.uz
```

---

## API endpointlar

| Method | Path | Tavsif |
|--------|------|--------|
| GET | `/health` | Health check + Sheets status |
| GET | `/r/{employee_code}` | Tracking redirect |
| POST | `/api/tracking/client-log` | Client-side log |
| POST | `/api/employees/register` | Employee ro'yxatdan o'tish |
| GET | `/api/employees/{id}` | Employee profili |
| GET | `/api/employees/{id}/stats` | Employee statistikasi |
| GET | `/api/employees/{id}/leaderboard` | Employee reytingi |
| POST | `/api/admins/create` | Admin yaratish |
| POST | `/api/admins/employee-status` | Status o'zgartirish |
| POST | `/api/admins/manual-points` | Manual ball |
| GET | `/api/admins/stats` | Tizim statistikasi |
| POST | `/api/events/create` | Event yaratish |
| POST | `/api/events/{id}/activate` | Event boshlash |
| POST | `/api/events/{id}/pause` | Event to'xtatish |
| POST | `/api/events/{id}/finish` | Event tugatish |
| GET | `/api/events/{id}/leaderboard` | Event reytingi |
| POST | `/api/qr/generate/employee/{id}` | QR yaratish |
| GET | `/admin?key=...` | Web admin panel |
