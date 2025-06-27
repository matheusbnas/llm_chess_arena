from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from typing import Dict, Any, List
import uuid
import asyncio

from app.core.database import get_db
from app.core.websocket_manager import websocket_manager
from app.services.game_service import GameService
from app.services.model_manager import ModelManager
from app.schemas.arena import BattleRequest, TournamentRequest

router = APIRouter()

# Store active battles
active_battles: Dict[str, Dict[str, Any]] = {}

@router.post("/start-battle")
async def start_battle(
    battle_request: BattleRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """Start a battle between two models"""
    battle_id = str(uuid.uuid4())
    
    battle_data = {
        "id": battle_id,
        "white_model": battle_request.white_model,
        "black_model": battle_request.black_model,
        "opening": battle_request.opening,
        "num_games": battle_request.num_games,
        "speed": battle_request.speed,
        "status": "starting",
        "current_game": 1,
        "total_games": battle_request.num_games,
        "white_wins": 0,
        "black_wins": 0,
        "draws": 0,
        "current_board": None
    }
    
    active_battles[battle_id] = battle_data
    
    # Start battle in background
    background_tasks.add_task(run_battle, battle_id, battle_data, db)
    
    return battle_data

@router.post("/start-tournament")
async def start_tournament(
    tournament_request: TournamentRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """Start a tournament with multiple models"""
    tournament_id = str(uuid.uuid4())
    
    # Calculate total games for round-robin tournament
    num_models = len(tournament_request.models)
    total_games = (num_models * (num_models - 1)) * tournament_request.games_per_pair
    
    tournament_data = {
        "id": tournament_id,
        "type": "tournament",
        "models": tournament_request.models,
        "games_per_pair": tournament_request.games_per_pair,
        "speed": tournament_request.speed,
        "status": "starting",
        "total_games": total_games,
        "completed_games": 0,
        "results": {}
    }
    
    active_battles[tournament_id] = tournament_data
    
    # Start tournament in background
    background_tasks.add_task(run_tournament, tournament_id, tournament_data, db)
    
    return tournament_data

@router.get("/battles/{battle_id}")
async def get_battle_status(battle_id: str):
    """Get status of a specific battle"""
    if battle_id not in active_battles:
        raise HTTPException(status_code=404, detail="Battle not found")
    
    return active_battles[battle_id]

@router.post("/battles/{battle_id}/stop")
async def stop_battle(battle_id: str):
    """Stop a running battle"""
    if battle_id not in active_battles:
        raise HTTPException(status_code=404, detail="Battle not found")
    
    active_battles[battle_id]["status"] = "stopped"
    return {"message": "Battle stopped"}

async def run_battle(battle_id: str, battle_data: Dict[str, Any], db: Session):
    """Run a battle between two models"""
    try:
        model_manager = ModelManager()
        game_service = GameService(db)
        
        battle_data["status"] = "running"
        
        for game_num in range(1, battle_data["num_games"] + 1):
            if battle_data["status"] == "stopped":
                break
                
            battle_data["current_game"] = game_num
            
            # Simulate a game (replace with actual game logic)
            await simulate_game(battle_data, model_manager, game_service)
            
            # Broadcast update
            await websocket_manager.broadcast_to_arena({
                "type": "battle_update",
                "data": battle_data
            })
            
            # Wait based on speed setting
            await asyncio.sleep(1.0 / battle_data["speed"])
        
        battle_data["status"] = "completed"
        
        # Broadcast completion
        await websocket_manager.broadcast_to_arena({
            "type": "battle_finished",
            "data": battle_data
        })
        
    except Exception as e:
        print(f"Error in battle {battle_id}: {e}")
        battle_data["status"] = "error"
        battle_data["error"] = str(e)

async def run_tournament(tournament_id: str, tournament_data: Dict[str, Any], db: Session):
    """Run a round-robin tournament"""
    try:
        models = tournament_data["models"]
        games_per_pair = tournament_data["games_per_pair"]
        
        tournament_data["status"] = "running"
        
        # Generate all matchups
        matchups = []
        for i, model1 in enumerate(models):
            for j, model2 in enumerate(models):
                if i != j:  # Don't play against self
                    for game_num in range(games_per_pair):
                        matchups.append((model1, model2))
        
        for idx, (white_model, black_model) in enumerate(matchups):
            if tournament_data["status"] == "stopped":
                break
                
            # Simulate game
            result = await simulate_tournament_game(white_model, black_model)
            
            # Update results
            if white_model not in tournament_data["results"]:
                tournament_data["results"][white_model] = {"wins": 0, "draws": 0, "losses": 0}
            if black_model not in tournament_data["results"]:
                tournament_data["results"][black_model] = {"wins": 0, "draws": 0, "losses": 0}
            
            if result == "1-0":
                tournament_data["results"][white_model]["wins"] += 1
                tournament_data["results"][black_model]["losses"] += 1
            elif result == "0-1":
                tournament_data["results"][black_model]["wins"] += 1
                tournament_data["results"][white_model]["losses"] += 1
            else:
                tournament_data["results"][white_model]["draws"] += 1
                tournament_data["results"][black_model]["draws"] += 1
            
            tournament_data["completed_games"] = idx + 1
            
            # Broadcast update
            await websocket_manager.broadcast_to_arena({
                "type": "tournament_update",
                "data": tournament_data
            })
            
            await asyncio.sleep(1.0 / tournament_data["speed"])
        
        tournament_data["status"] = "completed"
        
        # Broadcast completion
        await websocket_manager.broadcast_to_arena({
            "type": "tournament_finished",
            "data": tournament_data
        })
        
    except Exception as e:
        print(f"Error in tournament {tournament_id}: {e}")
        tournament_data["status"] = "error"
        tournament_data["error"] = str(e)

async def simulate_game(battle_data: Dict[str, Any], model_manager: ModelManager, game_service: GameService):
    """Simulate a game between two models"""
    import random
    
    # Simulate game result
    results = ["1-0", "0-1", "1/2-1/2"]
    weights = [0.4, 0.4, 0.2]  # 40% white wins, 40% black wins, 20% draws
    result = random.choices(results, weights=weights)[0]
    
    if result == "1-0":
        battle_data["white_wins"] += 1
    elif result == "0-1":
        battle_data["black_wins"] += 1
    else:
        battle_data["draws"] += 1
    
    # Simulate some moves for the current board
    battle_data["current_board"] = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"

async def simulate_tournament_game(white_model: str, black_model: str) -> str:
    """Simulate a tournament game"""
    import random
    
    results = ["1-0", "0-1", "1/2-1/2"]
    weights = [0.4, 0.4, 0.2]
    return random.choices(results, weights=weights)[0]