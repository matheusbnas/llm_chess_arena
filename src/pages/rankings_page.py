import streamlit as st
import pandas as pd
import plotly.express as px


def show_rankings(db, analyzer, ui):
    st.markdown("## 🏆 Rankings e Estatísticas")

    tab1, tab2, tab3 = st.tabs(
        ["🏆 Ranking Geral", "📊 Estatísticas Detalhadas", "🎯 Performance por Abertura"])

    # --- TAB 1: Ranking Geral ---
    with tab1:
        st.markdown("### 🏆 Ranking Geral dos Modelos")

        # Calculate ELO ratings
        games = db.get_all_games()
        rankings = analyzer.calculate_elo_ratings(games)

        rankings_df = None
        if rankings:
            # Display rankings table
            rankings_df = pd.DataFrame(list(rankings.values()))
            rankings_df = rankings_df.sort_values(
                'elo', ascending=False).reset_index(drop=True)
            rankings_df.index += 1

            st.dataframe(
                rankings_df[['model', 'elo', 'games_played', 'win_rate']],
                column_config={
                    'model': 'Modelo',
                    'elo': 'Rating ELO',
                    'games_played': 'Partidas',
                    'win_rate': st.column_config.ProgressColumn('Taxa de Vitória', min_value=0, max_value=1)
                },
                use_container_width=True
            )

            # ELO progression chart
            st.markdown("### 📈 Evolução do Rating ELO")

            elo_history = db.get_elo_history()
            if elo_history:
                fig = px.line(
                    elo_history,
                    x='date',
                    y='elo',
                    color='model',
                    title="Evolução do Rating ELO ao Longo do Tempo"
                )
                st.plotly_chart(fig, use_container_width=True)
        else:
            st.info(
                "Dados insuficientes para calcular rankings. Jogue mais partidas!")

    # --- TAB 2: Estatísticas Detalhadas ---
    with tab2:
        st.markdown("### 📊 Estatísticas Detalhadas")

        # Model selection for detailed stats
        unique_models = list(db.get_unique_models())
        selected_model = st.selectbox(
            "Selecione um modelo para análise detalhada:",
            unique_models,
            key="stats_model"
        )

        if selected_model:
            stats = analyzer.get_detailed_stats(selected_model, db)

            # Sincronizar ELO com ranking geral, se disponível
            current_elo = stats.get('current_elo', 1500)
            if rankings_df is not None:
                elo_row = rankings_df[rankings_df['model'] == selected_model]
                if not elo_row.empty:
                    current_elo = elo_row.iloc[0]['elo']

            # Usar color_stats para garantir consistência dos dados
            color_stats = stats['by_color']
            wins = color_stats['white']['wins'] + color_stats['black']['wins']
            draws = color_stats['white']['draws'] + color_stats['black']['draws']
            losses = color_stats['white']['losses'] + color_stats['black']['losses']
            total_games = wins + draws + losses

            win_rate = (wins / total_games * 100) if total_games > 0 else 0.0
            loss_rate = (losses / total_games * 100) if total_games > 0 else 0.0

            # Key metrics
            col1, col2, col3, col4, col5 = st.columns(5)

            with col1:
                st.metric("Partidas Jogadas", total_games)
            with col2:
                st.metric("Taxa de Vitória", f"{win_rate:.1f}%")
            with col3:
                st.metric("Taxa de Empate", f"{draws:.1f}%")
            with col4:
                st.metric("Taxa de Derrota", f"{loss_rate:.1f}%")
            with col5:
                st.metric("Rating ELO", current_elo)

            # Performance by color
            st.markdown("#### 🎨 Performance por Cor")

            color_df = pd.DataFrame([
                {'Cor': 'Brancas', 'Vitórias': color_stats['white']['wins'],
                    'Empates': color_stats['white']['draws'], 'Derrotas': color_stats['white']['losses']},
                {'Cor': 'Pretas', 'Vitórias': color_stats['black']['wins'],
                    'Empates': color_stats['black']['draws'], 'Derrotas': color_stats['black']['losses']}
            ])

            fig = px.bar(
                color_df,
                x='Cor',
                y=['Vitórias', 'Empates', 'Derrotas'],
                title="Resultados por Cor das Peças"
            )
            st.plotly_chart(fig, use_container_width=True)


    # --- TAB 3: Performance por Abertura ---
    with tab3:
        st.markdown("### 🎯 Performance por Abertura")

        opening_stats = analyzer.get_opening_statistics(db)

        if opening_stats:
            opening_df = pd.DataFrame(opening_stats)
            opening_df = opening_df.sort_values('games_played', ascending=False)

            # Garante que todas as colunas existem ANTES de acessar
            for col in ['win_rate', 'loss_rate', 'draw_rate', 'avg_game_length']:
                if col not in opening_df.columns:
                    opening_df[col] = 0.0

            opening_df = opening_df.fillna(0.0)

            st.dataframe(
                opening_df.reindex(columns=[
                    'opening',
                    'games_played',
                    'win_rate',
                    'loss_rate',
                    'draw_rate',
                    'avg_game_length'
                ]),
                column_config={
                    'opening': 'Abertura',
                    'games_played': 'Partidas',
                    'win_rate': st.column_config.ProgressColumn('Vitórias Brancas', min_value=0, max_value=1, format="%.1%"),
                    'loss_rate': st.column_config.ProgressColumn('Vitórias Pretas', min_value=0, max_value=1, format="%.1%"),
                    'draw_rate': st.column_config.ProgressColumn('Empates', min_value=0, max_value=1, format="%.1%"),
                    'avg_game_length': 'Lances Médios'
                },
                use_container_width=True
            )

            # Opening popularity chart
            st.markdown("#### 📊 Popularidade das Aberturas")

            fig = px.pie(
                opening_df,
                values='games_played',
                names='opening',
                title="Distribuição de Partidas por Abertura"
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Dados insuficientes para análise de aberturas.")
