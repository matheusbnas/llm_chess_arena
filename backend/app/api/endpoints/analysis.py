from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db

router = APIRouter()

@router.get("/")
async def get_analysis_overview(db: Session = Depends(get_db)):
    """Get analysis overview"""
    return {
        "message": "Analysis endpoint working",
        "total_analyzed_games": 0,
        "avg_accuracy": 0.0
    }