from fastapi import APIRouter
from app.integrations.google_sheets import get_sheets

router = APIRouter()

@router.get("/health")
async def health_check():
    sheets_ok = False
    try:
        sheets = get_sheets()
        sheets.get_sheet("meta")
        sheets_ok = True
    except Exception:
        pass
    return {"ok": True, "sheets_connected": sheets_ok, "service": "Jelly Follow API"}
