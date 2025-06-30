import streamlit as st
import pandas as pd
from datetime import datetime
import os
import chess
import time
import chess.pgn
import io
from src.analysis import GameAnalyzer


def show_battle_arena(model_manager, game_engine, db, ui, start_tournament_func=None, start_individual_battle_func=None):
    st.markdown("## ⚔️ Arena de Batalha")

    col1, col2 = st.columns([1, 2])

    with col1:
        st.markdown("### 🎮 Configuração da Batalha")

        st.markdown("#### 🥊 Batalha Individual")

        white_model = st.selectbox(
            "Modelo das Brancas:",
            list(model_manager.get_available_models().keys()),
            key="white_model"
        )

        black_model = st.selectbox(
            "Modelo das Pretas:",
            list(model_manager.get_available_models().keys()),
            key="black_model"
        )

        opening = st.selectbox(
            "Abertura:",
            ["1. e4", "1. d4", "1. c4", "1. Nf3", "1. b3",
                "1. c3", "1. e3", "1. d3", "1. g3", "1. Nc3"],
            key="opening"
        )

        # Slider para velocidade
        realtime_speed = st.slider(
            "Velocidade dos lances (s)", 0.1, 3.0, 1.0, 0.1, key="realtime_speed")

        # Botão para batalha em tempo real
        if st.button("⚡ Batalha em Tempo Real", type="primary"):
            st.info(
                f"Rodando batalha em tempo real: {white_model} vs {black_model}")
            # Inicializa arena_game se ainda não existir ou se uma nova partida está começando
            if 'arena_game' not in st.session_state or st.session_state.get('reset_game', False):
                st.session_state.arena_game = {
                    'white': white_model,
                    'black': black_model,
                    'opening': opening,
                    'board': chess.Board(),
                    'move_history': [],
                    'pgn_game': chess.pgn.Game(),
                    'current_node': None,
                    'auto_play': True  # Flag to indicate auto-play mode
                }
                st.session_state.reset_game = False
                st.session_state.arena_game['current_node'] = st.session_state.arena_game['pgn_game']
                
                # Configure game headers
                st.session_state.arena_game['pgn_game'].headers["White"] = white_model
                st.session_state.arena_game['pgn_game'].headers["Black"] = black_model
                st.session_state.arena_game['pgn_game'].headers["Date"] = datetime.now().strftime("%Y.%m.%d")
                st.session_state.arena_game['pgn_game'].headers["Event"] = "LLM Chess Arena"
                
                # Play opening move if specified
                if opening and opening != "Custom":
                    opening_move = opening.split()[-1]
                    try:
                        move = st.session_state.arena_game['board'].parse_san(opening_move)
                        st.session_state.arena_game['board'].push(move)
                        node = st.session_state.arena_game['current_node'].add_variation(move)
                        st.session_state.arena_game['current_node'] = node
                        st.session_state.arena_game['move_history'].append({
                            'move': opening_move,
                            'by': 'opening',
                            'from_square': move.from_square,
                            'to_square': move.to_square,
                            'explanation': "Lance de abertura"
                        })
                    except ValueError:
                        st.error(f"Abertura inválida: {opening}")
            else:
                # Ensure auto-play is enabled
                st.session_state.arena_game['auto_play'] = True
            
            # Force rerun to start the auto-play loop
            st.rerun()

    with col2:
        st.markdown("### 🎮 Status da Batalha")

        # Show battle status
        if 'arena_game' in st.session_state:
            game = st.session_state.arena_game
            
            # Game status
            color_to_move = "Brancas" if game['board'].turn == chess.WHITE else "Pretas"
            current_model = game['white'] if color_to_move == "Brancas" else game['black']
            
            st.markdown(f"""
            <div class="game-status status-playing">
                🎮 Batalha em Andamento<br>
                {game['white']} (Brancas) vs {game['black']} (Pretas)<br>
                Vez das {color_to_move}: {current_model}
            </div>
            """, unsafe_allow_html=True)
            
            # Controls for auto-play
            col_pause, col_resume, col_reset, col_save = st.columns(4)
            with col_pause:
                if st.button("⏸️ Pausar") and game.get('auto_play', False):
                    st.session_state.arena_game['auto_play'] = False
                    
            with col_resume:
                if st.button("▶️ Continuar") and not game.get('auto_play', False):
                    st.session_state.arena_game['auto_play'] = True
                    st.rerun()
                    
            with col_reset:
                if st.button("🔄 Nova Partida"):
                    st.session_state.reset_game = True
                    st.rerun()
                    
            with col_save:
                if st.button("💾 Salvar Partida"):
                    save_finished_game(st.session_state.arena_game, db)
            
            # Board
            highlight = []
            if game.get('move_history'):
                last_move = game['move_history'][-1]
                if 'from_square' in last_move and 'to_square' in last_move:
                    highlight = [last_move['from_square'], last_move['to_square']]
            
            ui.display_board(game['board'], key="arena_game_board", highlight_squares=highlight)
            
            # Histórico de movimentos
            st.markdown("### 📝 Histórico de Lances")
            if game['move_history']:
                moves_df = pd.DataFrame(game['move_history'])
                st.dataframe(moves_df, use_container_width=True)
                
                # Mostrar explicação do último lance
                if len(game['move_history']) > 0:
                    last_move = game['move_history'][-1]
                    if 'explanation' in last_move and last_move['explanation']:
                        st.info(f"Explicação do último lance ({last_move['move']}): {last_move['explanation']}")
            
            # Adicionar botão para o próximo lance
            if st.button("▶️ Próximo Lance"):
                st.rerun()  # Força o recarregamento da página para executar a lógica do próximo lance
        
        elif 'current_battle' in st.session_state:
            battle = st.session_state.current_battle

            st.markdown(f"""
            <div class="game-status status-playing">
                🎮 Batalha em Andamento<br>
                {battle['white']} vs {battle['black']}<br>
                Partida {battle['current_game']}/{battle['total_games']}
            </div>
            """, unsafe_allow_html=True)

            # Show current board
            if 'current_board' in st.session_state:
                ui.display_board(
                    st.session_state.current_board, key="battle_board")

            # Progress bar
            progress = battle['current_game'] / battle['total_games']
            st.progress(progress)

            # Results so far
            if battle['results']:
                st.markdown("#### 📊 Resultados Parciais")
                results_df = pd.DataFrame(battle['results'])
                st.dataframe(results_df, use_container_width=True)

        else:
            st.info(
                "Nenhuma batalha em andamento. Configure uma batalha na coluna à esquerda.")

        # Joga um lance de cada vez
        if 'arena_game' in st.session_state and not st.session_state.arena_game['board'].is_game_over():
            # Check if we're in auto-play mode
            if st.session_state.arena_game.get('auto_play', False):
                # Determine which model plays now
                current_model = black_model if st.session_state.arena_game['board'].turn == chess.BLACK else white_model
                color = "black" if st.session_state.arena_game['board'].turn == chess.BLACK else "white"
                
                # Get move from LLM
                move, explanation = game_engine.get_ai_move(
                    st.session_state.arena_game['board'], 
                    current_model
                )
                
                if move:
                    from_square = move.from_square
                    to_square = move.to_square
                    move_san = st.session_state.arena_game['board'].san(move)  # Get SAN before making the move
                    st.session_state.arena_game['board'].push(move)
                    
                    # Update PGN
                    node = st.session_state.arena_game['current_node'].add_variation(move)
                    if explanation:
                        node.comment = explanation
                    st.session_state.arena_game['current_node'] = node
                    
                    # Save to history
                    st.session_state.arena_game['move_history'].append({
                        'move': move_san,
                        'by': current_model,
                        'from_square': from_square,
                        'to_square': to_square,
                        'explanation': explanation
                    })
                    
                    # Logic for check and checkmate detection
                    if st.session_state.arena_game['board'].is_check():
                        check_color = "Brancas" if st.session_state.arena_game['board'].turn == chess.BLACK else "Pretas"
                        st.session_state.arena_game['move_history'][-1]['explanation'] += f" (Xeque para as {check_color})"
                    
                    if st.session_state.arena_game['board'].is_checkmate():
                        winner = "Brancas" if st.session_state.arena_game['board'].turn == chess.BLACK else "Pretas"
                        st.session_state.arena_game['move_history'][-1]['explanation'] += f" (Xeque-mate! {winner} venceu)"
                        st.session_state.arena_game['auto_play'] = False
                        
                        # Auto-save game when it ends by checkmate
                        save_finished_game(st.session_state.arena_game, db)
                    
                    # Also check for other game ending conditions
                    elif st.session_state.arena_game['board'].is_stalemate() or st.session_state.arena_game['board'].is_insufficient_material() or st.session_state.arena_game['board'].is_fifty_moves():
                        end_reason = "empate por afogamento" if st.session_state.arena_game['board'].is_stalemate() else \
                                     "empate por material insuficiente" if st.session_state.arena_game['board'].is_insufficient_material() else \
                                     "empate pela regra dos 50 movimentos"
                        st.session_state.arena_game['move_history'][-1]['explanation'] += f" (Fim de jogo: {end_reason})"
                        st.session_state.arena_game['auto_play'] = False
                        
                        # Auto-save game when it ends by draw
                        save_finished_game(st.session_state.arena_game, db)
                    
                    # Wait for the configured time
                    time.sleep(realtime_speed)
                    st.rerun()  # Update the page for the next move
                else:
                    st.error(f"Model {current_model} couldn't generate a valid move.")


def save_finished_game(game, db):
    """Save the finished game to a PGN file and database"""
    try:
        # Set the result in the PGN
        result = game['board'].result()
        analyzer = GameAnalyzer()
        opening_name = analyzer._get_opening_name(game['pgn_game'])

        # Create folder if it doesn't exist
        folder_name = f"{game['white']} vs {game['black']}"
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
        game['pgn_game'].headers["Opening"] = opening_name
        game['pgn_game'].headers["White"] = game['white']
        game['pgn_game'].headers["Black"] = game['black']
        game['pgn_game'].headers["Result"] = result
        
        # Save to PGN file with the format: {game_num}_game.pgn
        pgn_path = f"{folder_name}/{game_num}_game.pgn"
        with open(pgn_path, "w", encoding="utf-8") as f:
            f.write(str(game['pgn_game']))
        
        # Also save move history as CSV with the format: {game_num}_moves.csv
        moves_df = pd.DataFrame(game['move_history'])
        csv_path = f"{folder_name}/{game_num}_moves.csv"
        moves_df.to_csv(csv_path, index=True)
        
        # Save to database if db is available
        if db:
            game_data = {
                'white': game['white'],
                'black': game['black'],
                'result': result,
                'pgn': str(game['pgn_game']),
                'moves': len(game['move_history']),
                'opening': game.get('opening', ''),
                'date': datetime.now().isoformat(),  # Use ISO format for database
                'analysis': {},
                'round': game_num  # Also include round in database
            }
            db.save_game(game_data)
        
        st.success(f"✅ Partida salva em {pgn_path}!")
        
        # Also provide download links with appropriate names
        pgn_str = str(game['pgn_game'])
        st.download_button(
            label="📥 Baixar PGN",
            data=pgn_str,
            file_name=f"{game_num}_game.pgn",
            mime="text/plain"
        )
        
        csv_str = moves_df.to_csv(index=True)
        st.download_button(
            label="📥 Baixar CSV dos Movimentos",
            data=csv_str,
            file_name=f"{game_num}_moves.csv",
            mime="text/csv"
        )
        
        return True
    except Exception as e:
        st.error(f"Erro ao salvar a partida: {str(e)}")
        return False
