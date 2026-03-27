"""
Internal endpoints — protected, not public.
"""
from fastapi import APIRouter, HTTPException, Header
from app.config import settings
from app.bootstrap.sheets_init import run_bootstrap

router = APIRouter(prefix="/internal")


def _check(secret: str):
    if secret != settings.INTERNAL_SECRET:
        raise HTTPException(status_code=403, detail="Forbidden")


@router.post("/bootstrap-sheets")
async def bootstrap_sheets(x_internal_secret: str = Header("")):
    _check(x_internal_secret)
    try:
        run_bootstrap()
        return {"ok": True, "message": "Bootstrap completed"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/sync-schema")
async def sync_schema(x_internal_secret: str = Header("")):
    _check(x_internal_secret)
    try:
        from app.bootstrap.sheets_init import _ensure_headers
        from app.integrations.google_sheets import get_sheets
        _ensure_headers(get_sheets())
        return {"ok": True, "message": "Schema synced"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
