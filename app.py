import streamlit as st
import chess
import chess.pgn
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
from streamlit_option_menu import option_menu
from dotenv import load_dotenv

# Import modules
from src.models import ModelManager
from src.game_engine import GameEngine
from src.analysis import GameAnalyzer
from src.lichess_api import LichessAPI
from src.database import GameDatabase
from src.ui_components import UIComponents
from src.pages.dashboard_page import show_dashboard
from src.pages.arena_page import show_battle_arena
from src.pages.human_vs_llm_page import show_human_vs_llm
from src.pages.analysis_page import show_game_analysis
from src.pages.rankings_page import show_rankings
from src.pages.settings_page import show_settings
from src.pgn_importer import import_pgns_to_db

load_dotenv()

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

    # Importar PGNs das pastas para o banco de dados (apenas se houver novas)
    base_path = os.getcwd()
    imported_count = import_pgns_to_db(base_path, db)
    if imported_count > 0:
        st.success(f"{imported_count} partidas PGN importadas das pastas!")

    # Header
    st.markdown('<h1 class="main-header">♟️ LLM Chess Arena</h1>',
                unsafe_allow_html=True)

    # Sidebar
    with st.sidebar:
        selected = option_menu(
            menu_title="Menu Principal",
            options=[
                "🏠 Dashboard",
                "⚔️ Arena de Batalha",
                "🎯 Humano vs LLM",
                "📊 Análise de Partidas",
                "🏆 Rankings",
                "⚙️ Configurações",
                "📥 Importar PGNs"
            ],
            icons=[
                "bar-chart", "trophy", "person", "graph-up", "award", "gear", "cloud-upload"
            ],
            menu_icon="cast",
            default_index=0,
            orientation="vertical"
        )
        st.markdown('---')

    # Main content based on selected page
    if selected == "🏠 Dashboard":
        show_dashboard(db, analyzer, ui)
    elif selected == "⚔️ Arena de Batalha":
        # Create wrapper functions that will be called only when needed   
        def battle_wrapper(*args, **kwargs):
            start_individual_battle(*args, **kwargs)
        def start_individual_battle(model, opponent, opening=None, realtime_speed=1.0):
            """
            Start an individual battle between the selected model and opponent.
            This function is wrapped to allow passing it to the UI without direct reference.
            """
            game_engine.start_individual_battle(
                model=model,
                opponent=opponent,
                opening=opening,
                realtime_speed=realtime_speed
            )
        # Pass the wrapper functions instead of direct references
        show_battle_arena(model_manager, game_engine, db, ui, 
                         start_individual_battle_func=battle_wrapper)
    elif selected == "🎯 Humano vs LLM":
        show_human_vs_llm(model_manager, db, game_engine)
    elif selected == "📊 Análise de Partidas":
        show_game_analysis(db, analyzer, lichess_api, ui)
    elif selected == "🏆 Rankings":
        show_rankings(db, analyzer, ui)
    elif selected == "⚙️ Configurações":
        show_settings(model_manager, lichess_api, db)
    elif selected == "📥 Importar PGNs":
        show_import_pgns()


def show_import_pgns():
    import os
    st.markdown("## 📥 Importar Partidas PGN das Pastas")
    st.info("Esta função irá importar todas as partidas PGN das subpastas do projeto.")
    if st.button("🚀 Importar PGNs das Pastas", type="primary"):
        from src.pgn_importer import import_all_pgn_games
        base_path = os.getcwd()
        games = import_all_pgn_games(base_path)
        st.success(f"✅ {len(games)} partidas importadas!")
        # Opcional: mostrar uma amostra das partidas
        if games:
            st.write("Exemplo de partida importada:")
            game = games[0]['game']
            st.text(str(game))


if __name__ == "__main__":
    main()
