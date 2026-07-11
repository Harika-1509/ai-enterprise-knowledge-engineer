from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.database import get_db

router = APIRouter()


@router.get("/health")
def health_check():
    """Basic liveness check - is the API process running at all."""
    return {"status": "ok", "service": "ai-enterprise-knowledge-engineer"}


@router.get("/health/db")
def health_check_db(db: Session = Depends(get_db)):
    """Readiness check - can we actually reach Postgres."""
    db.execute(text("SELECT 1"))
    return {"status": "ok", "database": "connected"}