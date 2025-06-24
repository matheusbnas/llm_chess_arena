import streamlit as st
import pandas as pd
from datetime import datetime


def show_battle_arena(model_manager, game_engine, db, ui):
    st.markdown("## ⚔️ Arena de Batalha")

    col1, col2 = st.columns([1, 2])

    with col1:
        st.markdown("### 🎮 Configuração da Batalha")

        # Tournament mode
        tournament_mode = st.checkbox(
            "Modo Torneio (todos vs todos)", value=False)

        if tournament_mode:
            st.markdown("#### 🏆 Configuração do Torneio")
            selected_models = st.multiselect(
                "Selecione os modelos participantes:",
                list(model_manager.get_available_models().keys()),
                default=list(model_manager.get_available_models().keys())[:4]
            )

            games_per_pair = st.slider("Partidas por confronto:", 1, 10, 3)

            if st.button("🚀 Iniciar Torneio", type="primary"):
                if len(selected_models) >= 2:
                    from app import start_tournament
                    start_tournament(selected_models, games_per_pair,
                                     model_manager, game_engine, db)
                else:
                    st.error("Selecione pelo menos 2 modelos para o torneio!")

        else:
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

            num_games = st.slider("Número de partidas:", 1, 20, 5)

            # Novo: slider para velocidade
            realtime_speed = st.slider(
                "Velocidade dos lances (s)", 0.1, 3.0, 1.0, 0.1, key="realtime_speed")

            if st.button("⚔️ Iniciar Batalha", type="primary"):
                from app import start_individual_battle
                start_individual_battle(
                    white_model, black_model, opening, num_games, model_manager, game_engine, db)

            # Botão para batalha em tempo real
            if st.button("⚡ Batalha em Tempo Real", type="secondary"):
                st.info(
                    f"Rodando batalha em tempo real: {white_model} vs {black_model}")
                result = game_engine.play_game_realtime(
                    white_model, black_model, opening=opening, ui=ui, sleep_time=realtime_speed)
                st.success(f"Resultado: {result['result']}")
                # Salvar no banco de dados
                db.save_game({
                    'white': white_model,
                    'black': black_model,
                    'result': result['result'],
                    'pgn': result['pgn'],
                    'moves': result['moves'],
                    'opening': opening,
                    'date': datetime.now().isoformat(),
                    'tournament_id': None,
                    'analysis': {}
                })
                st.info("Partida salva no banco de dados!")

    with col2:
        st.markdown("### 🎮 Status da Batalha")

        # Show current battle status
        if 'current_battle' in st.session_state:
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
