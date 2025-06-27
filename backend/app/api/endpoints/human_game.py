from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db

router = APIRouter()

@router.post("/start")
async def start_human_game(game_config: dict, db: Session = Depends(get_db)):
    """Start a game between human and LLM"""
    return {
        "game_id": "human_game_1",
        "status": "started",
        "player_color": game_config.get("player_color", "white"),
        "opponent": game_config.get("model", "GPT-4o")
    }

@router.post("/move")
async def make_human_move(move_data: dict, db: Session = Depends(get_db)):
    """Make a move in human vs LLM game"""
    return {
        "status": "move_accepted",
        "move": move_data.get("move"),
        "board": "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"
    }

@router.post("/reset")
async def reset_human_game(db: Session = Depends(get_db)):
    """Reset human vs LLM game"""
    return {"status": "reset"}