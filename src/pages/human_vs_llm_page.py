import streamlit as st
import pandas as pd
import chess
import os
from datetime import datetime
import time
from src.analysis import GameAnalyzer
from src.models import ModelManager
from src.ui_components import UIComponents

# Global UI instance for board rendering
ui = UIComponents()

def show_human_vs_llm(model_manager, db, game_engine):
    st.markdown("## Arena de LLMs em Xadrez")
    
    # Cria uma instância do ModelManager em modo de confiança
    model_manager = ModelManager(api_keys=model_manager.api_keys, trust_cached=True)
    
    col1, col2 = st.columns([1, 2])

    with col1:
        st.markdown("### 🎮 Configuração do Jogo")

        # Obter apenas modelos que realmente funcionam
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
                capabilities = model_manager._get_capabilities(model_name)
                st.write(f"• **{model_name}** ({provider} - {pricing})")
                if capabilities:
                    st.write(f"  💡 Capacidades: {', '.join(capabilities)}")

        # Model selection
        opponent_model = st.selectbox(
            "Escolha seu oponente:",
            list(working_models.keys()),
            key="opponent_model",
            help="Apenas modelos com chaves válidas são mostrados"
        )

        # Mostrar informações do modelo selecionado
        if opponent_model:
            model_info = model_manager.get_model_info(opponent_model)
            st.info(f"🤖 **{opponent_model}** - {model_info.get('provider', 'N/A')} ({model_info.get('pricing_tier', 'N/A')} cost)")

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
        auto_ai_moves = st.checkbox(
            "Jogadas automáticas da IA", 
            value=True,  # Mudei para True por padrão
            help="A IA fará jogadas automaticamente após sua jogada"
        )
        
        # Auto-move speed if auto-play is enabled
        ai_move_speed = 1.0
        if auto_ai_moves:
            ai_move_speed = st.slider(
                "Velocidade da jogada da IA (s)", 0.5, 3.0, 1.0, 0.1
            )

        # Opção para usar fallback
        use_fallback = st.checkbox(
            "Usar fallback se IA falhar",
            value=False,
            help="Se a IA falhar, usar lance aleatório em vez de parar o jogo"
        )

        if st.button("🎮 Novo Jogo", type="primary"):
            # Verificar se o modelo ainda está funcionando (usando cache)
            if not model_manager.is_model_working(opponent_model):
                st.error(f"❌ Modelo '{opponent_model}' não está mais disponível!")
                return
                
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
                'use_fallback': use_fallback,
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
            
            st.success(f"🎮 Novo jogo iniciado contra **{opponent_model}**!")
            
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

            # Verificar se o modelo ainda está funcionando (usando cache)
            if not model_manager.is_model_working(game['opponent']):
                st.error(f"❌ Modelo '{game['opponent']}' não está mais disponível!")
                st.info("💡 Vá em Configurações > Modelos e clique em 'Re-testar Modelos' se necessário.")
                if st.button("🔄 Reiniciar Jogo"):
                    del st.session_state.human_game
                    st.rerun()
                return

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
                🎮 Jogando contra <strong>{game['opponent']}</strong><br>
                Você: {game['player_color']} | Dificuldade: {game['difficulty']}
                {f"<br><strong>{result_text}</strong>" if result_text else ""}
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
                    st.info(f"💭 Sua explicação: {last_move['explanation']}")
                elif last_move['by'] == 'llm' and last_move.get('explanation'):
                    if last_move['explanation'].startswith("(⚠️ FALLBACK"):
                        st.warning(f"⚠️ {last_move['explanation']}")
                    else:
                        st.success(f"🤖 Explicação da IA: {last_move['explanation']}")
            
            # Input options for player's move
            if is_player_turn and not game['board'].is_game_over():
                # Tabuleiro interativo: captura SAN diretamente
                san = ui.display_click_board(game['board'])
                # `display_click_board` returns a value only after the user makes a move.
                # It may initially be a Streamlit `DeltaGenerator`, which does **not** support
                # string methods like `strip()`.  Guard against this by ensuring we only
                # process the value when it is actually a string.
                if isinstance(san, str) and san:
                    player_move_san = san.strip()
                    st.session_state.human_game['player_move_input'] = player_move_san
                
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
                            if make_human_move(game, move_input, human_explanation):
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
                    st.success(f"🏆 Xeque-mate! {winner} venceu!")
                elif game['board'].is_stalemate():
                    st.info("🤝 Empate por afogamento!")
                elif game['board'].is_insufficient_material():
                    st.info("🤝 Empate por material insuficiente!")
                elif game['board'].is_fifty_moves():
                    st.info("🤝 Empate pela regra dos 50 movimentos!")

            # Move history
            st.markdown("### 📝 Histórico de Lances")
            if game['move_history']:
                moves_df = pd.DataFrame(game['move_history'])
                st.dataframe(moves_df[['move', 'by', 'explanation']], use_container_width=True)

        else:
            st.info("🎯 Configure um novo jogo na coluna à esquerda para começar!")


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
        st.error(f"❌ Lance inválido: {e}")
        return False


def make_ai_move(game, model_manager, game_engine):
    """Make an AI move in the game"""
    board = game['board']
    model_name = game['opponent']
    
    # Verificar se o modelo ainda está funcionando (usando cache)
    if not model_manager.is_model_working(model_name):
        st.error(f"❌ Modelo '{model_name}' não está mais disponível!")
        return False
    
    # Get move from game engine with explicit fallback control
    use_fallback = game.get('use_fallback', False)
    move, explanation = game_engine.get_ai_move(board, model_name, use_fallback=use_fallback)
    
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
        # AI failed to make a move
        error_explanation = f"❌ A IA falhou em gerar um lance válido. {explanation}"
        st.error(error_explanation)
        
        # Add error to move history
        game['move_history'].append({
            'move': 'ERRO',
            'by': 'llm',
            'from_square': None,
            'to_square': None,
            'explanation': error_explanation
        })
        
        return False


def save_finished_game(game, db=None):
    """Save the finished game to a PGN file and database"""
    try:
        result = game['board'].result()
        analyzer = GameAnalyzer()
        opening_name = analyzer._get_opening_name(game['pgn_game'])

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
        game['pgn_game'].headers["Round"] = str(game_num)
        game['pgn_game'].headers["Opening"] = opening_name
        game['pgn_game'].headers["White"] = "Humano" if game['player_color'] == "Brancas" else game['opponent']
        game['pgn_game'].headers["Black"] = game['opponent'] if game['player_color'] == "Brancas" else "Humano"
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
                'white': "Humano" if game['player_color'] == "Brancas" else game['opponent'],
                'black': game['opponent'] if game['player_color'] == "Brancas" else "Humano",
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
        st.error(f"❌ Erro ao salvar a partida: {str(e)}")
        return False