from pydantic import BaseModel
from typing import List, Optional

class BattleRequest(BaseModel):
    white_model: str
    black_model: str
    opening: str = "1. e4"
    num_games: int = 1
    speed: float = 1.0

class TournamentRequest(BaseModel):
    models: List[str]
    games_per_pair: int = 3
    speed: float = 1.0