import requests
import chess.pgn
from typing import List, Dict, Optional, Any
import time
from io import StringIO

class LichessAPI:
    """Interface with Lichess API for game data and analysis"""
    
    def __init__(self):
        self.base_url = "https://lichess.org/api"
        self.token = None
        self.session = requests.Session()
        
    def set_token(self, token: str):
        """Set the Lichess API token"""
        self.token = token
        self.session.headers.update({
            'Authorization': f'Bearer {token}'
        })
    
    def test_connection(self, token: str = None) -> bool:
        """Test connection to Lichess API"""
        if token:
            self.set_token(token)
        
        try:
            response = self.session.get(f"{self.base_url}/account")
            return response.status_code == 200
        except Exception as e:
            print(f"Lichess connection error: {e}")
            return False
    
    def get_user_info(self, username: str) -> Optional[Dict[str, Any]]:
        """Get user information from Lichess"""
        try:
            response = self.session.get(f"{self.base_url}/user/{username}")
            if response.status_code == 200:
                return response.json()
        except Exception as e:
            print(f"Error getting user info: {e}")
        return None
    
    def import_user_games(self, username: str, max_games: int = 100, 
                         rated: bool = True, time_class: str = None) -> List[Dict[str, Any]]:
        """Import games from a Lichess user"""
        
        params = {
            'max': min(max_games, 300),  # Lichess API limit
            'rated': 'true' if rated else 'false',
            'format': 'pgn'
        }
        
        if time_class:
            params['perfType'] = time_class
        
        try:
            response = self.session.get(
                f"{self.base_url}/games/user/{username}",
                params=params,
                stream=True
            )
            
            if response.status_code != 200:
                print(f"Error: {response.status_code}")
                return []
            
            games = []
            current_pgn = ""
            
            for line in response.iter_lines(decode_unicode=True):
                if line.strip():
                    current_pgn += line + "\n"
                else:
                    if current_pgn.strip():
                        # Parse the PGN
                        game = chess.pgn.read_game(StringIO(current_pgn))
                        if game:
                            game_data = self._extract_game_data(game, current_pgn)
                            if game_data:
                                games.append(game_data)
                        current_pgn = ""
                
                if len(games) >= max_games:
                    break
            
            # Process last game if exists
            if current_pgn.strip():
                game = chess.pgn.read_game(StringIO(current_pgn))
                if game:
                    game_data = self._extract_game_data(game, current_pgn)
                    if game_data:
                        games.append(game_data)
            
            return games
            
        except Exception as e:
            print(f"Error importing games: {e}")
            return []
    
    def _extract_game_data(self, game: chess.pgn.Game, pgn_text: str) -> Optional[Dict[str, Any]]:
        """Extract relevant data from a chess game"""
        try:
            headers = game.headers
            
            # Count moves
            move_count = 0
            board = chess.Board()
            for node in game.mainline():
                if node.move:
                    move_count += 1
                    board.push(node.move)
            
            # Extract ratings
            white_elo = int(headers.get('WhiteElo', 0))
            black_elo = int(headers.get('BlackElo', 0))
            avg_rating = (white_elo + black_elo) / 2 if white_elo and black_elo else 0
            
            return {
                'white': headers.get('White', ''),
                'black': headers.get('Black', ''),
                'result': headers.get('Result', ''),
                'date': headers.get('UTCDate', ''),
                'time_control': headers.get('TimeControl', ''),
                'white_elo': white_elo,
                'black_elo': black_elo,
                'rating': avg_rating,
                'moves': move_count,
                'opening': headers.get('Opening', ''),
                'eco': headers.get('ECO', ''),
                'termination': headers.get('Termination', ''),
                'pgn': pgn_text.strip()
            }
            
        except Exception as e:
            print(f"Error extracting game data: {e}")
            return None
    
    def get_top_games(self, count: int = 50) -> List[Dict[str, Any]]:
        """Get top-rated games from Lichess"""
        try:
            response = self.session.get(
                f"{self.base_url}/games/export/_ids",
                params={'format': 'pgn'}
            )
            
            # This would need specific game IDs
            # For now, return empty list
            return []
            
        except Exception as e:
            print(f"Error getting top games: {e}")
            return []
    
    def search_games(self, query: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Search for games with specific criteria"""
        
        # Build search parameters
        params = {}
        
        if 'rating_min' in query:
            params['ratingMin'] = query['rating_min']
        if 'rating_max' in query:
            params['ratingMax'] = query['rating_max']
        if 'opening' in query:
            params['opening'] = query['opening']
        if 'time_class' in query:
            params['perfType'] = query['time_class']
        
        try:
            # Note: Lichess doesn't have a direct search API
            # This would need to be implemented differently
            return []
            
        except Exception as e:
            print(f"Error searching games: {e}")
            return []
    
    def get_opening_stats(self, opening_code: str) -> Dict[str, Any]:
        """Get statistics for a specific opening"""
        try:
            response = self.session.get(f"{self.base_url}/opening/{opening_code}")
            if response.status_code == 200:
                return response.json()
        except Exception as e:
            print(f"Error getting opening stats: {e}")
        return {}
    
    def get_master_games(self, opening: str = None, max_games: int = 100) -> List[Dict[str, Any]]:
        """Get master games from Lichess database"""
        
        params = {
            'max': min(max_games, 200),
            'format': 'pgn'
        }
        
        if opening:
            params['opening'] = opening
        
        try:
            response = self.session.get(
                f"{self.base_url}/master",
                params=params
            )
            
            if response.status_code == 200:
                # Parse PGN response similar to user games
                return self._parse_pgn_response(response.text)
            
        except Exception as e:
            print(f"Error getting master games: {e}")
        
        return []
    
    def _parse_pgn_response(self, pgn_text: str) -> List[Dict[str, Any]]:
        """Parse PGN text response into game data"""
        games = []
        current_pgn = ""
        
        for line in pgn_text.split('\n'):
            if line.strip():
                current_pgn += line + "\n"
            else:
                if current_pgn.strip():
                    game = chess.pgn.read_game(StringIO(current_pgn))
                    if game:
                        game_data = self._extract_game_data(game, current_pgn)
                        if game_data:
                            games.append(game_data)
                    current_pgn = ""
        
        return games
    
    def analyze_position(self, fen: str, depth: int = 15) -> Dict[str, Any]:
        """Analyze a position using Lichess cloud analysis"""
        try:
            response = self.session.post(
                f"{self.base_url}/cloud-eval",
                json={
                    'fen': fen,
                    'multiPv': 1,
                    'depth': depth
                }
            )
            
            if response.status_code == 200:
                return response.json()
                
        except Exception as e:
            print(f"Error analyzing position: {e}")
        
        return {}
    
    def get_puzzle_data(self, count: int = 100, rating_min: int = 1000, 
                       rating_max: int = 2500) -> List[Dict[str, Any]]:
        """Get puzzle data from Lichess"""
        try:
            response = self.session.get(
                f"{self.base_url}/puzzle/daily"
            )
            
            if response.status_code == 200:
                return [response.json()]
                
        except Exception as e:
            print(f"Error getting puzzles: {e}")
        
        return []
    
    def export_study(self, study_id: str) -> Optional[str]:
        """Export a Lichess study"""
        try:
            response = self.session.get(
                f"{self.base_url}/study/{study_id}.pgn"
            )
            
            if response.status_code == 200:
                return response.text
                
        except Exception as e:
            print(f"Error exporting study: {e}")
        
        return None
    
    def create_study(self, name: str, games: List[str]) -> Optional[str]:
        """Create a new study with games"""
        # This would require authentication and specific permissions
        # Implementation would depend on Lichess API capabilities
        return None
    
    def get_leaderboard(self, perf_type: str = "blitz") -> List[Dict[str, Any]]:
        """Get leaderboard for a specific time control"""
        try:
            response = self.session.get(f"{self.base_url}/leaderboard/{perf_type}")
            if response.status_code == 200:
                data = response.json()
                return data.get('users', [])
        except Exception as e:
            print(f"Error getting leaderboard: {e}")
        return []