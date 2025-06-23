import chess
import chess.pgn
from typing import Dict, List, Any, Optional, Tuple
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from io import StringIO
import math


class GameAnalyzer:
    """Analyzes chess games and provides insights"""

    def __init__(self):
        pass

    def analyze_game(self, game: chess.pgn.Game, depth: int = 15) -> Dict[str, Any]:
        """Analyze a complete game"""
        return self._analyze_without_engine(game)

    def _analyze_without_engine(self, game: chess.pgn.Game) -> Dict[str, Any]:
        """Basic analysis without engine"""

        board = chess.Board()
        move_count = 0
        captures = 0
        checks = 0
        castles = 0

        for node in game.mainline():
            if node.move:
                move_count += 1
                move = node.move

                # Count special moves
                if board.is_capture(move):
                    captures += 1

                board.push(move)

                if board.is_check():
                    checks += 1

                if move in [chess.Move.from_uci("e1g1"), chess.Move.from_uci("e1c1"),
                            chess.Move.from_uci("e8g8"), chess.Move.from_uci("e8c8")]:
                    castles += 1

        return {
            'total_moves': move_count,
            'white_accuracy': 0.0,
            'black_accuracy': 0.0,
            'move_evaluations': [],
            'move_accuracies': [],
            'blunders': 0,
            'best_moves': [],
            'worst_moves': [],
            'captures': captures,
            'checks': checks,
            'castles': castles,
            'average_evaluation': 0
        }

    def compare_models(self, model1: str, model2: str, db) -> Dict[str, Any]:
        """Compare two models head-to-head"""

        # Get games between these models
        games = db.get_games_between_models(model1, model2)

        if not games:
            return {"error": "No games found between these models"}

        model1_wins = 0
        model2_wins = 0
        draws = 0

        model1_accuracies = []
        model2_accuracies = []
        model1_times = []
        model2_times = []

        performance_over_time = []

        for i, game_data in enumerate(games):
            result = game_data['result']
            white = game_data['white']
            black = game_data['black']

            # Count results
            if result == "1-0":
                if white == model1:
                    model1_wins += 1
                else:
                    model2_wins += 1
            elif result == "0-1":
                if black == model1:
                    model1_wins += 1
                else:
                    model2_wins += 1
            else:
                draws += 1

            # Analyze game for accuracy
            game_pgn = chess.pgn.read_game(StringIO(game_data['pgn']))
            analysis = self.analyze_game(game_pgn)

            if white == model1:
                model1_accuracies.append(analysis['white_accuracy'])
                model2_accuracies.append(analysis['black_accuracy'])
            else:
                model1_accuracies.append(analysis['black_accuracy'])
                model2_accuracies.append(analysis['white_accuracy'])

            # Track performance over time
            performance_over_time.append({
                'game_number': i + 1,
                'model': model1,
                'accuracy': model1_accuracies[-1]
            })
            performance_over_time.append({
                'game_number': i + 1,
                'model': model2,
                'accuracy': model2_accuracies[-1]
            })

        return {
            'model1_wins': model1_wins,
            'model2_wins': model2_wins,
            'draws': draws,
            'model1_accuracy': np.mean(model1_accuracies) if model1_accuracies else 0,
            'model2_accuracy': np.mean(model2_accuracies) if model2_accuracies else 0,
            'model1_avg_moves': np.mean([g['moves'] for g in games if g['white'] == model1 or g['black'] == model1]),
            'model2_avg_moves': np.mean([g['moves'] for g in games if g['white'] == model2 or g['black'] == model2]),
            'model1_error_rate': 100 - np.mean(model1_accuracies) if model1_accuracies else 0,
            'model2_error_rate': 100 - np.mean(model2_accuracies) if model2_accuracies else 0,
            'model1_avg_time': np.mean(model1_times) if model1_times else 0,
            'model2_avg_time': np.mean(model2_times) if model2_times else 0,
            'performance_over_time': performance_over_time
        }

    def calculate_elo_ratings(self, games: List[Dict], initial_rating: int = 1500) -> Dict[str, Dict]:
        """Calculate ELO ratings for all models"""

        ratings = {}
        games_played = {}

        # Initialize ratings
        for game in games:
            for player in [game['white'], game['black']]:
                if player not in ratings:
                    ratings[player] = initial_rating
                    games_played[player] = 0

        # Process games chronologically
        sorted_games = sorted(games, key=lambda x: x.get('date', ''))

        for game in sorted_games:
            white = game['white']
            black = game['black']
            result = game['result']

            # Get current ratings
            white_rating = ratings[white]
            black_rating = ratings[black]

            # Calculate expected scores
            white_expected = 1 / \
                (1 + 10**((black_rating - white_rating) / 400))
            black_expected = 1 - white_expected

            # Determine actual scores
            if result == "1-0":
                white_score, black_score = 1, 0
            elif result == "0-1":
                white_score, black_score = 0, 1
            else:
                white_score, black_score = 0.5, 0.5

            # Calculate K-factor (higher for fewer games)
            white_k = 32 if games_played[white] < 30 else 16
            black_k = 32 if games_played[black] < 30 else 16

            # Update ratings
            ratings[white] += white_k * (white_score - white_expected)
            ratings[black] += black_k * (black_score - black_expected)

            games_played[white] += 1
            games_played[black] += 1

        # Calculate additional statistics
        result_data = {}
        for model in ratings.keys():
            model_games = [g for g in games if g['white']
                           == model or g['black'] == model]

            wins = sum(1 for g in model_games if
                       (g['white'] == model and g['result'] == "1-0") or
                       (g['black'] == model and g['result'] == "0-1"))

            total = len(model_games)
            win_rate = wins / total if total > 0 else 0

            # Calculate average accuracy from game analysis
            accuracies = []
            for game_data in model_games:
                game_pgn = chess.pgn.read_game(
                    StringIO(game_data.get('pgn', '')))
                if game_pgn:
                    analysis = self.analyze_game(game_pgn)
                    if game_data['white'] == model:
                        accuracies.append(analysis['white_accuracy'])
                    else:
                        accuracies.append(analysis['black_accuracy'])

            result_data[model] = {
                'model': model,
                'elo': round(ratings[model]),
                'games_played': games_played[model],
                'win_rate': win_rate,
                'avg_accuracy': np.mean(accuracies) if accuracies else 0
            }

        return result_data

    def get_detailed_stats(self, model: str, db) -> Dict[str, Any]:
        """Get detailed statistics for a specific model"""

        games = db.get_games_for_model(model)

        if not games:
            return {"error": "No games found for this model"}

        total_games = len(games)
        wins = sum(1 for g in games if
                   (g['white'] == model and g['result'] == "1-0") or
                   (g['black'] == model and g['result'] == "0-1"))
        draws = sum(1 for g in games if g['result'] == "1/2-1/2")
        losses = total_games - wins - draws

        win_rate = (wins / total_games * 100) if total_games > 0 else 0

        # Analyze by color
        white_games = [g for g in games if g['white'] == model]
        black_games = [g for g in games if g['black'] == model]

        white_wins = sum(1 for g in white_games if g['result'] == "1-0")
        black_wins = sum(1 for g in black_games if g['result'] == "0-1")

        white_draws = sum(1 for g in white_games if g['result'] == "1/2-1/2")
        black_draws = sum(1 for g in black_games if g['result'] == "1/2-1/2")

        # Calculate accuracies
        accuracies = []
        for game_data in games:
            game_pgn = chess.pgn.read_game(StringIO(game_data.get('pgn', '')))
            if game_pgn:
                analysis = self.analyze_game(game_pgn)
                if game_data['white'] == model:
                    accuracies.append(analysis['white_accuracy'])
                else:
                    accuracies.append(analysis['black_accuracy'])

        avg_accuracy = np.mean(accuracies) if accuracies else 0

        # Recent performance (last 20 games)
        recent_games = games[-20:] if len(games) >= 20 else games
        recent_accuracies = []

        for game_data in recent_games:
            game_pgn = chess.pgn.read_game(StringIO(game_data.get('pgn', '')))
            if game_pgn:
                analysis = self.analyze_game(game_pgn)
                if game_data['white'] == model:
                    recent_accuracies.append(analysis['white_accuracy'])
                else:
                    recent_accuracies.append(analysis['black_accuracy'])

        return {
            'total_games': total_games,
            'wins': wins,
            'draws': draws,
            'losses': losses,
            'win_rate': win_rate,
            'avg_accuracy': avg_accuracy,
            'current_elo': 1500,  # Would need to calculate from ELO system
            'by_color': {
                'white': {
                    'wins': white_wins,
                    'draws': white_draws,
                    'losses': len(white_games) - white_wins - white_draws
                },
                'black': {
                    'wins': black_wins,
                    'draws': black_draws,
                    'losses': len(black_games) - black_wins - black_draws
                }
            },
            'recent_trend': recent_accuracies
        }

    def get_opening_statistics(self, db) -> List[Dict[str, Any]]:
        """Get statistics by opening"""

        games = db.get_all_games()
        opening_stats = {}

        for game_data in games:
            game_pgn = chess.pgn.read_game(StringIO(game_data.get('pgn', '')))
            if not game_pgn:
                continue

            # Get opening name (simplified)
            opening = self._get_opening_name(game_pgn)

            if opening not in opening_stats:
                opening_stats[opening] = {
                    'opening': opening,
                    'games_played': 0,
                    'white_wins': 0,
                    'black_wins': 0,
                    'draws': 0,
                    'total_moves': 0,
                    'accuracies': []
                }

            stats = opening_stats[opening]
            stats['games_played'] += 1
            stats['total_moves'] += game_data.get('moves', 0)

            result = game_data['result']
            if result == "1-0":
                stats['white_wins'] += 1
            elif result == "0-1":
                stats['black_wins'] += 1
            else:
                stats['draws'] += 1

            # Add accuracy data
            analysis = self.analyze_game(game_pgn)
            avg_accuracy = (analysis['white_accuracy'] +
                            analysis['black_accuracy']) / 2
            stats['accuracies'].append(avg_accuracy)

        # Calculate final statistics
        result = []
        for opening, stats in opening_stats.items():
            if stats['games_played'] >= 3:  # Only include openings with enough games
                win_rate = (stats['white_wins'] +
                            stats['black_wins']) / stats['games_played']
                avg_accuracy = np.mean(
                    stats['accuracies']) if stats['accuracies'] else 0
                avg_game_length = stats['total_moves'] / stats['games_played']

                result.append({
                    'opening': opening,
                    'games_played': stats['games_played'],
                    'win_rate': win_rate,
                    'avg_accuracy': avg_accuracy,
                    'avg_game_length': avg_game_length
                })

        return result

    def _get_opening_name(self, game: chess.pgn.Game) -> str:
        """Get opening name from game"""

        # Try to get from headers first
        opening = game.headers.get("Opening", "")
        if opening:
            return opening

        # Basic opening detection
        board = chess.Board()
        moves = []

        for node in game.mainline():
            if node.move and len(moves) < 6:  # First 3 moves each
                moves.append(board.san(node.move))
                board.push(node.move)

        if not moves:
            return "Unknown"

        first_move = moves[0]

        openings = {
            "e4": "King's Pawn",
            "d4": "Queen's Pawn",
            "Nf3": "Réti Opening",
            "c4": "English Opening",
            "g3": "King's Indian Attack",
            "b3": "Nimzo-Larsen Attack",
            "f4": "Bird's Opening",
            "Nc3": "Van Geet Opening"
        }

        return openings.get(first_move, "Other")

    def process_lichess_games(self, lichess_games: List[Dict]) -> Dict[str, Any]:
        """Process Lichess games for training data"""

        training_data = {
            'positions': [],
            'evaluations': [],
            'best_moves': [],
            'openings': [],
            'endgames': []
        }

        for game_data in lichess_games:
            try:
                game = chess.pgn.read_game(StringIO(game_data['pgn']))
                if not game:
                    continue

                board = chess.Board()
                move_count = 0

                for node in game.mainline():
                    if node.move:
                        move_count += 1

                        # Store position data
                        position_data = {
                            'fen': board.fen(),
                            'move': board.san(node.move),
                            'move_number': move_count,
                            'rating': game_data.get('rating', 1500)
                        }

                        # Categorize by game phase
                        if move_count <= 10:
                            training_data['openings'].append(position_data)
                        elif move_count >= 40:
                            training_data['endgames'].append(position_data)
                        else:
                            training_data['positions'].append(position_data)

                        board.push(node.move)

            except Exception as e:
                print(f"Error processing Lichess game: {e}")
                continue

        return training_data

    def apply_rag_improvements(self) -> Dict[str, Dict[str, float]]:
        """Apply RAG improvements based on training data"""

        # This would implement actual RAG improvements
        # For now, return simulated improvements

        improvements = {
            'GPT-4o': {
                'accuracy_gain': 2.5,
                'performance_gain': 1.8
            },
            'Gemini-Pro': {
                'accuracy_gain': 3.1,
                'performance_gain': 2.2
            },
            'Deepseek-Chat': {
                'accuracy_gain': 1.9,
                'performance_gain': 1.5
            }
        }

        return improvements
