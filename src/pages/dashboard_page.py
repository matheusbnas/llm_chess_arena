import streamlit as st
import pandas as pd
import plotly.express as px


def show_dashboard(db, analyzer, ui):
    st.markdown("## 📈 Dashboard Geral")

    # Metrics row
    col1, col2, col3, col4 = st.columns(4)

    stats = db.get_global_stats()

    with col1:
        st.markdown(f"""
        <div class="metric-card">
            <h3>{stats['total_games']}</h3>
            <p>Total de Partidas</p>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        st.markdown(f"""
        <div class="metric-card">
            <h3>{stats['active_models']}</h3>
            <p>Modelos Ativos</p>
        </div>
        """, unsafe_allow_html=True)

    with col3:
        st.markdown(f"""
        <div class="metric-card">
            <h3>{stats['avg_game_length']:.1f}</h3>
            <p>Lances por Partida</p>
        </div>
        """, unsafe_allow_html=True)

    with col4:
        st.markdown(f"""
        <div class="metric-card">
            <h3>{stats['tournaments_completed']}</h3>
            <p>Torneios Completos</p>
        </div>
        """, unsafe_allow_html=True)

    # Charts row
    col1, col2 = st.columns(2)

    with col1:
        st.markdown("### 📊 Resultados por Modelo")
        results_data = db.get_results_by_model()
        if results_data:
            fig = px.bar(
                results_data,
                x='model',
                y=['wins', 'draws', 'losses'],
                title="Vitórias, Empates e Derrotas por Modelo"
            )
            st.plotly_chart(fig, use_container_width=True)

    with col2:
        st.markdown("### 🎯 Taxa de Vitória")
        winrate_data = db.get_winrate_data()
        if winrate_data:
            fig = px.pie(
                winrate_data,
                values='percentage',
                names='result_type',
                title="Distribuição de Resultados"
            )
            st.plotly_chart(fig, use_container_width=True)

    # Recent games
    st.markdown("### 🕒 Partidas Recentes")
    recent_games = db.get_recent_games(limit=10)
    if recent_games:
        df = pd.DataFrame(recent_games)
        st.dataframe(df, use_container_width=True)
    else:
        st.info("Nenhuma partida encontrada. Inicie uma batalha na Arena!")
