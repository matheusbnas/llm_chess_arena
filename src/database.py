import sqlite3
import json
import os
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timedelta
import chess.pgn
from io import StringIO
from src.analysis import GameAnalyzer
import glob
import re

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
            
            conn.commit()
    
    def save_game(self, game_data: Dict[str, Any]) -> int:
        """Save a game to the database e já atualiza o ELO"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT INTO games (white, black, result, pgn, moves, opening, date, analysis_data)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                game_data['white'],
                game_data['black'],
                game_data['result'],
                game_data['pgn'],
                game_data.get('moves', 0),
                game_data.get('opening', ''),
                game_data.get('date', datetime.now().isoformat()),
                json.dumps(game_data.get('analysis', {}))
            ))
            
            game_id = cursor.lastrowid

            # Atualiza estatísticas dos modelos
            self._update_model_stats(game_data['white'], game_data['black'], game_data['result'])

            # --- NOVO: Atualiza ELO e histórico ---
            K = 32
            def expected_score(rating_a, rating_b):
                return 1 / (1 + 10 ** ((rating_b - rating_a) / 400))
            def update_elo(rating_a, rating_b, score_a):
                exp_a = expected_score(rating_a, rating_b)
                return round(rating_a + K * (score_a - exp_a))

            # Busca ELO atual dos modelos
            cursor.execute("SELECT current_elo FROM model_stats WHERE model_name = ?", (game_data['white'],))
            white_elo = cursor.fetchone()
            white_elo = white_elo[0] if white_elo else 1500
            cursor.execute("SELECT current_elo FROM model_stats WHERE model_name = ?", (game_data['black'],))
            black_elo = cursor.fetchone()
            black_elo = black_elo[0] if black_elo else 1500

            # Define resultado numérico
            if game_data['result'] == "1-0":
                score_white, score_black = 1, 0
            elif game_data['result'] == "0-1":
                score_white, score_black = 0, 1
            else:
                score_white, score_black = 0.5, 0.5

            # Calcula novo ELO
            new_white_elo = update_elo(white_elo, black_elo, score_white)
            new_black_elo = update_elo(black_elo, white_elo, score_black)

            # Salva histórico de ELO
            now = datetime.now().isoformat()
            cursor.execute(
                "INSERT INTO elo_history (model_name, elo_rating, date, game_id) VALUES (?, ?, ?, ?)",
                (game_data['white'], new_white_elo, now, game_id)
            )
            cursor.execute(
                "INSERT INTO elo_history (model_name, elo_rating, date, game_id) VALUES (?, ?, ?, ?)",
                (game_data['black'], new_black_elo, now, game_id)
            )

            # Atualiza ELO atual em model_stats
            cursor.execute(
                "UPDATE model_stats SET current_elo = ?, last_updated = ? WHERE model_name = ?",
                (new_white_elo, now, game_data['white'])
            )
            cursor.execute(
                "UPDATE model_stats SET current_elo = ?, last_updated = ? WHERE model_name = ?",
                (new_black_elo, now, game_data['black'])
            )

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
                SELECT id, white, black, result, pgn, moves, opening, date, analysis_data
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
                    'analysis': json.loads(row[8]) if row[8] else {}
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
            
            return {
                'total_games': total_games,
                'active_models': active_models,
                'avg_game_length': avg_game_length
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
                        (id, white, black, result, pgn, moves, opening, date, analysis_data, created_at)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        game.get('id'),
                        game.get('white'),
                        game.get('black'),
                        game.get('result'),
                        game.get('pgn'),
                        game.get('moves'),
                        game.get('opening'),
                        game.get('date'),
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
            
            conn.commit()
        
        # Reinitialize
        self._initialize_database()
    
    def recalculate_all_stats_and_elo(self):
        """Recalcula estatísticas e ELO de todos os modelos a partir dos jogos existentes"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            # Limpa model_stats e elo_history
            cursor.execute("DELETE FROM model_stats")
            cursor.execute("DELETE FROM elo_history")

            # Busca todos os jogos em ordem de data
            cursor.execute("SELECT id, white, black, result, date FROM games ORDER BY date, id")
            games = cursor.fetchall()

            # Inicializa stats e ELO
            stats = {}
            elo = {}
            K = 32
            START_ELO = 1500

            def expected_score(rating_a, rating_b):
                return 1 / (1 + 10 ** ((rating_b - rating_a) / 400))
            def update_elo(rating_a, rating_b, score_a):
                exp_a = expected_score(rating_a, rating_b)
                return round(rating_a + K * (score_a - exp_a))

            for game_id, white, black, result, date in games:
                for model in [white, black]:
                    if model not in stats:
                        stats[model] = {"games_played": 0, "wins": 0, "draws": 0, "losses": 0}
                    if model not in elo:
                        elo[model] = START_ELO

                # Atualiza stats
                stats[white]["games_played"] += 1
                stats[black]["games_played"] += 1
                if result == "1-0":
                    stats[white]["wins"] += 1
                    stats[black]["losses"] += 1
                    score_white, score_black = 1, 0
                elif result == "0-1":
                    stats[black]["wins"] += 1
                    stats[white]["losses"] += 1
                    score_white, score_black = 0, 1
                else:
                    stats[white]["draws"] += 1
                    stats[black]["draws"] += 1
                    score_white, score_black = 0.5, 0.5

                # Calcula novo ELO
                new_white_elo = update_elo(elo[white], elo[black], score_white)
                new_black_elo = update_elo(elo[black], elo[white], score_black)

                # Salva histórico de ELO
                cursor.execute(
                    "INSERT INTO elo_history (model_name, elo_rating, date, game_id) VALUES (?, ?, ?, ?)",
                    (white, new_white_elo, date or datetime.now().isoformat(), game_id)
                )
                cursor.execute(
                    "INSERT INTO elo_history (model_name, elo_rating, date, game_id) VALUES (?, ?, ?, ?)",
                    (black, new_black_elo, date or datetime.now().isoformat(), game_id)
                )

                # Atualiza ELO atual
                elo[white] = new_white_elo
                elo[black] = new_black_elo

            # Salva stats e ELO final em model_stats
            now = datetime.now().isoformat()
            for model in stats:
                cursor.execute("""
                    INSERT OR REPLACE INTO model_stats
                    (model_name, games_played, wins, draws, losses, current_elo, last_updated)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    model,
                    stats[model]["games_played"],
                    stats[model]["wins"],
                    stats[model]["draws"],
                    stats[model]["losses"],
                    elo[model],
                    now
                ))
            conn.commit()
    
    def get_opening_stats_from_db(self):
        """
        Retorna estatísticas de performance por abertura diretamente do banco.
        Para cada abertura: número de partidas, taxa de vitória das brancas, taxa de vitória das pretas, taxa de empate, média de lances.
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT 
                    opening, 
                    COUNT(*) as games_played,
                    SUM(CASE WHEN result = '1-0' THEN 1 ELSE 0 END) as white_wins,
                    SUM(CASE WHEN result = '0-1' THEN 1 ELSE 0 END) as black_wins,
                    SUM(CASE WHEN result = '1/2-1/2' THEN 1 ELSE 0 END) as draws,
                    AVG(moves) as avg_game_length
                FROM games
                WHERE opening IS NOT NULL AND opening != ''
                GROUP BY opening
                ORDER BY games_played DESC
            """)
            data = []
            for row in cursor.fetchall():
                opening = row[0]
                games_played = row[1]
                white_wins = row[2]
                black_wins = row[3]
                draws = row[4]
                avg_game_length = row[5] or 0

                # Taxas em percentual
                win_rate = (white_wins / games_played) if games_played > 0 else 0.0
                loss_rate = (black_wins / games_played) if games_played > 0 else 0.0
                draw_rate = (draws / games_played) if games_played > 0 else 0.0

                data.append({
                    'opening': opening,
                    'games_played': games_played,
                    'win_rate': win_rate,      # Taxa de vitória das brancas
                    'loss_rate': loss_rate,    # Taxa de vitória das pretas
                    'draw_rate': draw_rate,    # Taxa de empate
                    'avg_game_length': round(avg_game_length, 1)
                })
            return data
        
    def sync_filesystem_and_database(self, root_path="."):
        """
        Remove do banco de dados todos os jogos cujos arquivos .pgn não existem mais nas pastas de jogos.
        """
        # Busca todas as pastas de jogos (ex: Human_vs_*, * vs *)
        game_folders = [f for f in os.listdir(root_path) if os.path.isdir(os.path.join(root_path, f))]
        pattern = re.compile(r"(.+)_vs_(.+)|Human_vs_(.+)")

        # Coleta todos os jogos existentes no banco
        all_games = self.get_all_games()
        removed_count = 0

        for game in all_games:
            # Sanitize player names
            white = _sanitize_folder_name(game['white'])
            black = _sanitize_folder_name(game['black'])

            if white == "Humano":
                folder = f"Human_vs_{black}"
            elif black == "Humano":
                folder = f"Human_vs_{white}"
            else:
                folder = f"{white} vs {black}"

            folder_path = os.path.join(root_path, folder)

        # Após remover jogos, pode ser interessante recalcular stats e ELO
        self.recalculate_all_stats_and_elo()
        return removed_count
    
    def fill_opening_and_analysis(self):
        """
        Preenche os campos opening e analysis_data das partidas existentes.
        """
        analyzer = GameAnalyzer()
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id, pgn FROM games")
            for game_id, pgn in cursor.fetchall():
                if not pgn:
                    continue
                game = chess.pgn.read_game(StringIO(pgn))
                if not game:
                    continue
                # Preenche opening
                opening = game.headers.get("Opening", "")
                if not opening:
                    opening = analyzer._get_opening_name(game)
                # Preenche analysis_data
                analysis = analyzer.analyze_game(game)
                analysis_json = json.dumps(analysis)
                cursor.execute(
                    "UPDATE games SET opening = ?, analysis_data = ? WHERE id = ?",
                    (opening, analysis_json, game_id)
                )
            conn.commit()

    def update_avg_accuracy(self):
        """
        Recalcula e atualiza o campo avg_accuracy em model_stats para cada modelo.
        """
        analyzer = GameAnalyzer()
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT model_name FROM model_stats")
            models = [row[0] for row in cursor.fetchall()]
            for model in models:
                cursor.execute("SELECT pgn, white, black FROM games WHERE white = ? OR black = ?", (model, model))
                accuracies = []
                for pgn, white, black in cursor.fetchall():
                    if not pgn:
                        continue
                    game = chess.pgn.read_game(StringIO(pgn))
                    if not game:
                        continue
                    analysis = analyzer.analyze_game(game)
                    if white == model:
                        accuracies.append(analysis['white_accuracy'])
                    else:
                        accuracies.append(analysis['black_accuracy'])
                avg_acc = sum(accuracies) / len(accuracies) if accuracies else 0
                cursor.execute("UPDATE model_stats SET avg_accuracy = ? WHERE model_name = ?", (avg_acc, model))
            conn.commit()

    def export_training_data(self, export_path="training_data.jsonl"):
        """
        Exporta os dados da tabela training_data para um arquivo .jsonl.
        """
        with sqlite3.connect(self.db_path) as conn, open(export_path, "w", encoding="utf-8") as f:
            cursor = conn.cursor()
            cursor.execute("SELECT position_fen, best_move, evaluation, source, rating FROM training_data")
            for row in cursor.fetchall():
                data = {
                    "fen": row[0],
                    "best_move": row[1],
                    "evaluation": row[2],
                    "source": row[3],
                    "rating": row[4]
                }
                f.write(json.dumps(data) + "\n")

def _sanitize_folder_name(name: str) -> str:
    # Remove barras, backslashes, .., e caracteres não alfanuméricos básicos
    name = os.path.basename(name)
    name = re.sub(r'[^a-zA-Z0-9_\- ]', '', name)
    name = name.replace('..', '')
    return name.strip()