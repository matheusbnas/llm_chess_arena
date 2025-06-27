from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Dict, Any

from app.core.database import get_db
from app.services.game_service import GameService

router = APIRouter()

@router.get("/stats")
async def get_dashboard_stats(db: Session = Depends(get_db)):
    """Get dashboard statistics"""
    game_service = GameService(db)
    
    # Get basic stats
    total_games = len(await game_service.get_games(limit=10000))
    recent_games = await game_service.get_recent_games(10)
    
    return {
        "totalGames": total_games,
        "activeModels": 5,  # Mock data for now
        "avgGameLength": 45.2,
        "tournamentsCompleted": 3
    }

@router.get("/recent-games")
async def get_recent_games(limit: int = 10, db: Session = Depends(get_db)):
    """Get recent games for dashboard"""
    game_service = GameService(db)
    games = await game_service.get_recent_games(limit)
    return games

@router.get("/chart-data")
async def get_chart_data(db: Session = Depends(get_db)):
    """Get chart data for dashboard"""
    return {
        "modelResults": [
            {"model": "GPT-4o", "wins": 15, "draws": 3, "losses": 7},
            {"model": "Gemini-Pro", "wins": 12, "draws": 5, "losses": 8},
            {"model": "Deepseek-Chat", "wins": 10, "draws": 4, "losses": 11}
        ],
        "winRateData": [
            {"name": "White Wins", "value": 45},
            {"name": "Black Wins", "value": 35},
            {"name": "Draws", "value": 20}
        ]
    }