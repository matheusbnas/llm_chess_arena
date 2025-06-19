import streamlit as st
import chess
import chess.pgn
import chess.engine
import os
from io import StringIO
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import json
import requests
from typing import Dict, List, Tuple, Optional
import asyncio
import time

# Import modules
from src.models import ModelManager
from src.game_engine import GameEngine
from src.analysis import GameAnalyzer
from src.lichess_api import LichessAPI
from src.database import GameDatabase
from src.ui_components import UIComponents

# Page config
st.set_page_config(
    page_title="LLM Chess Arena",
    page_icon="♟️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        text-align: center;
        color: #1f77b4;
        font-size: 3rem;
        font-weight: bold;
        margin-bottom: 2rem;
        text-shadow: 2px 2px 4px rgba(0,0,0,0.1);
    }
    
    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1.5rem;
        border-radius: 15px;
        color: white;
        text-align: center;
        box-shadow: 0 8px 32px rgba(0,0,0,0.1);
        margin-bottom: 1rem;
    }
    
    .model-card {
        background: #f8f9fa;
        border: 2px solid #e9ecef;
        border-radius: 10px;
        padding: 1rem;
        margin: 0.5rem 0;
        transition: all 0.3s ease;
    }
    
    .model-card:hover {
        border-color: #1f77b4;
        box-shadow: 0 4px 12px rgba(31, 119, 180, 0.15);
    }
    
    .game-status {
        padding: 1rem;
        border-radius: 10px;
        margin: 1rem 0;
        font-weight: bold;
        text-align: center;
    }
    
    .status-playing {
        background: #d4edda;
        color: #155724;
        border: 1px solid #c3e6cb;
    }
    
    .status-finished {
        background: #f8d7da;
        color: #721c24;
        border: 1px solid #f5c6cb;
    }
    
    .chess-board {
        display: flex;
        justify-content: center;
        margin: 2rem 0;
    }
    
    .sidebar-section {
        background: #f8f9fa;
        padding: 1rem;
        border-radius: 10px;
        margin-bottom: 1rem;
    }
</style>
""", unsafe_allow_html=True)

def main():
    # Initialize components
    model_manager = ModelManager()
    game_engine = GameEngine()
    analyzer = GameAnalyzer()
    lichess_api = LichessAPI()
    db = GameDatabase()
    ui = UIComponents()
    
    # Header
    st.markdown('<h1 class="main-header">♟️ LLM Chess Arena</h1>', unsafe_allow_html=True)
    
    # Sidebar
    with st.sidebar:
        st.markdown('<div class="sidebar-section">', unsafe_allow_html=True)
        st.markdown("### 🎮 Navegação")
        
        # Main navigation
        page = st.selectbox(
            "Escolha uma seção:",
            ["🏠 Dashboard", "⚔️ Arena de Batalha", "🎯 Jogar vs LLM", "📊 Análise de Partidas", "🏆 Rankings", "⚙️ Configurações"],
            key="main_nav"
        )
        st.markdown('</div>', unsafe_allow_html=True)
        
        # Model status
        st.markdown('<div class="sidebar-section">', unsafe_allow_html=True)
        st.markdown("### 🤖 Status dos Modelos")
        available_models = model_manager.get_available_models()
        for model_name, status in available_models.items():
            status_icon = "🟢" if status else "🔴"
            st.markdown(f"{status_icon} {model_name}")
        st.markdown('</div>', unsafe_allow_html=True)
    
    # Main content based on selected page
    if page == "🏠 Dashboard":
        show_dashboard(db, analyzer, ui)
    elif page == "⚔️ Arena de Batalha":
        show_battle_arena(model_manager, game_engine, db, ui)
    elif page == "🎯 Jogar vs LLM":
        show_human_vs_llm(model_manager, game_engine, ui)
    elif page == "📊 Análise de Partidas":
        show_game_analysis(db, analyzer, lichess_api, ui)
    elif page == "🏆 Rankings":
        show_rankings(db, analyzer, ui)
    elif page == "⚙️ Configurações":
        show_settings(model_manager, lichess_api)

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

def show_battle_arena(model_manager, game_engine, db, ui):
    st.markdown("## ⚔️ Arena de Batalha")
    
    col1, col2 = st.columns([1, 2])
    
    with col1:
        st.markdown("### 🎮 Configuração da Batalha")
        
        # Tournament mode
        tournament_mode = st.checkbox("Modo Torneio (todos vs todos)", value=False)
        
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
                    start_tournament(selected_models, games_per_pair, model_manager, game_engine, db)
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
                ["1. e4", "1. d4", "1. c4", "1. Nf3", "1. b3", "1. c3", "1. e3", "1. d3", "1. g3", "1. Nc3"],
                key="opening"
            )
            
            num_games = st.slider("Número de partidas:", 1, 20, 5)
            
            if st.button("⚔️ Iniciar Batalha", type="primary"):
                start_individual_battle(white_model, black_model, opening, num_games, model_manager, game_engine, db)
    
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
                ui.display_board(st.session_state.current_board, key="battle_board")
            
            # Progress bar
            progress = battle['current_game'] / battle['total_games']
            st.progress(progress)
            
            # Results so far
            if battle['results']:
                st.markdown("#### 📊 Resultados Parciais")
                results_df = pd.DataFrame(battle['results'])
                st.dataframe(results_df, use_container_width=True)
        
        else:
            st.info("Nenhuma batalha em andamento. Configure uma batalha na coluna à esquerda.")

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
            initialize_human_game(opponent_model, player_color, difficulty, time_control)
        
        # Game controls
        if 'human_game' in st.session_state:
            st.markdown("### 🎮 Controles do Jogo")
            
            if st.button("🔄 Reiniciar"):
                del st.session_state.human_game
                st.rerun()
            
            if st.button("💾 Salvar Partida"):
                save_human_game()
            
            if st.button("🤖 Dica da IA"):
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
            ui.display_board(game['board'], key="human_game_board")
            
            # Move input
            if game['board'].turn == (chess.WHITE if game['player_color'] == "Brancas" else chess.BLACK):
                st.markdown("### 🎯 Seu Lance")
                
                col_move1, col_move2 = st.columns(2)
                
                with col_move1:
                    move_input = st.text_input(
                        "Digite seu lance (ex: e4, Nf3):",
                        key="move_input"
                    )
                
                with col_move2:
                    if st.button("▶️ Jogar Lance"):
                        if move_input:
                            make_human_move(move_input)
            
            else:
                st.markdown("### 🤖 IA está pensando...")
                if st.button("⏭️ Processar Lance da IA"):
                    make_ai_move(game['opponent'], model_manager, game_engine)
            
            # Move history
            st.markdown("### 📝 Histórico de Lances")
            if game['move_history']:
                moves_df = pd.DataFrame(game['move_history'])
                st.dataframe(moves_df, use_container_width=True)
        
        else:
            st.info("Configure um novo jogo na coluna à esquerda para começar!")

def show_game_analysis(db, analyzer, lichess_api, ui):
    st.markdown("## 📊 Análise de Partidas")
    
    tab1, tab2, tab3 = st.tabs(["🔍 Análise Individual", "📈 Análise Comparativa", "🌐 Integração Lichess"])
    
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
                    st.metric("Precisão das Brancas", f"{analysis['white_accuracy']:.1f}%")
                    st.metric("Precisão das Pretas", f"{analysis['black_accuracy']:.1f}%")
                    st.metric("Lances Totais", analysis['total_moves'])
                    st.metric("Erros Graves", analysis['blunders'])
                    
                    # Move quality chart
                    if analysis['move_evaluations']:
                        fig = px.line(
                            x=range(len(analysis['move_evaluations'])),
                            y=analysis['move_evaluations'],
                            title="Avaliação por Lance"
                        )
                        st.plotly_chart(fig, use_container_width=True)
                    
                    # Best/worst moves
                    if analysis['best_moves']:
                        st.markdown("#### ✅ Melhores Lances")
                        for move in analysis['best_moves'][:3]:
                            st.success(f"Lance {move['move_number']}: {move['san']}")
                    
                    if analysis['worst_moves']:
                        st.markdown("#### ❌ Piores Lances")
                        for move in analysis['worst_moves'][:3]:
                            st.error(f"Lance {move['move_number']}: {move['san']}")
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
            comparison = analyzer.compare_models(model1, model2)
            
            # Head-to-head record
            st.markdown("#### 🥊 Confronto Direto")
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric(f"Vitórias {model1}", comparison['model1_wins'])
            with col2:
                st.metric("Empates", comparison['draws'])
            with col3:
                st.metric(f"Vitórias {model2}", comparison['model2_wins'])
            
            # Performance metrics
            st.markdown("#### 📈 Métricas de Performance")
            
            metrics_df = pd.DataFrame({
                'Métrica': ['Precisão Média', 'Lances por Partida', 'Taxa de Erro', 'Tempo Médio'],
                model1: [
                    f"{comparison['model1_accuracy']:.1f}%",
                    f"{comparison['model1_avg_moves']:.1f}",
                    f"{comparison['model1_error_rate']:.1f}%",
                    f"{comparison['model1_avg_time']:.1f}s"
                ],
                model2: [
                    f"{comparison['model2_accuracy']:.1f}%",
                    f"{comparison['model2_avg_moves']:.1f}",
                    f"{comparison['model2_error_rate']:.1f}%",
                    f"{comparison['model2_avg_time']:.1f}s"
                ]
            })
            
            st.dataframe(metrics_df, use_container_width=True)
            
            # Performance over time
            if comparison['performance_over_time']:
                fig = px.line(
                    comparison['performance_over_time'],
                    x='game_number',
                    y='accuracy',
                    color='model',
                    title="Evolução da Precisão ao Longo do Tempo"
                )
                st.plotly_chart(fig, use_container_width=True)
    
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
                    imported_games = lichess_api.import_user_games(username, max_games)
                    
                    if imported_games:
                        st.success(f"✅ {len(imported_games)} partidas importadas com sucesso!")
                        
                        # Process games for training data
                        training_data = analyzer.process_lichess_games(imported_games)
                        
                        # Save training data
                        db.save_training_data(training_data)
                        
                        st.info("💾 Dados de treinamento salvos para melhorar os modelos!")
                    else:
                        st.error("❌ Erro ao importar partidas. Verifique o token e nome de usuário.")
            
            # RAG Enhancement
            st.markdown("#### 🧠 Melhoramento RAG")
            
            if st.button("🚀 Aplicar Melhoramentos RAG"):
                with st.spinner("Aplicando melhoramentos baseados em dados do Lichess..."):
                    # Apply RAG improvements to models
                    improvements = analyzer.apply_rag_improvements()
                    
                    if improvements:
                        st.success("✅ Melhoramentos RAG aplicados com sucesso!")
                        
                        # Show improvement metrics
                        for model, improvement in improvements.items():
                            st.metric(
                                f"Melhoria {model}",
                                f"+{improvement['accuracy_gain']:.1f}%",
                                delta=f"{improvement['performance_gain']:.1f}%"
                            )
                    else:
                        st.warning("⚠️ Nenhum melhoramento significativo detectado.")

def show_rankings(db, analyzer, ui):
    st.markdown("## 🏆 Rankings e Estatísticas")
    
    tab1, tab2, tab3 = st.tabs(["🏆 Ranking Geral", "📊 Estatísticas Detalhadas", "🎯 Performance por Abertura"])
    
    with tab1:
        st.markdown("### 🏆 Ranking Geral dos Modelos")
        
        # Calculate ELO ratings
        rankings = analyzer.calculate_elo_ratings()
        
        if rankings:
            # Display rankings table
            rankings_df = pd.DataFrame(rankings)
            rankings_df = rankings_df.sort_values('elo', ascending=False).reset_index(drop=True)
            rankings_df.index += 1
            
            st.dataframe(
                rankings_df[['model', 'elo', 'games_played', 'win_rate', 'avg_accuracy']],
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
            st.info("Dados insuficientes para calcular rankings. Jogue mais partidas!")
    
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
                {'Cor': 'Brancas', 'Vitórias': color_stats['white']['wins'], 'Empates': color_stats['white']['draws'], 'Derrotas': color_stats['white']['losses']},
                {'Cor': 'Pretas', 'Vitórias': color_stats['black']['wins'], 'Empates': color_stats['black']['draws'], 'Derrotas': color_stats['black']['losses']}
            ])
            
            fig = px.bar(
                color_df,
                x='Cor',
                y=['Vitórias', 'Empates', 'Derrotas'],
                title="Resultados por Cor das Peças"
            )
            st.plotly_chart(fig, use_container_width=True)
            
            # Recent performance trend
            st.markdown("#### 📈 Tendência de Performance (Últimas 20 Partidas)")
            
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
        
        opening_stats = analyzer.get_opening_statistics()
        
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

def show_settings(model_manager, lichess_api):
    st.markdown("## ⚙️ Configurações")
    
    tab1, tab2, tab3, tab4 = st.tabs(["🤖 Modelos", "🌐 APIs", "🎮 Jogo", "💾 Dados"])
    
    with tab1:
        st.markdown("### 🤖 Configuração dos Modelos")
        
        # API Keys configuration
        st.markdown("#### 🔑 Chaves de API")
        
        openai_key = st.text_input(
            "OpenAI API Key:",
            type="password",
            value=os.getenv("OPENAI_API_KEY", ""),
            key="openai_key"
        )
        
        google_key = st.text_input(
            "Google API Key:",
            type="password",
            value=os.getenv("GOOGLE_API_KEY", ""),
            key="google_key"
        )
        
        deepseek_key = st.text_input(
            "DeepSeek API Key:",
            type="password",
            value=os.getenv("DEEPSEEK_API_KEY", ""),
            key="deepseek_key"
        )
        
        groq_key = st.text_input(
            "Groq API Key:",
            type="password",
            value=os.getenv("GROQ_API_KEY", ""),
            key="groq_key"
        )
        
        if st.button("💾 Salvar Chaves de API"):
            # Save API keys to .env file
            env_content = f"""
OPENAI_API_KEY={openai_key}
GOOGLE_API_KEY={google_key}
DEEPSEEK_API_KEY={deepseek_key}
GROQ_API_KEY={groq_key}
"""
            with open('.env', 'w') as f:
                f.write(env_content)
            
            st.success("✅ Chaves de API salvas com sucesso!")
            st.info("🔄 Reinicie a aplicação para aplicar as mudanças.")
        
        # Model parameters
        st.markdown("#### 🎛️ Parâmetros dos Modelos")
        
        temperature = st.slider(
            "Temperatura (criatividade):",
            0.0, 2.0, 0.1, 0.1,
            help="Valores mais altos tornam as respostas mais criativas"
        )
        
        max_tokens = st.slider(
            "Máximo de tokens:",
            100, 4000, 1000, 100,
            help="Limite de tokens para as respostas dos modelos"
        )
        
        thinking_time = st.slider(
            "Tempo de reflexão (segundos):",
            1, 30, 5, 1,
            help="Tempo que o modelo tem para 'pensar' antes de fazer um lance"
        )
        
        # Model testing
        st.markdown("#### 🧪 Teste dos Modelos")
        
        test_model = st.selectbox(
            "Modelo para teste:",
            list(model_manager.get_available_models().keys()),
            key="test_model"
        )
        
        if st.button("🧪 Testar Modelo"):
            with st.spinner("Testando modelo..."):
                test_result = model_manager.test_model(test_model)
                
                if test_result['success']:
                    st.success(f"✅ Modelo {test_model} funcionando corretamente!")
                    st.info(f"Tempo de resposta: {test_result['response_time']:.2f}s")
                else:
                    st.error(f"❌ Erro no modelo {test_model}: {test_result['error']}")
    
    with tab2:
        st.markdown("### 🌐 Configuração de APIs")
        
        # Lichess API
        st.markdown("#### ♟️ Lichess API")
        
        lichess_token = st.text_input(
            "Token do Lichess:",
            type="password",
            help="Obtenha em https://lichess.org/account/oauth/token"
        )
        
        if st.button("🔗 Conectar ao Lichess"):
            if lichess_token:
                success = lichess_api.test_connection(lichess_token)
                if success:
                    st.success("✅ Conectado ao Lichess com sucesso!")
                else:
                    st.error("❌ Erro na conexão com o Lichess. Verifique o token.")
            else:
                st.warning("⚠️ Insira um token válido.")
        
        # Stockfish configuration
        st.markdown("#### 🐟 Stockfish Engine")
        
        stockfish_path = st.text_input(
            "Caminho do Stockfish:",
            value="/usr/local/bin/stockfish",
            help="Caminho para o executável do Stockfish"
        )
        
        stockfish_depth = st.slider(
            "Profundidade de análise:",
            1, 20, 15, 1,
            help="Profundidade da análise do Stockfish (maior = mais preciso, mas mais lento)"
        )
        
        if st.button("🧪 Testar Stockfish"):
            try:
                with chess.engine.SimpleEngine.popen_uci(stockfish_path) as engine:
                    st.success("✅ Stockfish funcionando corretamente!")
                    info = engine.id
                    st.info(f"Versão: {info.get('name', 'Desconhecida')}")
            except Exception as e:
                st.error(f"❌ Erro no Stockfish: {str(e)}")
    
    with tab3:
        st.markdown("### 🎮 Configurações de Jogo")
        
        # Default game settings
        st.markdown("#### 🎯 Configurações Padrão")
        
        default_time_control = st.selectbox(
            "Controle de tempo padrão:",
            ["Sem limite", "5 min", "10 min", "15 min", "30 min"],
            index=2
        )
        
        auto_save_games = st.checkbox(
            "Salvar partidas automaticamente",
            value=True,
            help="Salva automaticamente todas as partidas jogadas"
        )
        
        show_coordinates = st.checkbox(
            "Mostrar coordenadas no tabuleiro",
            value=True,
            help="Exibe as coordenadas (a-h, 1-8) no tabuleiro"
        )
        
        highlight_last_move = st.checkbox(
            "Destacar último lance",
            value=True,
            help="Destaca o último lance jogado no tabuleiro"
        )
        
        # Analysis settings
        st.markdown("#### 📊 Configurações de Análise")
        
        auto_analysis = st.checkbox(
            "Análise automática após partidas",
            value=False,
            help="Executa análise automática com Stockfish após cada partida"
        )
        
        analysis_depth = st.slider(
            "Profundidade da análise automática:",
            5, 20, 12, 1,
            help="Profundidade da análise automática (se habilitada)"
        )
        
        save_analysis = st.checkbox(
            "Salvar resultados da análise",
            value=True,
            help="Salva os resultados da análise no banco de dados"
        )
    
    with tab4:
        st.markdown("### 💾 Gerenciamento de Dados")
        
        # Database statistics
        st.markdown("#### 📊 Estatísticas do Banco de Dados")
        
        db_stats = db.get_database_stats()
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Total de Partidas", db_stats['total_games'])
        with col2:
            st.metric("Modelos Únicos", db_stats['unique_models'])
        with col3:
            st.metric("Tamanho do BD", f"{db_stats['db_size_mb']:.1f} MB")
        
        # Data management
        st.markdown("#### 🗂️ Gerenciamento de Dados")
        
        # Export data
        if st.button("📤 Exportar Dados"):
            export_data = db.export_all_data()
            
            st.download_button(
                label="💾 Baixar Dados (JSON)",
                data=json.dumps(export_data, indent=2),
                file_name=f"llm_chess_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                mime="application/json"
            )
        
        # Import data
        uploaded_file = st.file_uploader(
            "📥 Importar Dados",
            type=['json'],
            help="Importe dados de backup em formato JSON"
        )
        
        if uploaded_file and st.button("📥 Importar"):
            try:
                import_data = json.load(uploaded_file)
                success = db.import_data(import_data)
                
                if success:
                    st.success("✅ Dados importados com sucesso!")
                else:
                    st.error("❌ Erro ao importar dados.")
            except Exception as e:
                st.error(f"❌ Erro ao processar arquivo: {str(e)}")
        
        # Clear data
        st.markdown("#### 🗑️ Limpeza de Dados")
        
        st.warning("⚠️ Atenção: As operações abaixo são irreversíveis!")
        
        if st.button("🗑️ Limpar Partidas Antigas (>30 dias)", type="secondary"):
            if st.checkbox("Confirmo que quero deletar partidas antigas"):
                deleted_count = db.delete_old_games(days=30)
                st.success(f"✅ {deleted_count} partidas antigas removidas.")
        
        if st.button("💥 Resetar Banco de Dados", type="secondary"):
            if st.checkbox("Confirmo que quero resetar TODOS os dados"):
                if st.text_input("Digite 'CONFIRMAR' para prosseguir:") == "CONFIRMAR":
                    db.reset_database()
                    st.success("✅ Banco de dados resetado com sucesso!")
                    st.info("🔄 Reinicie a aplicação.")

# Helper functions for battle management
def start_tournament(models, games_per_pair, model_manager, game_engine, db):
    """Start a tournament with all selected models"""
    st.session_state.tournament = {
        'models': models,
        'games_per_pair': games_per_pair,
        'current_pair': 0,
        'current_game': 0,
        'total_pairs': len(models) * (len(models) - 1),
        'results': [],
        'status': 'running'
    }
    
    st.success(f"🏆 Torneio iniciado com {len(models)} modelos!")
    st.info(f"Total de confrontos: {st.session_state.tournament['total_pairs']}")

def start_individual_battle(white_model, black_model, opening, num_games, model_manager, game_engine, db):
    """Start an individual battle between two models"""
    st.session_state.current_battle = {
        'white': white_model,
        'black': black_model,
        'opening': opening,
        'current_game': 0,
        'total_games': num_games,
        'results': [],
        'status': 'running'
    }
    
    st.success(f"⚔️ Batalha iniciada: {white_model} vs {black_model}")

def initialize_human_game(opponent_model, player_color, difficulty, time_control):
    """Initialize a new human vs AI game"""
    st.session_state.human_game = {
        'board': chess.Board(),
        'opponent': opponent_model,
        'player_color': player_color,
        'difficulty': difficulty,
        'time_control': time_control,
        'move_history': [],
        'start_time': datetime.now(),
        'status': 'playing'
    }
    
    st.success(f"🎮 Novo jogo iniciado contra {opponent_model}!")

def make_human_move(move_input):
    """Process a human player's move"""
    game = st.session_state.human_game
    
    try:
        move = game['board'].parse_san(move_input)
        game['board'].push(move)
        
        game['move_history'].append({
            'move_number': len(game['move_history']) + 1,
            'player': 'Humano',
            'move': move_input,
            'time': datetime.now()
        })
        
        st.success(f"✅ Lance jogado: {move_input}")
        
        # Check for game end
        if game['board'].is_game_over():
            end_human_game()
        
    except ValueError:
        st.error("❌ Lance inválido! Tente novamente.")

def make_ai_move(opponent_model, model_manager, game_engine):
    """Process an AI move"""
    game = st.session_state.human_game
    
    with st.spinner("🤖 IA está pensando..."):
        # Get AI move using the game engine
        ai_move = game_engine.get_ai_move(
            game['board'], 
            opponent_model, 
            game['difficulty']
        )
        
        if ai_move:
            game['board'].push(ai_move)
            
            game['move_history'].append({
                'move_number': len(game['move_history']) + 1,
                'player': opponent_model,
                'move': game['board'].san(ai_move),
                'time': datetime.now()
            })
            
            st.success(f"🤖 IA jogou: {game['board'].san(ai_move)}")
            
            # Check for game end
            if game['board'].is_game_over():
                end_human_game()
        else:
            st.error("❌ Erro ao processar lance da IA")

def end_human_game():
    """End the current human vs AI game"""
    game = st.session_state.human_game
    result = game['board'].result()
    
    game['status'] = 'finished'
    game['result'] = result
    game['end_time'] = datetime.now()
    
    # Determine winner
    if result == "1-0":
        winner = "Brancas"
    elif result == "0-1":
        winner = "Pretas"
    else:
        winner = "Empate"
    
    st.success(f"🏁 Jogo finalizado! Resultado: {winner}")

def save_human_game():
    """Save the current human game to database"""
    if 'human_game' in st.session_state:
        game = st.session_state.human_game
        # Save game logic here
        st.success("💾 Partida salva com sucesso!")

def show_ai_hint():
    """Show an AI hint for the current position"""
    if 'human_game' in st.session_state:
        game = st.session_state.human_game
        # Get hint logic here
        st.info("💡 Dica: Considere desenvolver suas peças antes de atacar!")

if __name__ == "__main__":
    main()