"""Jelly Follow — FastAPI Backend. Supports polling and webhook."""
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
from app.routers import admin_web

logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(name)s | %(message)s")
logger = logging.getLogger(__name__)

USE_WEBHOOK = os.getenv("APP_ENV", "development").lower() == "production"
BOOTSTRAP_ON_START = settings.BOOTSTRAP_ON_START
SEED_SUPER_ADMIN_ON_START = settings.SEED_SUPER_ADMIN_ON_START


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("=== Jelly Follow starting up ===")
    app.state.bot = None
    app.state.dp = None
    app.state.bot_task = None
    app.state.webhook_enabled = False

    try:
        if BOOTSTRAP_ON_START:
            run_bootstrap()
            logger.info("Google Sheets bootstrap complete.")
        else:
            logger.info("BOOTSTRAP_ON_START=false, skipped.")
    except Exception as e:
        logger.error("Bootstrap failed: %s", e)

    try:
        if SEED_SUPER_ADMIN_ON_START:
            seed_super_admin(settings.SUPER_ADMIN_TELEGRAM_ID)
            logger.info("Super admin seed complete.")
    except Exception as e:
        logger.warning("Super admin seed failed: %s", e)

    from app.bot.bot import create_bot, create_dispatcher
    bot = create_bot()
    dp = create_dispatcher()
    app.state.bot = bot
    app.state.dp = dp

    if USE_WEBHOOK:
        webhook_url = f"{str(settings.BASE_URL).rstrip('/')}/webhook"
        try:
            await bot.set_webhook(webhook_url)
            app.state.webhook_enabled = True
            logger.info("Webhook set: %s", webhook_url)
        except Exception as e:
            logger.error("Webhook set failed: %s", e)
    else:
        try:
            task = asyncio.create_task(dp.start_polling(bot))
            app.state.bot_task = task
            logger.info("Bot polling started.")
        except Exception as e:
            logger.error("Polling start failed: %s", e)

    yield

    try:
        if USE_WEBHOOK and app.state.bot and app.state.webhook_enabled:
            try:
                await app.state.bot.delete_webhook()
            except Exception:
                pass
        if getattr(app.state, "bot_task", None):
            app.state.bot_task.cancel()
            try:
                await app.state.bot_task
            except (asyncio.CancelledError, Exception):
                pass
        if app.state.bot:
            try:
                await app.state.bot.session.close()
            except Exception:
                pass
    finally:
        logger.info("=== Jelly Follow shutdown ===")


app = FastAPI(title="Jelly Follow API", version="1.1.0", lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

os.makedirs("static/qr", exist_ok=True)
app.mount("/static", StaticFiles(directory="static"), name="static")

app.include_router(health.router)
app.include_router(tracking.router)
app.include_router(employees.router)
app.include_router(admins.router)
app.include_router(events.router)
app.include_router(qr.router)
app.include_router(internal.router)
app.include_router(admin_web.router)


@app.get("/")
async def root():
    return {"ok": True, "service": "Jelly Follow API", "version": "1.1.0",
            "env": os.getenv("APP_ENV", "development"), "webhook_mode": USE_WEBHOOK}


@app.post("/webhook")
async def telegram_webhook(request: Request):
    from aiogram.types import Update
    bot = getattr(request.app.state, "bot", None)
    dp = getattr(request.app.state, "dp", None)
    if not bot or not dp:
        return {"ok": False, "error": "bot_not_ready"}
    data = await request.json()
    update = Update.model_validate(data)
    await dp.feed_update(bot, update)
    return {"ok": True}
