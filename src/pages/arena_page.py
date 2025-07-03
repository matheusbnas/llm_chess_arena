import streamlit as st
import pandas as pd
from datetime import datetime
import os
import chess
import time
import chess.pgn
import io
from src.analysis import GameAnalyzer
from src.models import ModelManager

def show_battle_arena(model_manager, game_engine, db, ui, start_tournament_func=None, start_individual_battle_func=None):
    st.markdown("## ⚔️ Arena de Batalha")
    
    # Cria uma instância do ModelManager em modo de confiança
    model_manager = ModelManager(api_keys=model_manager.api_keys, trust_cached=True)
    
    col1, col2 = st.columns([1, 2])

    with col1:
        st.markdown("### 🎮 Configuração da Batalha")

        # Obter modelos disponíveis (em modo de confiança)
        working_models = model_manager.get_working_models_only()
        
        if not working_models:
            st.error("❌ Nenhum modelo disponível! Verifique suas chaves de API em Configurações.")
            return

        st.success(f"✅ {len(working_models)} modelo(s) disponível(eis)")
        
        # Mostrar quais modelos estão funcionando
        with st.expander("🔍 Modelos Funcionais Detectados"):
            for model_name in working_models:
                provider = model_manager._get_provider(model_name)
                pricing = model_manager._get_pricing_tier(model_name)
                st.write(f"• **{model_name}** ({provider} - {pricing})")

        st.markdown("#### 🥊 Batalha Individual")

        white_model = st.selectbox(
            "Modelo das Brancas:",
            list(working_models.keys()),
            key="white_model",
            help="Apenas modelos com chaves válidas são mostrados"
        )

        black_model = st.selectbox(
            "Modelo das Pretas:",
            list(working_models.keys()),
            key="black_model",
            help="Apenas modelos com chaves válidas são mostrados"
        )

        # Verificar se os modelos selecionados são diferentes
        if white_model == black_model:
            st.warning("⚠️ Você selecionou o mesmo modelo para ambos os lados. Isso é permitido, mas pode ser menos interessante.")

        opening = st.selectbox(
            "Abertura:",
            ["1. e4", "1. d4", "1. c4", "1. Nf3", "1. b3",
                "1. c3", "1. e3", "1. d3", "1. g3", "1. Nc3"],
            key="opening"
        )

        # Slider para velocidade
        realtime_speed = st.slider(
            "Velocidade dos lances (s)", 0.1, 3.0, 1.0, 0.1, 
            key="realtime_speed",
            help="Tempo entre cada lance na batalha em tempo real"
        )

        # Opção para usar fallback
        use_fallback = st.checkbox(
            "Usar fallback em caso de erro",
            value=False,
            help="Se um modelo falhar, usar lance aleatório em vez de parar o jogo"
        )

        # Botão para batalha em tempo real
        if st.button("⚡ Batalha em Tempo Real", type="primary"):
            # Verificar se os modelos ainda estão funcionando (usando cache)
            if not model_manager.is_model_working(white_model):
                st.error(f"❌ Modelo das brancas '{white_model}' não está mais disponível!")
                return
            if not model_manager.is_model_working(black_model):
                st.error(f"❌ Modelo das pretas '{black_model}' não está mais disponível!")
                return
                
            st.info(f"🎮 Iniciando batalha: **{white_model}** vs **{black_model}**")
            
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
                    'auto_play': True,  # Flag to indicate auto-play mode
                    'use_fallback': use_fallback,
                    'realtime_speed': realtime_speed
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
                st.session_state.arena_game['use_fallback'] = use_fallback
                st.session_state.arena_game['realtime_speed'] = realtime_speed
            
            # Force rerun to start the auto-play loop
            st.rerun()

    with col2:
        st.markdown("### 🎮 Status da Batalha")

        # Show battle status
        if 'arena_game' in st.session_state:
            game = st.session_state.arena_game
            
            # Verificar se os modelos ainda estão funcionando
            current_working = model_manager.get_working_models_only()
            if game['white'] not in current_working or game['black'] not in current_working:
                st.error("❌ Um ou ambos os modelos não estão mais disponíveis. Reinicie a batalha.")
                if st.button("🔄 Reiniciar"):
                    st.session_state.reset_game = True
                    st.rerun()
                return
            
            # Game status
            color_to_move = "Brancas" if game['board'].turn == chess.WHITE else "Pretas"
            current_model = game['white'] if color_to_move == "Brancas" else game['black']
            
            # Verificar se o jogo terminou
            is_game_over = game['board'].is_game_over()
            
            if is_game_over:
                result = game['board'].result()
                if result == "1-0":
                    winner = f"{game['white']} (Brancas)"
                elif result == "0-1":
                    winner = f"{game['black']} (Pretas)"
                else:
                    winner = "Empate"
                
                st.markdown(f"""
                <div class="game-status status-finished">
                    🏆 Batalha Finalizada!<br>
                    {game['white']} (Brancas) vs {game['black']} (Pretas)<br>
                    <strong>Resultado: {winner}</strong>
                </div>
                """, unsafe_allow_html=True)
            else:
                st.markdown(f"""
                <div class="game-status status-playing">
                    🎮 Batalha em Andamento<br>
                    {game['white']} (Brancas) vs {game['black']} (Pretas)<br>
                    Vez das {color_to_move}: <strong>{current_model}</strong>
                </div>
                """, unsafe_allow_html=True)
            
            # Controls for auto-play
            col_pause, col_resume, col_reset, col_save = st.columns(4)
            with col_pause:
                if st.button("⏸️ Pausar") and game.get('auto_play', False):
                    st.session_state.arena_game['auto_play'] = False
                    st.success("⏸️ Jogo pausado")
                    
            with col_resume:
                if st.button("▶️ Continuar") and not game.get('auto_play', False) and not is_game_over:
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
                        if last_move['explanation'].startswith("(⚠️ FALLBACK"):
                            st.warning(f"⚠️ {last_move['explanation']}")
                        else:
                            st.info(f"💭 Explicação do último lance ({last_move['move']}): {last_move['explanation']}")
            
            # Próximo lance (apenas se não terminou)
            if not is_game_over and not game.get('auto_play', False):
                if st.button("▶️ Próximo Lance"):
                    st.rerun()
        
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
            st.info("🎯 Nenhuma batalha em andamento. Configure uma batalha na coluna à esquerda.")

        # Joga um lance de cada vez (lógica principal do jogo)
        if 'arena_game' in st.session_state and not st.session_state.arena_game['board'].is_game_over():
            # Check if we're in auto-play mode
            if st.session_state.arena_game.get('auto_play', False):
                # Determine which model plays now
                current_model = black_model if st.session_state.arena_game['board'].turn == chess.BLACK else white_model
                color = "black" if st.session_state.arena_game['board'].turn == chess.BLACK else "white"
                
                # Get move from LLM with explicit fallback control
                use_fallback = st.session_state.arena_game.get('use_fallback', False)
                move, explanation = game_engine.get_ai_move(
                    st.session_state.arena_game['board'], 
                    current_model,
                    use_fallback=use_fallback
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
                        check_color = "Brancas" if st.session_state.arena_game['board'].turn == chess.WHITE else "Pretas"
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
                    time.sleep(st.session_state.arena_game.get('realtime_speed', 1.0))
                    st.rerun()  # Update the page for the next move
                else:
                    # Model failed to make a move
                    st.error(f"❌ Modelo {current_model} falhou em fazer um lance!")
                    st.session_state.arena_game['auto_play'] = False
                    
                    # Add error to move history
                    st.session_state.arena_game['move_history'].append({
                        'move': 'ERRO',
                        'by': current_model,
                        'from_square': None,
                        'to_square': None,
                        'explanation': f"❌ Modelo {current_model} falhou em gerar um lance válido. {explanation}"
                    })


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
        game['pgn_game'].headers["Round"] = str(game_num)
        game['pgn_game'].headers["Opening"] = opening_name
        game['pgn_game'].headers["White"] = game['white']
        game['pgn_game'].headers["Black"] = game['black']
        game['pgn_game'].headers["Result"] = result
        
        # Save to PGN file
        pgn_path = f"{folder_name}/{game_num}_game.pgn"
        with open(pgn_path, "w", encoding="utf-8") as f:
            f.write(str(game['pgn_game']))
        
        # Save move history as CSV
        moves_df = pd.DataFrame(game['move_history'])
        csv_path = f"{folder_name}/{game_num}_moves.csv"
        moves_df.to_csv(csv_path, index=True)
        
        # Save to database if available
        if db:
            game_data = {
                'white': game['white'],
                'black': game['black'],
                'result': result,
                'pgn': str(game['pgn_game']),
                'moves': len(game['move_history']),
                'opening': opening_name,
                'date': datetime.now().isoformat(),
                'analysis': {},
                'round': game_num
            }
            db.save_game(game_data)
        
        st.success(f"✅ Partida salva em {pgn_path}!")
        
        # Download buttons
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
        st.error(f"❌ Erro ao salvar a partida: {str(e)}")
        return False