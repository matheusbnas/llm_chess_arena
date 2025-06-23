import chess
import chess.pgn
from typing import Optional, Dict, Any, List, Tuple
import re
import time
from datetime import datetime
from .models import ModelManager


class GameEngine:
    """Handles chess game logic and AI move generation"""

    def __init__(self):
        self.model_manager = ModelManager()
        self.judge_model = None
        self._initialize_judge()

    def _initialize_judge(self):
        """Initialize the judge model for move validation"""
        available_models = self.model_manager.get_available_models()

        # Prefer Groq models for judging (faster)
        if "Llama3-70B" in available_models and available_models["Llama3-70B"]:
            self.judge_model = self.model_manager.get_model("Llama3-70B")
        elif "Mixtral-8x7B" in available_models and available_models["Mixtral-8x7B"]:
            self.judge_model = self.model_manager.get_model("Mixtral-8x7B")
        else:
            # Fallback to any available model
            for model_name, status in available_models.items():
                if status:
                    self.judge_model = self.model_manager.get_model(model_name)
                    break

    def get_ai_move(self, board: chess.Board, model_name: str, difficulty: str = "Advanced",
                    last_move: str = None, max_retries: int = 3) -> Optional[chess.Move]:
        """Get a move from an AI model"""

        model = self.model_manager.get_model(model_name)
        if not model:
            return None

        color = "white" if board.turn == chess.WHITE else "black"
        prompt = self.model_manager.get_chess_prompt(color)
        chain = prompt | model

        # Prepare game context
        game_context = self._prepare_game_context(board, last_move)

        for attempt in range(max_retries):
            try:
                # Get model response
                response = chain.invoke({"input": game_context})
                move_text = response.content.strip()

                # Extract move from response
                extracted_move = self._extract_move(move_text)

                if extracted_move:
                    # Validate move with judge if available
                    if self.judge_model:
                        validated_move = self._validate_move_with_judge(
                            extracted_move, board, attempt > 0
                        )
                        if validated_move:
                            try:
                                move = board.parse_san(validated_move)
                                return move
                            except ValueError:
                                continue
                    else:
                        # Direct validation
                        try:
                            move = board.parse_san(extracted_move)
                            return move
                        except ValueError:
                            continue

            except Exception as e:
                print(f"Error getting move from {model_name}: {e}")
                continue

        # Fallback: return a random legal move
        legal_moves = list(board.legal_moves)
        if legal_moves:
            return legal_moves[0]

        return None

    def _prepare_game_context(self, board: chess.Board, last_move: str = None) -> str:
        """Prepare the game context for the AI model"""

        # Get game history
        game_temp = chess.pgn.Game.from_board(board)
        history = str(game_temp)

        # Clean up history
        pattern = r".*?(?=1\.)"
        history = re.sub(pattern, "", history, flags=re.DOTALL)

        # Get legal moves
        legal_moves = [board.san(move) for move in board.legal_moves]

        context = f"""
        Game History:
        {history}
        
        Last move played: {last_move or "Game start"}
        
        Current position (FEN): {board.fen()}
        
        Legal moves available: {', '.join(legal_moves[:20])}{'...' if len(legal_moves) > 20 else ''}
        
        Find the best move for this position.
        """

        return context

    def _extract_move(self, response_text: str) -> Optional[str]:
        """Extract chess move from model response"""

        # Look for "My move: " pattern
        move_pattern = r'My move:\s*["\']?([^"\']+)["\']?'
        match = re.search(move_pattern, response_text, re.IGNORECASE)

        if match:
            move = match.group(1).strip()
            # Clean up the move
            move = re.sub(r'[^\w\-\+\#\=]', '', move)
            return move

        # Fallback: look for chess move patterns
        chess_patterns = [
            r'\b([a-h][1-8])\b',  # Simple pawn moves
            r'\b([NBRQK][a-h]?[1-8]?x?[a-h][1-8])\b',  # Piece moves
            r'\b(O-O-O|O-O)\b',  # Castling
            r'\b([a-h]x[a-h][1-8])\b',  # Pawn captures
        ]

        for pattern in chess_patterns:
            matches = re.findall(pattern, response_text)
            if matches:
                return matches[0]

        return None

    def _validate_move_with_judge(self, proposed_move: str, board: chess.Board,
                                  is_retry: bool = False) -> Optional[str]:
        """Validate move using judge model"""

        if not self.judge_model:
            return proposed_move

        legal_moves = [board.san(move) for move in board.legal_moves]

        judge_prompt = f"""
        You are a chess arbiter. Validate this move:
        
        Proposed move: {proposed_move}
        Legal moves: {', '.join(legal_moves)}
        
        If the proposed move is in the legal moves list, respond with exactly that move.
        If not, respond with "INVALID".
        
        Response:
        """

        try:
            from langchain_core.prompts import PromptTemplate

            prompt = PromptTemplate.from_template(judge_prompt)
            chain = prompt | self.judge_model

            response = chain.invoke(
                {"proposed_move": proposed_move, "legal_moves": str(legal_moves)})
            result = response.content.strip()

            if result != "INVALID" and result in legal_moves:
                return result

        except Exception as e:
            print(f"Judge validation error: {e}")

        return None

    def play_game(self, white_model: str, black_model: str, opening: str = "1. e4",
                  max_moves: int = 200) -> Dict[str, Any]:
        """Play a complete game between two models"""

        board = chess.Board()
        game = chess.pgn.Game()
        node = game

        # Set up game headers
        game.headers["White"] = white_model
        game.headers["Black"] = black_model
        game.headers["Date"] = datetime.now().strftime("%Y.%m.%d")
        game.headers["Event"] = "LLM Chess Arena"

        # Play opening move
        opening_move = opening.split()[-1]
        try:
            move = board.parse_san(opening_move)
            board.push(move)
            node = node.add_variation(move)
        except ValueError:
            # Invalid opening, start with e4
            move = board.parse_san("e4")
            board.push(move)
            node = node.add_variation(move)

        last_move = opening
        move_count = 0

        # Game loop
        while not board.is_game_over() and move_count < max_moves:
            current_model = black_model if board.turn == chess.BLACK else white_model
            color = "black" if board.turn == chess.BLACK else "white"

            # Get move from current model
            move = self.get_ai_move(board, current_model, last_move=last_move)

            if move:
                board.push(move)
                node = node.add_variation(move)
                last_move = board.san(move)
                move_count += 1

                print(f"Move {move_count}: {current_model} played {last_move}")
            else:
                print(f"No valid move from {current_model}, ending game")
                break

        # Set result
        result = board.result()
        game.headers["Result"] = result

        return {
            "pgn": str(game),
            "result": result,
            "moves": move_count,
            "white": white_model,
            "black": black_model,
            "board": board,
            "game": game
        }
