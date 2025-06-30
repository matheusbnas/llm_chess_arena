import streamlit as st
import pandas as pd
import plotly.express as px
import chess
from io import StringIO


def show_game_analysis(db, analyzer, lichess_api, ui):
    st.markdown("## 📊 Análise de Partidas")

    tab1, tab2, tab3 = st.tabs(
        ["🔍 Análise Individual", "📈 Análise Comparativa", "🌐 Integração Lichess"])

    with tab1:
        st.markdown("### 🔍 Análise Detalhada de Partida")

        # Game selection
        games = db.get_all_games()
        if games:
            selected_game = st.selectbox(
                "Selecione uma partida:",
                games,
                format_func=lambda x: f"{x['white']} vs {x['black']} - {x['result']} ({x['date']})"
            )

            if selected_game:
                col1, col2 = st.columns([2, 1])

                with col1:
                    # Load and display game
                    game_pgn = db.load_game_pgn(selected_game['id'])
                    game = chess.pgn.read_game(StringIO(game_pgn))

                    # Interactive board with move navigation
                    ui.display_interactive_game(game, key="analysis_game")

                with col2:
                    # Analysis results
                    st.markdown("### 📊 Análise da Partida")

                    analysis = analyzer.analyze_game(game)

                    # Key metrics
                    st.metric("Lances Totais", analysis['total_moves'])

                    # Best/worst moves
                    if 'captures' in analysis:
                        st.metric("Capturas", analysis['captures'])
                    if 'checks' in analysis:
                        st.metric("Checks", analysis['checks'])
        else:
            st.info("Nenhuma partida encontrada para análise.")

    with tab2:
        st.markdown("### 📈 Análise Comparativa")

        # Model comparison
        col1, col2 = st.columns(2)

        with col1:
            model1 = st.selectbox(
                "Modelo 1:",
                list(db.get_unique_models()),
                key="compare_model1"
            )

        with col2:
            model2 = st.selectbox(
                "Modelo 2:",
                list(db.get_unique_models()),
                key="compare_model2"
            )

        if st.button("📊 Comparar Modelos"):
            comparison = analyzer.compare_models(model1, model2, db)

            if "error" in comparison:
                st.error(comparison["error"])
            else:
                # Head-to-head record only
                st.markdown("#### 🥊 Confronto Direto")
                col1, col2, col3 = st.columns(3)

                with col1:
                    st.metric(f"Vitórias {model1}", comparison['model1_wins'])
                with col2:
                    st.metric("Empates", comparison['draws'])
                with col3:
                    st.metric(f"Vitórias {model2}", comparison['model2_wins'])

    with tab3:
        st.markdown("### 🌐 Integração com Lichess")

        # Lichess configuration
        st.markdown("#### ⚙️ Configuração")

        lichess_token = st.text_input(
            "Token de API do Lichess:",
            type="password",
            help="Obtenha seu token em https://lichess.org/account/oauth/token"
        )

        if lichess_token:
            lichess_api.set_token(lichess_token)

            # Import games
            st.markdown("#### 📥 Importar Partidas")

            username = st.text_input("Nome de usuário do Lichess:")
            max_games = st.slider("Máximo de partidas:", 10, 1000, 100)

            if st.button("📥 Importar Partidas"):
                with st.spinner("Importando partidas do Lichess..."):
                    imported_games = lichess_api.import_user_games(
                        username, max_games)

                    if imported_games:
                        st.success(
                            f"✅ {len(imported_games)} partidas importadas com sucesso!")

                        # Process games for training data
                        training_data = analyzer.process_lichess_games(
                            imported_games)

                        # Save training data
                        db.save_training_data(training_data)

                        st.info(
                            "💾 Dados de treinamento salvos para melhorar os modelos!")
                    else:
                        st.error(
                            "❌ Erro ao importar partidas. Verifique o token e nome de usuário.")

            # RAG Enhancement
            st.markdown("#### 🧠 Melhoramento RAG")

            if st.button("🚀 Aplicar Melhoramentos RAG"):
                with st.spinner("Aplicando melhoramentos baseados em dados do Lichess..."):
                    # Apply RAG improvements to models
                    improvements = analyzer.apply_rag_improvements()

                    if improvements:
                        st.success(
                            "✅ Melhoramentos RAG aplicados com sucesso!")

                        # Show improvement metrics
                        for model, improvement in improvements.items():
                            st.metric(
                                f"Melhoria {model}",
                                f"+{improvement['accuracy_gain']:.1f}%",
                                delta=f"{improvement['performance_gain']:.1f}%"
                            )
                    else:
                        st.warning(
                            "⚠️ Nenhum melhoramento significativo detectado.")
