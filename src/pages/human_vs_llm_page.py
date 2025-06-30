import streamlit as st
import pandas as pd
import chess
import os
from datetime import datetime
import time


def show_human_vs_llm(model_manager, game_engine, ui, db):
    st.markdown("## 🎯 Jogar contra LLM")

    col1, col2 = st.columns([1, 2])

    with col1:
        st.markdown("### 🎮 Configuração do Jogo")

        # Model selection
        opponent_model = st.selectbox(
            "Escolha seu oponente:",
            list(model_manager.get_available_models().keys()),
            key="opponent_model"
        )

        # Color selection
        player_color = st.radio(
            "Escolha sua cor:",
            ["Brancas", "Pretas"],
            key="player_color"
        )

        # Difficulty level
        difficulty = st.selectbox(
            "Nível de dificuldade:",
            ["Iniciante", "Intermediário", "Avançado", "Mestre"],
            key="difficulty"
        )

        # Time control
        time_control = st.selectbox(
            "Controle de tempo:",
            ["Sem limite", "5 min", "10 min", "15 min", "30 min"],
            key="time_control"
        )

        # Auto-play option for AI
        auto_ai_moves = st.checkbox("Jogadas automáticas da IA", value=False, 
                                   help="A IA fará jogadas automaticamente após sua jogada")
        
        # Auto-move speed if auto-play is enabled
        ai_move_speed = 1.0
        if auto_ai_moves:
            ai_move_speed = st.slider(
                "Velocidade da jogada da IA (s)", 0.5, 3.0, 1.0, 0.1
            )

        if st.button("🎮 Novo Jogo", type="primary"):
            # Initialize human game
            st.session_state.human_game = {
                'opponent': opponent_model,
                'player_color': player_color,
                'difficulty': difficulty,
                'time_control': time_control,
                'board': chess.Board(),
                'move_history': [],
                'pgn_game': chess.pgn.Game(),
                'current_node': None,
                'auto_ai_moves': auto_ai_moves,
                'ai_move_speed': ai_move_speed,
                'selected_square': None,
                'legal_moves_for_selected': []
            }
            st.session_state.human_game['current_node'] = st.session_state.human_game['pgn_game']
            
            # Configure initial PGN headers
            st.session_state.human_game['pgn_game'].headers["Event"] = "LLM Chess Arena"
            st.session_state.human_game['pgn_game'].headers["Site"] = "LLM Chess Arena"
            st.session_state.human_game['pgn_game'].headers["Date"] = datetime.now().strftime("%Y.%m.%d")
            st.session_state.human_game['pgn_game'].headers["White"] = "Humano" if player_color == "Brancas" else opponent_model
            st.session_state.human_game['pgn_game'].headers["Black"] = opponent_model if player_color == "Brancas" else "Humano"
            
            # Start with AI move if player chose black
            if player_color == "Pretas" and auto_ai_moves:
                st.rerun()

        # Game controls
        if 'human_game' in st.session_state:
            st.markdown("### 🎮 Controles do Jogo")

            col_ctrl1, col_ctrl2 = st.columns(2)
            
            with col_ctrl1:
                if st.button("🔄 Reiniciar"):
                    del st.session_state.human_game
                    st.rerun()
            
            with col_ctrl2:
                if st.button("💾 Salvar Partida"):
                    save_finished_game(st.session_state.human_game, db)

    with col2:
        if 'human_game' in st.session_state:
            game = st.session_state.human_game

            # Game status
            result_text = ""
            if game['board'].is_checkmate():
                winner = "Você" if (game['board'].turn == chess.BLACK and game['player_color'] == "Brancas") or \
                                   (game['board'].turn == chess.WHITE and game['player_color'] == "Pretas") else game['opponent']
                result_text = f"🏆 Xeque-mate! {winner} venceu!"
            elif game['board'].is_stalemate():
                result_text = "🤝 Empate por afogamento!"
            elif game['board'].is_insufficient_material():
                result_text = "🤝 Empate por material insuficiente!"
            elif game['board'].is_fifty_moves():
                result_text = "🤝 Empate pela regra dos 50 movimentos!"
            
            status_class = "status-finished" if result_text else "status-playing"
            
            st.markdown(f"""
            <div class="game-status {status_class}">
                🎮 Jogando contra {game['opponent']}<br>
                Você: {game['player_color']} | Dificuldade: {game['difficulty']}
                {f"<br>{result_text}" if result_text else ""}
            </div>
            """, unsafe_allow_html=True)

            # Highlight squares based on last move and selected square
            highlight_squares = []
            if game.get('move_history'):
                last_move = game['move_history'][-1]
                if 'from_square' in last_move and 'to_square' in last_move:
                    highlight_squares = [last_move['from_square'], last_move['to_square']]
            
            # Add highlighting for selected square and legal moves
            if game.get('selected_square') is not None:
                if game['selected_square'] not in highlight_squares:
                    highlight_squares.append(game['selected_square'])
                highlight_squares.extend(game['legal_moves_for_selected'])
            
            # Display the board
            flipped = game['player_color'] == "Pretas"
            ui.display_board(
                game['board'], 
                flipped=flipped,
                key="human_game_board", 
                highlight_squares=highlight_squares
            )
            
            # Show whose turn it is
            is_player_turn = game['board'].turn == (chess.WHITE if game['player_color'] == "Brancas" else chess.BLACK)
            turn_text = "### 🎯 Seu Lance" if is_player_turn else "### 🤖 Vez da IA"
            st.markdown(turn_text)

            # Display the last explanation if available
            if game.get('move_history') and len(game['move_history']) > 0:
                last_move = game['move_history'][-1]
                if last_move['by'] == 'human' and last_move.get('explanation'):
                    st.info(f"Sua explicação: {last_move['explanation']}")
                elif last_move['by'] == 'llm' and last_move.get('explanation'):
                    st.success(f"Explicação da IA: {last_move['explanation']}")
            
            # Input options for player's move
            if is_player_turn and not game['board'].is_game_over():
                # Handle square selection for interactive board
                if st.button("🔍 Selecionar Peça no Tabuleiro"):
                    # Show squares to select
                    piece_squares = []
                    for square in chess.SQUARES:
                        piece = game['board'].piece_at(square)
                        if piece and piece.color == game['board'].turn:
                            piece_squares.append(square)
                    
                    # Create a grid of buttons for piece selection
                    if piece_squares:
                        st.markdown("#### Selecione uma peça:")
                        cols = st.columns(min(8, len(piece_squares)))
                        for i, square in enumerate(piece_squares):
                            piece = game['board'].piece_at(square)
                            square_name = chess.square_name(square)
                            col_idx = i % len(cols)
                            with cols[col_idx]:
                                if st.button(f"{piece.symbol()} {square_name}", key=f"select_{square_name}"):
                                    st.session_state.human_game['selected_square'] = square
                                    # Get legal moves for this piece
                                    legal_moves = []
                                    for move in game['board'].legal_moves:
                                        if move.from_square == square:
                                            legal_moves.append(move.to_square)
                                    st.session_state.human_game['legal_moves_for_selected'] = legal_moves
                                    st.rerun()
                
                # If a square is selected, show possible destination squares
                if game.get('selected_square') is not None:
                    st.markdown("#### Mover para:")
                    cols = st.columns(min(8, len(game['legal_moves_for_selected'])))
                    for i, to_square in enumerate(game['legal_moves_for_selected']):
                        square_name = chess.square_name(to_square)
                        col_idx = i % len(cols)
                        with cols[col_idx]:
                            if st.button(f"{square_name}", key=f"move_to_{square_name}"):
                                # Create the move
                                move = chess.Move(game['selected_square'], to_square)
                                
                                # Check if it's a promotion
                                if game['board'].piece_at(game['selected_square']).piece_type == chess.PAWN:
                                    if (to_square >= 56 and game['board'].turn == chess.WHITE) or \
                                       (to_square <= 7 and game['board'].turn == chess.BLACK):
                                        # It's a promotion, ask for piece
                                        pieces = {
                                            "Dama": chess.QUEEN,
                                            "Torre": chess.ROOK,
                                            "Bispo": chess.BISHOP,
                                            "Cavalo": chess.KNIGHT
                                        }
                                        promotion = st.radio("Promover para:", list(pieces.keys()))
                                        move.promotion = pieces[promotion]
                                
                                # Ask for an explanation
                                human_explanation = st.text_area(
                                    "Explique seu lance (opcional):",
                                    key="human_explanation_interactive"
                                )
                                
                                if st.button("Confirmar Movimento"):
                                    # Make the move
                                    from_square = game['selected_square']
                                    to_square = to_square
                                    san_move = game['board'].san(move)
                                    
                                    # Push the move to the board
                                    game['board'].push(move)
                                    
                                    # Update PGN
                                    node = game['current_node'].add_variation(move)
                                    if human_explanation:
                                        node.comment = human_explanation
                                    game['current_node'] = node
                                    
                                    # Save to history
                                    game['move_history'].append({
                                        'move': san_move,
                                        'by': 'human',
                                        'from_square': from_square,
                                        'to_square': to_square,
                                        'explanation': human_explanation
                                    })
                                    
                                    # Reset selected square
                                    game['selected_square'] = None
                                    game['legal_moves_for_selected'] = []
                                    
                                    # Check for checkmate or draw
                                    if game['board'].is_game_over():
                                        save_finished_game(game, db)
                                    # Trigger AI move if auto-play is enabled
                                    elif game.get('auto_ai_moves', False):
                                        # Wait for the specified time before AI moves
                                        time.sleep(game.get('ai_move_speed', 1.0))
                                        make_ai_move(game, model_manager, game_engine)
                                        
                                        # Check for game over after AI move
                                        if game['board'].is_game_over():
                                            save_finished_game(game, db)
                                    
                                    st.rerun()
                
                # Text input for move as an alternative
                st.markdown("#### Ou digite seu lance:")
                col_text1, col_text2 = st.columns([3, 1])
                
                with col_text1:
                    move_input = st.text_input(
                        "Digite seu lance (ex: e4, Nf3):",
                        key="move_input"
                    )
                    human_explanation = st.text_area(
                        "Explique seu lance (opcional):",
                        key="human_explanation"
                    )

                with col_text2:
                    if st.button("▶️ Jogar Lance"):
                        if move_input:
                            make_human_move(game, move_input, human_explanation)
                            
                            # Check for checkmate or draw
                            if game['board'].is_game_over():
                                save_finished_game(game, db)
                            # Trigger AI move if auto-play is enabled
                            elif game.get('auto_ai_moves', False):
                                # Wait for the specified time before AI moves
                                time.sleep(game.get('ai_move_speed', 1.0))
                                make_ai_move(game, model_manager, game_engine)
                                
                                # Check for game over after AI move
                                if game['board'].is_game_over():
                                    save_finished_game(game, db)
                            
                            st.rerun()
            
            # AI move processing
            elif not is_player_turn and not game['board'].is_game_over():
                if game.get('auto_ai_moves', False):
                    make_ai_move(game, model_manager, game_engine)
                    
                    # Check for game over after AI move
                    if game['board'].is_game_over():
                        save_finished_game(game, db)
                    
                    st.rerun()
                else:
                    if st.button("⏭️ Processar Lance da IA", type="primary"):
                        make_ai_move(game, model_manager, game_engine)
                        
                        # Check for game over after AI move
                        if game['board'].is_game_over():
                            save_finished_game(game, db)
                        
                        st.rerun()
            
            # Game over display
            if game['board'].is_game_over():
                st.markdown("### 🏁 Jogo Finalizado")
                result = game['board'].result()
                
                if game['board'].is_checkmate():
                    winner = "Você" if (game['board'].turn == chess.BLACK and game['player_color'] == "Brancas") or \
                                     (game['board'].turn == chess.WHITE and game['player_color'] == "Pretas") else game['opponent']
                    st.success(f"Xeque-mate! {winner} venceu!")
                elif game['board'].is_stalemate():
                    st.info("Empate por afogamento!")
                elif game['board'].is_insufficient_material():
                    st.info("Empate por material insuficiente!")
                elif game['board'].is_fifty_moves():
                    st.info("Empate pela regra dos 50 movimentos!")

            # Move history
            st.markdown("### 📝 Histórico de Lances")
            if game['move_history']:
                moves_df = pd.DataFrame(game['move_history'])
                st.dataframe(moves_df[['move', 'by', 'explanation']], use_container_width=True)

        else:
            st.info("Configure um novo jogo na coluna à esquerda para começar!")


def make_human_move(game, move_input, human_explanation=None):
    """Make a human move in the game"""
    board = game['board']
    try:
        move = board.parse_san(move_input)
        from_square = move.from_square
        to_square = move.to_square
        board.push(move)
        # Atualiza PGN
        node = game['current_node'].add_variation(move)
        if human_explanation:
            node.comment = human_explanation
        game['current_node'] = node
        # Salva histórico
        game['move_history'].append({
            'move': move_input,
            'by': 'human',
            'from_square': from_square,
            'to_square': to_square,
            'explanation': human_explanation
        })
        return True
    except Exception as e:
        st.error(f"Lance inválido: {e}")
        return False


def make_ai_move(game, model_manager, game_engine):
    """Make an AI move in the game"""
    board = game['board']
    color = 'white' if (game['player_color'] == 'Pretas') else 'black'
    model_name = game['opponent']
    
    # Get move from game engine
    move, explanation = game_engine.get_ai_move(board, model_name)
    
    if move:
        from_square = move.from_square
        to_square = move.to_square
        move_san = board.san(move)  # Get SAN before pushing the move
        board.push(move)
        
        # Update PGN
        node = game['current_node'].add_variation(move)
        node.comment = explanation
        game['current_node'] = node
        
        # Save to history
        game['move_history'].append({
            'move': move_san,
            'by': 'llm',
            'from_square': from_square,
            'to_square': to_square,
            'explanation': explanation
        })
        
        # Logic for check and checkmate detection
        if board.is_check():
            check_color = "Brancas" if board.turn == chess.WHITE else "Pretas"
            game['move_history'][-1]['explanation'] += f" (Xeque para as {check_color})"
        
        return True
    else:
        st.error("A IA não conseguiu gerar um lance válido.")
        return False


def save_finished_game(game, db=None):
    """Save the finished game to a PGN file and database"""
    try:
        # Set the result in the PGN
        result = game['board'].result()
        
        # Create folder if it doesn't exist
        folder_name = f"Human_vs_{game['opponent']}"
        if not os.path.exists(folder_name):
            os.makedirs(folder_name)
        
        # Count existing games to determine the next game number
        game_num = len([f for f in os.listdir(folder_name) if f.endswith('.pgn')]) + 1
        
        # Ensure all required PGN headers are set
        current_date = datetime.now().strftime("%Y.%m.%d")
        game['pgn_game'].headers["Event"] = "LLM Chess Arena"
        game['pgn_game'].headers["Site"] = "LLM Chess Arena"
        game['pgn_game'].headers["Date"] = current_date
        game['pgn_game'].headers["Round"] = str(game_num)  # Set Round based on game number
        game['pgn_game'].headers["White"] = "Humano" if game['player_color'] == "Brancas" else game['opponent']
        game['pgn_game'].headers["Black"] = game['opponent'] if game['player_color'] == "Brancas" else "Humano"
        game['pgn_game'].headers["Result"] = result
        
        # Save to PGN file with the format: {game_num}_game.pgn
        pgn_path = f"{folder_name}/{game_num}_game.pgn"
        with open(pgn_path, "w", encoding="utf-8") as f:
            f.write(str(game['pgn_game']))
        
        # Also save move history as CSV 
        moves_df = pd.DataFrame(game['move_history'])
        csv_path = f"{folder_name}/{game_num}_moves.csv"
        moves_df.to_csv(csv_path, index=True)
        
        # Save to database if db is available
        if db:
            game_data = {
                'white': "Humano" if game['player_color'] == "Brancas" else game['opponent'],
                'black': game['opponent'] if game['player_color'] == "Brancas" else "Humano",
                'result': result,
                'pgn': str(game['pgn_game']),
                'moves': len(game['move_history']),
                'opening': game.get('opening', ''),
                'date': datetime.now().isoformat(),
                'tournament_id': None,
                'analysis': {},
                'round': game_num
            }
            db.save_game(game_data)
        
        st.success(f"✅ Partida salva em {pgn_path}!")
        
        # Also provide download links
        pgn_str = str(game['pgn_game'])
        st.download_button(
            label="📥 Baixar PGN",
            data=pgn_str,
            file_name=f"Human_vs_{game['opponent']}_game{game_num}.pgn",
            mime="text/plain"
        )
        
        if not moves_df.empty:
            csv_str = moves_df.to_csv(index=True)
            st.download_button(
                label="📥 Baixar CSV dos Movimentos",
                data=csv_str,
                file_name=f"Human_vs_{game['opponent']}_moves{game_num}.csv",
                mime="text/csv"
            )
        
        return True
    except Exception as e:
        st.error(f"Erro ao salvar a partida: {str(e)}")
        return False
