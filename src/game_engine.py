import chess
import chess.pgn
from typing import Optional, Dict, Any, List, Tuple
import re
import time
from datetime import datetime
from .models import ModelManager
import streamlit as st
from src.ui_components import UIComponents


class GameEngine:
    """Handles chess game logic and AI move generation"""

    def __init__(self):
        self.model_manager = ModelManager()
        self.judge_model = None
        self._initialize_judge()

    def _initialize_judge(self):
        """Initialize the judge model for move validation"""
        working_models = self.model_manager.get_working_models_only()

        # Prefer Groq models for judging (faster)
        if "Llama-3.3-70B" in working_models:
            self.judge_model = self.model_manager.get_model("Llama-3.3-70B")
        elif "Llama-3.1-8B" in working_models:
            self.judge_model = self.model_manager.get_model("Llama-3.1-8B")
        else:
            # Fallback to any available working model
            for model_name in working_models:
                self.judge_model = self.model_manager.get_model(model_name)
                break
                
        if self.judge_model:
            print(f"🧠 Judge model initialized: {list(working_models.keys())[0] if working_models else 'None'}")
        else:
            print("⚠️ No judge model available")

    def get_ai_move(self, board: chess.Board, model_name: str, difficulty: str = "Advanced",
                    last_move: str = None, max_retries: int = 3, use_fallback: bool = False):
        """
        Get a move and explanation from an AI model
        
        Args:
            board: Current chess board state
            model_name: Name of the LLM model to use
            difficulty: Difficulty level (not used currently)
            last_move: Last move played
            max_retries: Maximum number of retries
            use_fallback: Whether to use random move fallback if LLM fails
            
        Returns:
            tuple: (chess.Move, explanation) or (None, error_message)
        """
        # Verifica se o modelo está funcionando (usando cache)
        if not self.model_manager.is_model_working(model_name):
            error_msg = f"❌ ERRO: Modelo '{model_name}' não está disponível ou não tem chave válida!"
            print(error_msg)
            if 'st' in globals():
                st.error(error_msg)
            return None, error_msg
        
        model = self.model_manager.get_model(model_name)
        if not model:
            error_msg = f"❌ ERRO: Não foi possível carregar o modelo '{model_name}'"
            print(error_msg)
            if 'st' in globals():
                st.error(error_msg)
            return None, error_msg
        
        # Obtém o prompt específico para xadrez
        color = "white" if board.turn == chess.WHITE else "black"
        prompt = self.model_manager.get_chess_prompt(color)
        chain = prompt | model
        
        # Prepara o contexto do jogo
        game_context = self._prepare_game_context(board, last_move)
        
        print(f"🤖 Consultando modelo LLM '{model_name}' para obter lance...")
        
        # Tenta obter lance do modelo LLM
        for attempt in range(max_retries):
            try:
                print(f"   Tentativa {attempt + 1}/{max_retries}")
                
                # Chama o modelo LLM
                response = chain.invoke({"input": game_context})
                
                # Processa a resposta
                response_text = response.content.strip() if hasattr(response, 'content') else str(response)
                
                print(f"   Resposta do modelo: {response_text[:100]}...")
                
                # Extrai o lance da resposta
                move = self._extract_move_from_response(response_text, board)
                explanation = self._extract_explanation_from_response(response_text)
                
                if move and move in board.legal_moves:
                    print(f"✅ Lance válido obtido do modelo LLM: {board.san(move)}")
                    return move, explanation
                else:
                    print(f"   ❌ Lance inválido na tentativa {attempt + 1}: {move}")
                    
            except Exception as e:
                print(f"   ❌ Erro na tentativa {attempt + 1}: {str(e)}")
                continue
        
        # Se chegou aqui, o modelo LLM falhou em todas as tentativas
        error_msg = f"❌ FALHA CRÍTICA: Modelo LLM '{model_name}' falhou em {max_retries} tentativas!"
        print(error_msg)
        
        if use_fallback:
            # Usa fallback apenas se explicitamente solicitado
            legal_moves = list(board.legal_moves)
            if legal_moves:
                fallback_move = legal_moves[0]
                fallback_explanation = f"(⚠️ FALLBACK: Modelo LLM falhou - usando lance aleatório: {board.san(fallback_move)})"
                print(f"⚠️ Usando fallback: {board.san(fallback_move)}")
                if 'st' in globals():
                    st.warning(fallback_explanation)
                return fallback_move, fallback_explanation
        
        # Se não usa fallback ou não há lances legais, retorna erro
        if 'st' in globals():
            st.error(error_msg)
        return None, error_msg

    def _extract_move_from_response(self, response_text: str, board: chess.Board) -> Optional[chess.Move]:
        """Extract chess move from model response"""
        
        # Procura por padrões de "My move: " primeiro
        move_patterns = [
            r'My move:\s*["\']([^"\']+)["\']',  # My move: "e4"
            r'My move:\s*([^\s\n]+)',           # My move: e4
            r'move:\s*["\']([^"\']+)["\']',     # move: "e4"
            r'move:\s*([^\s\n]+)',              # move: e4
            r'lance:\s*["\']([^"\']+)["\']',    # lance: "e4" (português)
            r'lance:\s*([^\s\n]+)',             # lance: e4 (português)
        ]
        
        for pattern in move_patterns:
            match = re.search(pattern, response_text, re.IGNORECASE)
            if match:
                move_str = match.group(1).strip()
                try:
                    # Tenta converter para objeto Move
                    move = board.parse_san(move_str)
                    if move in board.legal_moves:
                        return move
                except:
                    continue
        
        # Se não encontrou com padrões, procura por lances válidos no texto
        legal_moves_san = [board.san(move) for move in board.legal_moves]
        
        # Divide o texto em palavras e procura por lances válidos
        words = re.findall(r'\b[a-zA-Z0-9+#=-]+\b', response_text)
        
        for word in words:
            if word in legal_moves_san:
                try:
                    return board.parse_san(word)
                except:
                    continue
        
        return None

    def _extract_explanation_from_response(self, response_text: str) -> str:
        """Extract explanation from model response"""
        
        # Remove a parte do lance da explicação
        explanation = response_text
        
        # Remove padrões de lance
        patterns_to_remove = [
            r'My move:\s*["\']?[^"\']+["\']?',
            r'move:\s*["\']?[^"\']+["\']?',
            r'lance:\s*["\']?[^"\']+["\']?',
        ]
        
        for pattern in patterns_to_remove:
            explanation = re.sub(pattern, '', explanation, flags=re.IGNORECASE)
        
        # Limpa a explicação
        explanation = explanation.strip()
        
        # Remove linhas vazias e espaços extras
        lines = [line.strip() for line in explanation.split('\n') if line.strip()]
        explanation = ' '.join(lines)
        
        # Se a explicação está vazia, retorna um padrão
        if not explanation:
            return "Lance estratégico escolhido pelo modelo LLM."
        
        return explanation

    def _prepare_game_context(self, board: chess.Board, last_move: str = None) -> str:
        """Prepare the game context for the AI model"""

        # Get game history
        game_temp = chess.pgn.Game.from_board(board)
        history = str(game_temp)

        # Clean up history to show only moves
        pattern = r".*?(?=1\.)"
        history = re.sub(pattern, "", history, flags=re.DOTALL)

        # Get legal moves
        legal_moves = [board.san(move) for move in board.legal_moves]

        # Get current position analysis
        material_balance = self._get_material_balance(board)
        
        context = f"""
        Current Chess Game Analysis:
        
        Game History (PGN moves):
        {history}
        
        Last move played: {last_move or "Game start"}
        
        Current position (FEN): {board.fen()}
        
        Material balance: {material_balance}
        
        Legal moves available: {', '.join(legal_moves[:15])}{'...' if len(legal_moves) > 15 else ''}
        
        Your task: Find the best move for this position. Consider:
        1. Piece safety and development
        2. Center control
        3. King safety
        4. Tactical opportunities
        5. Positional advantages
        6. Preserve material: avoid sacrificing high-value pieces (Queen=9, Rook=5, Bishop/Knight=3, Pawn=1) unless it yields a clear forced win.
        7. Do not leave pieces "en prise" (undefended and capturable) on your turn.
        8. In the opening, prioritize rapid development (knights before bishops), control of the four central squares (e4, d4, e5, d5), and early castling for king safety.
        9. In the middlegame, coordinate your pieces and create threats; calculate at least 3 ply (your move, opponent reply, your follow-up) before deciding.
        10. In the endgame, activate the king and advance passed pawns.
        11. Prefer moves that improve the evaluation according to standard piece values and positional considerations.
        12. Only consider queen sacrifices if they lead to checkmate or decisive material/positional gain confirmed in your calculation.
        13. Provide a concise explanation (in Portuguese, max 2 sentences) outlining the tactical/strategic idea behind the move.
         
        Respond with your move in the required format.
        """

        return context

    def _get_material_balance(self, board: chess.Board) -> str:
        """Get material balance information"""
        piece_values = {
            chess.PAWN: 1,
            chess.KNIGHT: 3,
            chess.BISHOP: 3,
            chess.ROOK: 5,
            chess.QUEEN: 9,
            chess.KING: 0
        }
        
        white_material = 0
        black_material = 0
        
        for square in chess.SQUARES:
            piece = board.piece_at(square)
            if piece:
                value = piece_values[piece.piece_type]
                if piece.color == chess.WHITE:
                    white_material += value
                else:
                    black_material += value
        
        balance = white_material - black_material
        
        if balance > 0:
            return f"White +{balance}"
        elif balance < 0:
            return f"Black +{abs(balance)}"
        else:
            return "Equal"

    def play_game(self, white_model: str, black_model: str, opening: str = "1. e4",
                  max_moves: int = 200, use_fallback: bool = False) -> Dict[str, Any]:
        """
        Play a complete game between two models
        
        Args:
            white_model: Name of the white model
            black_model: Name of the black model
            opening: Opening move
            max_moves: Maximum number of moves
            use_fallback: Whether to use fallback when LLM fails
        """

        # Verifica se os modelos estão funcionando (usando cache)
        if not self.model_manager.is_model_working(white_model):
            return {
                "error": f"Modelo das brancas '{white_model}' não está disponível ou não tem chave válida!",
                "pgn": "",
                "result": "*",
                "moves": 0
            }
        
        if not self.model_manager.is_model_working(black_model):
            return {
                "error": f"Modelo das pretas '{black_model}' não está disponível ou não tem chave válida!",
                "pgn": "",
                "result": "*",
                "moves": 0
            }

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

            print(f"\n🎮 Lance {move_count + 1}: {current_model} ({color})")

            # Get move from current model
            move, explanation = self.get_ai_move(
                board, current_model, last_move=last_move, use_fallback=use_fallback)

            if move:
                san_move = board.san(move)
                board.push(move)
                node = node.add_variation(move)
                last_move = san_move
                move_count += 1

                print(f"✅ Lance: {san_move}")
                if explanation:
                    print(f"💭 Explicação: {explanation}")
            else:
                print(f"❌ ERRO: {current_model} não conseguiu fazer um lance válido!")
                if not use_fallback:
                    print("🛑 Jogo interrompido - modelo LLM falhou!")
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

    def play_game_realtime(self, white_model: str, black_model: str, opening: str = "1. e4", 
                          max_moves: int = 200, ui: UIComponents = None, sleep_time: float = 1.0,
                          use_fallback: bool = False) -> dict:
        """
        Play a game between two models in real-time, showing the board live
        
        Args:
            white_model: Name of the white model
            black_model: Name of the black model
            opening: Opening move
            max_moves: Maximum number of moves
            ui: UI components for display
            sleep_time: Time to wait between moves
            use_fallback: Whether to use fallback when LLM fails
        """
        
        # Verifica se os modelos estão funcionando (usando cache)
        if not self.model_manager.is_model_working(white_model):
            error_msg = f"❌ Modelo das brancas '{white_model}' não está disponível!"
            if 'st' in globals():
                st.error(error_msg)
            return {"error": error_msg, "pgn": "", "result": "*", "moves": 0}
        
        if not self.model_manager.is_model_working(black_model):
            error_msg = f"❌ Modelo das pretas '{black_model}' não está disponível!"
            if 'st' in globals():
                st.error(error_msg)
            return {"error": error_msg, "pgn": "", "result": "*", "moves": 0}
        
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
            move = board.parse_san("e4")
            board.push(move)
            node = node.add_variation(move)

        last_move = opening
        move_count = 0

        # Dynamic board display space
        if 'st' in globals():
            board_placeholder = st.empty()
        
        if ui is None:
            ui = UIComponents()

        # Game loop
        while not board.is_game_over() and move_count < max_moves:
            current_model = black_model if board.turn == chess.BLACK else white_model
            color = "black" if board.turn == chess.BLACK else "white"

            print(f"\n🎮 Lance {move_count + 1}: {current_model} ({color})")

            # Get move from current model
            move, explanation = self.get_ai_move(
                board, current_model, last_move=last_move, use_fallback=use_fallback)

            if move:
                san_move = board.san(move)  # Get SAN before push
                board.push(move)
                node = node.add_variation(move)
                last_move = san_move
                move_count += 1

                print(f"✅ Lance: {san_move}")
                if explanation:
                    print(f"💭 Explicação: {explanation}")

                # Update board display in real-time
                if 'st' in globals() and board_placeholder:
                    with board_placeholder:
                        highlight = [move.from_square, move.to_square]
                        ui.display_board(board, highlight_squares=highlight)
                        
                time.sleep(sleep_time)
            else:
                print(f"❌ ERRO: {current_model} não conseguiu fazer um lance válido!")
                if not use_fallback:
                    print("🛑 Jogo interrompido - modelo LLM falhou!")
                    break

        # Set result
        result = board.result()
        game.headers["Result"] = result

        # Show final board
        if 'st' in globals() and board_placeholder:
            with board_placeholder:
                ui.display_board(board)

        return {
            "pgn": str(game),
            "result": result,
            "moves": move_count,
            "white": white_model,
            "black": black_model,
            "board": board,
            "game": game
        }