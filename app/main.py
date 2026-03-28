"""
Jelly Follow — FastAPI Backend.
BOT_MODE: "polling" (development) | "webhook" (production) | "none" (API only)
"""
import logging
import asyncio
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, HTTPException, Header
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.bootstrap.sheets_init import run_bootstrap
from app.services.admins_service import seed_super_admin
from app.routers import health, tracking, employees, admins, events, qr, internal
from app.routers import admin_web

logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(name)s | %(message)s")
logger = logging.getLogger(__name__)

# BOT_MODE: "polling" | "webhook" | "none"
BOT_MODE = settings.BOT_MODE.lower()


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("=== Jelly Follow starting up (BOT_MODE=%s) ===", BOT_MODE)
    app.state.bot = None
    app.state.dp = None
    app.state.bot_task = None

    # 1) Google Sheets bootstrap
    try:
        if settings.BOOTSTRAP_ON_START:
            run_bootstrap()
            logger.info("Google Sheets bootstrap complete.")
    except Exception as e:
        logger.error("Bootstrap failed: %s", e)

    # 2) Super admin seed
    try:
        if settings.SEED_SUPER_ADMIN_ON_START:
            seed_super_admin(settings.SUPER_ADMIN_TELEGRAM_ID)
            logger.info("Super admin seed complete.")
    except Exception as e:
        logger.warning("Super admin seed failed: %s", e)

    # 3) Bot init
    if BOT_MODE != "none":
        from app.bot.bot import create_bot, create_dispatcher
        bot = create_bot()
        dp = create_dispatcher()
        app.state.bot = bot
        app.state.dp = dp

        if BOT_MODE == "webhook":
            # Set webhook automatically
            webhook_url = f"{str(settings.BASE_URL).rstrip('/')}/webhook"
            try:
                await bot.delete_webhook(drop_pending_updates=True)
                await bot.set_webhook(webhook_url)
                logger.info("Webhook set: %s", webhook_url)
            except Exception as e:
                logger.error("Webhook set failed: %s — Use POST /internal/set-webhook to retry", e)

        elif BOT_MODE == "polling":
            try:
                await bot.delete_webhook(drop_pending_updates=True)
                task = asyncio.create_task(dp.start_polling(bot))
                app.state.bot_task = task
                logger.info("Bot polling started.")
            except Exception as e:
                logger.error("Polling start failed: %s", e)

    yield

    # Shutdown
    logger.info("Shutting down...")
    if getattr(app.state, "bot_task", None):
        app.state.bot_task.cancel()
        try:
            await app.state.bot_task
        except (asyncio.CancelledError, Exception):
            pass

    if app.state.bot:
        try:
            if BOT_MODE == "webhook":
                await app.state.bot.delete_webhook()
        except Exception:
            pass
        try:
            await app.state.bot.session.close()
        except Exception:
            pass

    logger.info("=== Jelly Follow shutdown ===")


app = FastAPI(title="Jelly Follow API", version="1.2.0", lifespan=lifespan)
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
    return {"ok": True, "service": "Jelly Follow API", "version": "1.2.0",
            "bot_mode": BOT_MODE, "env": settings.APP_ENV}


@app.post("/webhook")
async def telegram_webhook(request: Request):
    from aiogram.types import Update
    bot = getattr(request.app.state, "bot", None)
    dp = getattr(request.app.state, "dp", None)
    if not bot or not dp:
        return {"ok": False, "error": "bot_not_ready"}
    try:
        data = await request.json()
        update = Update.model_validate(data)
        await dp.feed_update(bot, update)
    except Exception as e:
        logger.error("Webhook processing error: %s", e)
    return {"ok": True}


@app.post("/internal/set-webhook")
async def manual_set_webhook(x_internal_secret: str = Header("")):
    """Manually set webhook — use when auto-setup fails."""
    if x_internal_secret != settings.INTERNAL_SECRET:
        raise HTTPException(status_code=403, detail="Forbidden")
    bot = getattr(app.state, "bot", None)
    if not bot:
        raise HTTPException(status_code=500, detail="Bot not initialized")
    webhook_url = f"{str(settings.BASE_URL).rstrip('/')}/webhook"
    try:
        await bot.delete_webhook(drop_pending_updates=True)
        await bot.set_webhook(webhook_url)
        return {"ok": True, "webhook_url": webhook_url}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/internal/delete-webhook")
async def manual_delete_webhook(x_internal_secret: str = Header("")):
    if x_internal_secret != settings.INTERNAL_SECRET:
        raise HTTPException(status_code=403, detail="Forbidden")
    bot = getattr(app.state, "bot", None)
    if not bot:
        raise HTTPException(status_code=500, detail="Bot not initialized")
    await bot.delete_webhook(drop_pending_updates=True)
    return {"ok": True, "message": "Webhook deleted"}
