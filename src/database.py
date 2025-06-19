import sqlite3
import json
import os
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timedelta
import chess.pgn
from io import StringIO

class GameDatabase:
    """Manages the SQLite database for storing games and statistics"""
    
    def __init__(self, db_path: str = "chess_arena.db"):
        self.db_path = db_path
        self._initialize_database()
    
    def _initialize_database(self):
        """Initialize the database with required tables"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Games table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS games (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    white TEXT NOT NULL,
                    black TEXT NOT NULL,
                    result TEXT NOT NULL,
                    pgn TEXT NOT NULL,
                    moves INTEGER,
                    opening TEXT,
                    date TEXT,
                    tournament_id TEXT,
                    white_elo INTEGER DEFAULT 1500,
                    black_elo INTEGER DEFAULT 1500,
                    analysis_data TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Model statistics table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS model_stats (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    model_name TEXT NOT NULL,
                    games_played INTEGER DEFAULT 0,
                    wins INTEGER DEFAULT 0,
                    draws INTEGER DEFAULT 0,
                    losses INTEGER DEFAULT 0,
                    current_elo INTEGER DEFAULT 1500,
                    avg_accuracy REAL DEFAULT 0.0,
                    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(model_name)
                )
            """)
            
            # ELO history table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS elo_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    model_name TEXT NOT NULL,
                    elo_rating INTEGER NOT NULL,
                    date TEXT NOT NULL,
                    game_id INTEGER,
                    FOREIGN KEY (game_id) REFERENCES games (id)
                )
            """)
            
            # Training data table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS training_data (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    position_fen TEXT NOT NULL,
                    best_move TEXT,
                    evaluation REAL,
                    source TEXT,
                    rating INTEGER,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Tournaments table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS tournaments (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    participants TEXT NOT NULL,
                    status TEXT DEFAULT 'active',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    completed_at TIMESTAMP
                )
            """)
            
            conn.commit()
    
    def save_game(self, game_data: Dict[str, Any]) -> int:
        """Save a game to the database"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT INTO games (white, black, result, pgn, moves, opening, date, tournament_id, analysis_data)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                game_data['white'],
                game_data['black'],
                game_data['result'],
                game_data['pgn'],
                game_data.get('moves', 0),
                game_data.get('opening', ''),
                game_data.get('date', datetime.now().isoformat()),
                game_data.get('tournament_id'),
                json.dumps(game_data.get('analysis', {}))
            ))
            
            game_id = cursor.lastrowid
            
            # Update model statistics
            self._update_model_stats(game_data['white'], game_data['black'], game_data['result'])
            
            conn.commit()
            return game_id
    
    def _update_model_stats(self, white: str, black: str, result: str):
        """Update model statistics after a game"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Initialize models if they don't exist
            for model in [white, black]:
                cursor.execute("""
                    INSERT OR IGNORE INTO model_stats (model_name) VALUES (?)
                """, (model,))
            
            # Update white player stats
            if result == "1-0":
                cursor.execute("""
                    UPDATE model_stats 
                    SET games_played = games_played + 1, wins = wins + 1, last_updated = CURRENT_TIMESTAMP
                    WHERE model_name = ?
                """, (white,))
            elif result == "0-1":
                cursor.execute("""
                    UPDATE model_stats 
                    SET games_played = games_played + 1, losses = losses + 1, last_updated = CURRENT_TIMESTAMP
                    WHERE model_name = ?
                """, (white,))
            else:  # Draw
                cursor.execute("""
                    UPDATE model_stats 
                    SET games_played = games_played + 1, draws = draws + 1, last_updated = CURRENT_TIMESTAMP
                    WHERE model_name = ?
                """, (white,))
            
            # Update black player stats
            if result == "0-1":
                cursor.execute("""
                    UPDATE model_stats 
                    SET games_played = games_played + 1, wins = wins + 1, last_updated = CURRENT_TIMESTAMP
                    WHERE model_name = ?
                """, (black,))
            elif result == "1-0":
                cursor.execute("""
                    UPDATE model_stats 
                    SET games_played = games_played + 1, losses = losses + 1, last_updated = CURRENT_TIMESTAMP
                    WHERE model_name = ?
                """, (black,))
            else:  # Draw
                cursor.execute("""
                    UPDATE model_stats 
                    SET games_played = games_played + 1, draws = draws + 1, last_updated = CURRENT_TIMESTAMP
                    WHERE model_name = ?
                """, (black,))
            
            conn.commit()
    
    def get_all_games(self) -> List[Dict[str, Any]]:
        """Get all games from the database"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, white, black, result, pgn, moves, opening, date, tournament_id, analysis_data
                FROM games ORDER BY created_at DESC
            """)
            
            games = []
            for row in cursor.fetchall():
                games.append({
                    'id': row[0],
                    'white': row[1],
                    'black': row[2],
                    'result': row[3],
                    'pgn': row[4],
                    'moves': row[5],
                    'opening': row[6],
                    'date': row[7],
                    'tournament_id': row[8],
                    'analysis': json.loads(row[9]) if row[9] else {}
                })
            
            return games
    
    def get_recent_games(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent games"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT white, black, result, moves, opening, date
                FROM games 
                ORDER BY created_at DESC 
                LIMIT ?
            """, (limit,))
            
            games = []
            for row in cursor.fetchall():
                games.append({
                    'White': row[0],
                    'Black': row[1],
                    'Result': row[2],
                    'Moves': row[3],
                    'Opening': row[4],
                    'Date': row[5]
                })
            
            return games
    
    def get_games_between_models(self, model1: str, model2: str) -> List[Dict[str, Any]]:
        """Get all games between two specific models"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT white, black, result, pgn, moves, date
                FROM games 
                WHERE (white = ? AND black = ?) OR (white = ? AND black = ?)
                ORDER BY created_at
            """, (model1, model2, model2, model1))
            
            games = []
            for row in cursor.fetchall():
                games.append({
                    'white': row[0],
                    'black': row[1],
                    'result': row[2],
                    'pgn': row[3],
                    'moves': row[4],
                    'date': row[5]
                })
            
            return games
    
    def get_games_for_model(self, model: str) -> List[Dict[str, Any]]:
        """Get all games for a specific model"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT white, black, result, pgn, moves, date
                FROM games 
                WHERE white = ? OR black = ?
                ORDER BY created_at
            """, (model, model))
            
            games = []
            for row in cursor.fetchall():
                games.append({
                    'white': row[0],
                    'black': row[1],
                    'result': row[2],
                    'pgn': row[3],
                    'moves': row[4],
                    'date': row[5]
                })
            
            return games
    
    def get_unique_models(self) -> List[str]:
        """Get list of unique models that have played games"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT DISTINCT model_name FROM model_stats
                WHERE games_played > 0
                ORDER BY model_name
            """)
            
            return [row[0] for row in cursor.fetchall()]
    
    def get_global_stats(self) -> Dict[str, Any]:
        """Get global statistics"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Total games
            cursor.execute("SELECT COUNT(*) FROM games")
            total_games = cursor.fetchone()[0]
            
            # Active models
            cursor.execute("SELECT COUNT(*) FROM model_stats WHERE games_played > 0")
            active_models = cursor.fetchone()[0]
            
            # Average game length
            cursor.execute("SELECT AVG(moves) FROM games WHERE moves > 0")
            avg_game_length = cursor.fetchone()[0] or 0
            
            # Tournaments completed
            cursor.execute("SELECT COUNT(*) FROM tournaments WHERE status = 'completed'")
            tournaments_completed = cursor.fetchone()[0]
            
            return {
                'total_games': total_games,
                'active_models': active_models,
                'avg_game_length': avg_game_length,
                'tournaments_completed': tournaments_completed
            }
    
    def get_results_by_model(self) -> List[Dict[str, Any]]:
        """Get win/draw/loss results by model"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT model_name, wins, draws, losses
                FROM model_stats
                WHERE games_played > 0
                ORDER BY wins DESC
            """)
            
            results = []
            for row in cursor.fetchall():
                results.append({
                    'model': row[0],
                    'wins': row[1],
                    'draws': row[2],
                    'losses': row[3]
                })
            
            return results
    
    def get_winrate_data(self) -> List[Dict[str, Any]]:
        """Get overall winrate distribution"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT 
                    SUM(CASE WHEN result = '1-0' THEN 1 ELSE 0 END) as white_wins,
                    SUM(CASE WHEN result = '0-1' THEN 1 ELSE 0 END) as black_wins,
                    SUM(CASE WHEN result = '1/2-1/2' THEN 1 ELSE 0 END) as draws
                FROM games
            """)
            
            row = cursor.fetchone()
            white_wins, black_wins, draws = row[0] or 0, row[1] or 0, row[2] or 0
            total = white_wins + black_wins + draws
            
            if total == 0:
                return []
            
            return [
                {'result_type': 'White Wins', 'percentage': white_wins},
                {'result_type': 'Black Wins', 'percentage': black_wins},
                {'result_type': 'Draws', 'percentage': draws}
            ]
    
    def save_elo_rating(self, model: str, elo: int, game_id: int = None):
        """Save ELO rating for a model"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO elo_history (model_name, elo_rating, date, game_id)
                VALUES (?, ?, ?, ?)
            """, (model, elo, datetime.now().isoformat(), game_id))
            
            # Update current ELO in model_stats
            cursor.execute("""
                UPDATE model_stats 
                SET current_elo = ?, last_updated = CURRENT_TIMESTAMP
                WHERE model_name = ?
            """, (elo, model))
            
            conn.commit()
    
    def get_elo_history(self) -> List[Dict[str, Any]]:
        """Get ELO rating history for all models"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT model_name, elo_rating, date
                FROM elo_history
                ORDER BY date
            """)
            
            history = []
            for row in cursor.fetchall():
                history.append({
                    'model': row[0],
                    'elo': row[1],
                    'date': row[2]
                })
            
            return history
    
    def save_training_data(self, training_data: Dict[str, Any]):
        """Save training data from Lichess games"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            for category, positions in training_data.items():
                for pos_data in positions:
                    cursor.execute("""
                        INSERT INTO training_data (position_fen, best_move, evaluation, source, rating)
                        VALUES (?, ?, ?, ?, ?)
                    """, (
                        pos_data.get('fen', ''),
                        pos_data.get('move', ''),
                        pos_data.get('evaluation', 0.0),
                        'lichess',
                        pos_data.get('rating', 1500)
                    ))
            
            conn.commit()
    
    def load_game_pgn(self, game_id: int) -> str:
        """Load PGN for a specific game"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT pgn FROM games WHERE id = ?", (game_id,))
            result = cursor.fetchone()
            return result[0] if result else ""
    
    def get_database_stats(self) -> Dict[str, Any]:
        """Get database statistics"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Total games
            cursor.execute("SELECT COUNT(*) FROM games")
            total_games = cursor.fetchone()[0]
            
            # Unique models
            cursor.execute("SELECT COUNT(DISTINCT model_name) FROM model_stats")
            unique_models = cursor.fetchone()[0]
            
            # Database size
            db_size_bytes = os.path.getsize(self.db_path) if os.path.exists(self.db_path) else 0
            db_size_mb = db_size_bytes / (1024 * 1024)
            
            return {
                'total_games': total_games,
                'unique_models': unique_models,
                'db_size_mb': db_size_mb
            }
    
    def export_all_data(self) -> Dict[str, Any]:
        """Export all data for backup"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Export games
            cursor.execute("SELECT * FROM games")
            games = [dict(zip([col[0] for col in cursor.description], row)) 
                    for row in cursor.fetchall()]
            
            # Export model stats
            cursor.execute("SELECT * FROM model_stats")
            model_stats = [dict(zip([col[0] for col in cursor.description], row)) 
                          for row in cursor.fetchall()]
            
            # Export ELO history
            cursor.execute("SELECT * FROM elo_history")
            elo_history = [dict(zip([col[0] for col in cursor.description], row)) 
                          for row in cursor.fetchall()]
            
            return {
                'games': games,
                'model_stats': model_stats,
                'elo_history': elo_history,
                'export_date': datetime.now().isoformat()
            }
    
    def import_data(self, data: Dict[str, Any]) -> bool:
        """Import data from backup"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Import games
                for game in data.get('games', []):
                    cursor.execute("""
                        INSERT OR REPLACE INTO games 
                        (id, white, black, result, pgn, moves, opening, date, tournament_id, analysis_data, created_at)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        game.get('id'),
                        game.get('white'),
                        game.get('black'),
                        game.get('result'),
                        game.get('pgn'),
                        game.get('moves'),
                        game.get('opening'),
                        game.get('date'),
                        game.get('tournament_id'),
                        game.get('analysis_data'),
                        game.get('created_at')
                    ))
                
                # Import model stats
                for stats in data.get('model_stats', []):
                    cursor.execute("""
                        INSERT OR REPLACE INTO model_stats 
                        (id, model_name, games_played, wins, draws, losses, current_elo, avg_accuracy, last_updated)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        stats.get('id'),
                        stats.get('model_name'),
                        stats.get('games_played'),
                        stats.get('wins'),
                        stats.get('draws'),
                        stats.get('losses'),
                        stats.get('current_elo'),
                        stats.get('avg_accuracy'),
                        stats.get('last_updated')
                    ))
                
                conn.commit()
                return True
                
        except Exception as e:
            print(f"Import error: {e}")
            return False
    
    def delete_old_games(self, days: int = 30) -> int:
        """Delete games older than specified days"""
        cutoff_date = datetime.now() - timedelta(days=days)
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                DELETE FROM games 
                WHERE created_at < ?
            """, (cutoff_date.isoformat(),))
            
            deleted_count = cursor.rowcount
            conn.commit()
            return deleted_count
    
    def reset_database(self):
        """Reset the entire database"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Drop all tables
            cursor.execute("DROP TABLE IF EXISTS games")
            cursor.execute("DROP TABLE IF EXISTS model_stats")
            cursor.execute("DROP TABLE IF EXISTS elo_history")
            cursor.execute("DROP TABLE IF EXISTS training_data")
            cursor.execute("DROP TABLE IF EXISTS tournaments")
            
            conn.commit()
        
        # Reinitialize
        self._initialize_database()