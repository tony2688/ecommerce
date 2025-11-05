from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.api.deps import get_db

router = APIRouter()


@router.get("/")
def health_check():
    """Basic health check endpoint."""
    return {"status": "healthy"}


@router.get("/db")
def health_check_db(db: Session = Depends(get_db)):
    """Health check with database connection test."""
    try:
        db.execute(text("SELECT 1"))
        return {"status": "healthy", "database": "connected"}
    except Exception as e:
        return {"status": "unhealthy", "database": f"error: {str(e)}"}