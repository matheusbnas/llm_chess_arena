from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db

router = APIRouter()

@router.get("/")
async def get_lichess_status(db: Session = Depends(get_db)):
    """Get Lichess integration status"""
    return {
        "connected": False,
        "message": "Lichess integration not configured"
    }