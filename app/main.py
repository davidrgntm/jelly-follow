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

USE_WEBHOOK = os.getenv("APP_ENV", "development").lower() == "production"
BOOTSTRAP_ON_START = os.getenv("BOOTSTRAP_ON_START", "false").lower() == "true"
SEED_SUPER_ADMIN_ON_START = os.getenv("SEED_SUPER_ADMIN_ON_START", "false").lower() == "true"


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("=== Jelly Follow starting up ===")

    app.state.bot = None
    app.state.dp = None
    app.state.bot_task = None
    app.state.webhook_enabled = False

    # 1) Google Sheets bootstrap
    try:
        if BOOTSTRAP_ON_START:
            run_bootstrap()
            logger.info("Google Sheets bootstrap complete.")
        else:
            logger.info("BOOTSTRAP_ON_START=false, bootstrap skipped.")
    except Exception as e:
        logger.error(f"Bootstrap failed: {e}")

    # 2) Super admin seed
    try:
        if SEED_SUPER_ADMIN_ON_START:
            seed_super_admin(settings.SUPER_ADMIN_TELEGRAM_ID)
            logger.info("Super admin seed complete.")
        else:
            logger.info("SEED_SUPER_ADMIN_ON_START=false, super admin seed skipped.")
    except Exception as e:
        logger.warning(f"Super admin seed failed: {e}")

    # 3) Bot init
    from app.bot.bot import create_bot, create_dispatcher

    bot = create_bot()
    dp = create_dispatcher()

    app.state.bot = bot
    app.state.dp = dp

    # 4) Webhook / Polling
    if USE_WEBHOOK:
        webhook_url = f"{str(settings.BASE_URL).rstrip('/')}/webhook"
        try:
            await bot.set_webhook(webhook_url)
            app.state.webhook_enabled = True
            logger.info(f"Webhook set: {webhook_url}")
        except Exception as e:
            logger.error(f"Webhook set failed: {e}")
            logger.warning("App stays alive. Fix webhook/domain and redeploy.")
    else:
        try:
            task = asyncio.create_task(dp.start_polling(bot))
            app.state.bot_task = task
            logger.info("Bot polling started.")
        except Exception as e:
            logger.error(f"Polling start failed: {e}")

    yield

    # Shutdown
    try:
        if USE_WEBHOOK and app.state.bot and app.state.webhook_enabled:
            try:
                await app.state.bot.delete_webhook()
                logger.info("Webhook deleted.")
            except Exception as e:
                logger.warning(f"Webhook delete failed: {e}")

        if getattr(app.state, "bot_task", None):
            app.state.bot_task.cancel()
            try:
                await app.state.bot_task
            except asyncio.CancelledError:
                pass
            except Exception as e:
                logger.warning(f"Bot task cancel warning: {e}")

        if app.state.bot:
            try:
                await app.state.bot.session.close()
            except Exception as e:
                logger.warning(f"Bot session close failed: {e}")

    finally:
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


@app.get("/")
async def root():
    return {
        "ok": True,
        "service": "Jelly Follow API",
        "env": os.getenv("APP_ENV", "development"),
        "webhook_mode": USE_WEBHOOK,
    }


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