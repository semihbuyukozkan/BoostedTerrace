from fastapi import APIRouter
from database.db import SessionLocal
from sqlalchemy import text

router = APIRouter()

@router.get("/health", response_model=dict)
def health_check():
    ok = True
    try:
        with SessionLocal() as s:
            s.execute(text("SELECT 1"))
    except Exception:
        ok = False
    return {"status": "ok" if ok else "degraded", "database": ok}
