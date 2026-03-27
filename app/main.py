"""
Jelly Follow — FastAPI Backend
Supports both polling (local) and webhook (production/Railway)
"""
import logging
import asyncio
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.bootstrap.sheets_init import run_bootstrap
from app.services.admins_service import seed_super_admin
from app.routers import health, tracking, employees, admins, events, qr, internal

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)
logger = logging.getLogger(__name__)

USE_WEBHOOK = os.getenv("APP_ENV", "development") == "production"


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("=== Jelly Follow starting up ===")

    try:
        run_bootstrap()
        logger.info("Google Sheets bootstrap complete.")
    except Exception as e:
        logger.error(f"Bootstrap failed: {e}")

    try:
        seed_super_admin(settings.SUPER_ADMIN_TELEGRAM_ID)
    except Exception as e:
        logger.warning(f"Super admin seed failed: {e}")

    from app.bot.bot import create_bot, create_dispatcher
    bot = create_bot()
    dp = create_dispatcher()

    if USE_WEBHOOK:
        webhook_url = f"{settings.BASE_URL}/webhook"
        await bot.set_webhook(webhook_url)
        logger.info(f"Webhook set: {webhook_url}")
        app.state.bot = bot
        app.state.dp = dp
    else:
        task = asyncio.create_task(dp.start_polling(bot))
        app.state.bot_task = task
        logger.info("Bot polling started.")

    yield

    if USE_WEBHOOK:
        await bot.delete_webhook()
    elif hasattr(app.state, "bot_task"):
        app.state.bot_task.cancel()

    logger.info("=== Jelly Follow shutdown ===")


app = FastAPI(title="Jelly Follow API", version="1.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

os.makedirs("static/qr", exist_ok=True)
app.mount("/static", StaticFiles(directory="static"), name="static")

app.include_router(health.router)
app.include_router(tracking.router)
app.include_router(employees.router)
app.include_router(admins.router)
app.include_router(events.router)
app.include_router(qr.router)
app.include_router(internal.router)


@app.post("/webhook")
async def telegram_webhook(request: Request):
    from aiogram.types import Update
    bot = request.app.state.bot
    dp = request.app.state.dp
    data = await request.json()
    update = Update.model_validate(data)
    await dp.feed_update(bot, update)
    return {"ok": True}