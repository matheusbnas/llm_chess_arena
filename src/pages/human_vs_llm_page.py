import streamlit as st
import pandas as pd
import chess


def show_human_vs_llm(model_manager, game_engine, ui):
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

        if st.button("🎮 Novo Jogo", type="primary"):
            from src.human_game_utils import initialize_human_game
            initialize_human_game(
                opponent_model, player_color, difficulty, time_control)

        # Game controls
        if 'human_game' in st.session_state:
            st.markdown("### 🎮 Controles do Jogo")

            if st.button("🔄 Reiniciar"):
                del st.session_state.human_game
                st.rerun()

            if st.button("💾 Salvar Partida"):
                from src.human_game_utils import save_human_game
                save_human_game()

            if st.button("🤖 Dica da IA"):
                from src.human_game_utils import show_ai_hint
                show_ai_hint()

    with col2:
        if 'human_game' in st.session_state:
            game = st.session_state.human_game

            # Game status
            st.markdown(f"""
            <div class="game-status status-playing">
                🎮 Jogando contra {game['opponent']}<br>
                Você: {game['player_color']} | Dificuldade: {game['difficulty']}
            </div>
            """, unsafe_allow_html=True)

            # Board
            highlight = []
            if game.get('move_history'):
                last_move = game['move_history'][-1]
                if 'from_square' in last_move and 'to_square' in last_move:
                    highlight = [last_move['from_square'],
                                 last_move['to_square']]
            ui.display_board(
                game['board'], key="human_game_board", highlight_squares=highlight)

            # Move input
            if game['board'].turn == (chess.WHITE if game['player_color'] == "Brancas" else chess.BLACK):
                st.markdown("### 🎯 Seu Lance")

                col_move1, col_move2 = st.columns(2)

                with col_move1:
                    move_input = st.text_input(
                        "Digite seu lance (ex: e4, Nf3):",
                        key="move_input"
                    )
                    human_explanation = st.text_area(
                        "Explique seu lance (opcional):",
                        key="human_explanation"
                    )

                with col_move2:
                    if st.button("▶️ Jogar Lance"):
                        if move_input:
                            from src.human_game_utils import make_human_move
                            make_human_move(move_input, human_explanation)
                            if human_explanation:
                                st.info(f"Sua explicação: {human_explanation}")

            else:
                st.markdown("### 🤖 IA está pensando...")
                if st.button("⏭️ Processar Lance da IA"):
                    from src.human_game_utils import make_ai_move
                    explanation = make_ai_move(
                        game['opponent'], model_manager, game_engine)
                    if explanation:
                        st.info(f"Explicação da LLM: {explanation}")

            # Move history
            st.markdown("### 📝 Histórico de Lances")
            if game['move_history']:
                moves_df = pd.DataFrame(game['move_history'])
                st.dataframe(moves_df, use_container_width=True)

        else:
            st.info("Configure um novo jogo na coluna à esquerda para começar!")
