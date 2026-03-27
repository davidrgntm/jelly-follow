from fastapi import APIRouter
from app.utils.datetime_utils import now_str

router = APIRouter()


@router.get("/health")
async def health():
    return {"status": "ok", "time": now_str()}
