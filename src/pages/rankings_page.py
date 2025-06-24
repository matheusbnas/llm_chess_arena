import streamlit as st
import pandas as pd
import plotly.express as px


def show_rankings(db, analyzer, ui):
    st.markdown("## 🏆 Rankings e Estatísticas")

    tab1, tab2, tab3 = st.tabs(
        ["🏆 Ranking Geral", "📊 Estatísticas Detalhadas", "🎯 Performance por Abertura"])

    with tab1:
        st.markdown("### 🏆 Ranking Geral dos Modelos")

        # Calculate ELO ratings
        games = db.get_all_games()
        rankings = analyzer.calculate_elo_ratings(games)

        if rankings:
            # Display rankings table
            rankings_df = pd.DataFrame(list(rankings.values()))
            rankings_df = rankings_df.sort_values(
                'elo', ascending=False).reset_index(drop=True)
            rankings_df.index += 1

            st.dataframe(
                rankings_df[['model', 'elo', 'games_played',
                             'win_rate', 'avg_accuracy']],
                column_config={
                    'model': 'Modelo',
                    'elo': 'Rating ELO',
                    'games_played': 'Partidas',
                    'win_rate': st.column_config.ProgressColumn('Taxa de Vitória', min_value=0, max_value=1),
                    'avg_accuracy': 'Precisão Média'
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

    with tab2:
        st.markdown("### 📊 Estatísticas Detalhadas")

        # Model selection for detailed stats
        selected_model = st.selectbox(
            "Selecione um modelo para análise detalhada:",
            list(db.get_unique_models()),
            key="stats_model"
        )

        if selected_model:
            stats = analyzer.get_detailed_stats(selected_model)

            # Key metrics
            col1, col2, col3, col4 = st.columns(4)

            with col1:
                st.metric("Partidas Jogadas", stats['total_games'])
            with col2:
                st.metric("Taxa de Vitória", f"{stats['win_rate']:.1f}%")
            with col3:
                st.metric("Precisão Média", f"{stats['avg_accuracy']:.1f}%")
            with col4:
                st.metric("Rating ELO", stats['current_elo'])

            # Performance by color
            st.markdown("#### 🎨 Performance por Cor")

            color_stats = stats['by_color']
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

            # Recent performance trend
            st.markdown(
                "#### 📈 Tendência de Performance (Últimas 20 Partidas)")

            recent_performance = stats['recent_trend']
            if recent_performance:
                fig = px.line(
                    x=range(len(recent_performance)),
                    y=recent_performance,
                    title="Precisão nas Últimas Partidas"
                )
                st.plotly_chart(fig, use_container_width=True)

    with tab3:
        st.markdown("### 🎯 Performance por Abertura")

        opening_stats = analyzer.get_opening_statistics(db)

        if opening_stats:
            # Opening performance table
            opening_df = pd.DataFrame(opening_stats)
            opening_df = opening_df.sort_values('win_rate', ascending=False)

            st.dataframe(
                opening_df,
                column_config={
                    'opening': 'Abertura',
                    'games_played': 'Partidas',
                    'win_rate': st.column_config.ProgressColumn('Taxa de Vitória', min_value=0, max_value=1),
                    'avg_accuracy': 'Precisão Média',
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
