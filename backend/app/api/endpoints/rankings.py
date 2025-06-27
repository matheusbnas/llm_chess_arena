from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db

router = APIRouter()

@router.get("/")
async def get_rankings(db: Session = Depends(get_db)):
    """Get model rankings"""
    return {
        "rankings": [
            {"model": "GPT-4o", "elo": 1650, "games": 25, "win_rate": 0.68},
            {"model": "Gemini-Pro", "elo": 1580, "games": 23, "win_rate": 0.61},
            {"model": "Deepseek-Chat", "elo": 1520, "games": 20, "win_rate": 0.55}
        ]
    }