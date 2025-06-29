import streamlit as st
import pandas as pd
import plotly.express as px
import os
import chess.pgn
from io import StringIO
from collections import defaultdict
from src.pgn_importer import get_pgn_folders, read_pgn_file


def show_dashboard(db, analyzer, ui):
    st.markdown("## 📈 Dashboard Geral")

    # Metrics row
    col1, col2, col3= st.columns(3)

    stats = db.get_global_stats()

    with col1:
        st.markdown(f"""
        <div class="metric-card">
            <h3>{stats['total_games']}</h3>
            <p>Total de Partidas</p>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        active_models = get_active_models()
        st.markdown(f"""
        <div class="metric-card">
            <h3>{len(active_models)}</h3>
            <p>Modelos Ativos</p>
            <p style='font-size:0.9em; color:#eee;'>({', '.join(active_models) if active_models else 'Nenhum'})</p>
        </div>
        """, unsafe_allow_html=True)

    with col3:
        st.markdown(f"""
        <div class="metric-card">
            <h3>{stats['avg_game_length']:.1f}</h3>
            <p>Lances por Partida</p>
        </div>
        """, unsafe_allow_html=True)

    # Charts row
    col1, col2 = st.columns(2)

    with col1:
        st.markdown("### 📊 Resultados por Modelo")
        
        # First try to get results from database
        results_data = db.get_results_by_model()
        
        # If no results in database, scan PGN folders and calculate results
        if not results_data:
            results_data = get_results_from_pgn_folders()
            
        if results_data:
            # Convert results to DataFrame for plotting
            df = pd.DataFrame(results_data)
            
            fig = px.bar(
                df,
                x='model',
                y=['wins', 'draws', 'losses'],
                title="Vitórias, Empates e Derrotas por Modelo",
                color_discrete_sequence=['#28a745', '#ffc107', '#dc3545']
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Nenhum resultado de modelo encontrado. Importe partidas para visualizar.")

    with col2:
        st.markdown("### 🎯 Taxa de Vitória")
        winrate_data = db.get_winrate_data()
        if winrate_data:
            # Ensure percentages add up to 100%
            total = sum(item['percentage'] for item in winrate_data)
            if total > 0:
                for item in winrate_data:
                    item['percentage'] = (item['percentage'] / total) * 100
                    
            fig = px.pie(
                winrate_data,
                values='percentage',
                names='result_type',
                title="Distribuição de Resultados",
                color_discrete_sequence=['#28a745', '#dc3545', '#ffc107']
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Nenhum dado de vitória encontrado. Inicie uma batalha na Arena!")

    # Recent games
    st.markdown("### 🕒 Partidas Recentes")
    recent_games = db.get_recent_games(limit=10)
    if recent_games:
        df = pd.DataFrame(recent_games)
        st.dataframe(df, use_container_width=True)
    else:
        st.info("Nenhuma partida encontrada. Inicie uma batalha na Arena!")

def get_results_from_pgn_folders():
    """Extract game results from PGN folders to calculate model statistics"""
    base_path = os.getcwd()
    pgn_folders = get_pgn_folders(base_path)
    model_stats = defaultdict(lambda: {'wins': 0, 'draws': 0, 'losses': 0})
    
    for folder in pgn_folders:
        folder_path = os.path.join(base_path, folder)
        
        # Extract model names from folder name (e.g., "GPT-4o vs Gemini-Pro")
        parts = folder.split(" vs ")
        if len(parts) == 2:  # Formato "Modelo1 vs Modelo2"
            model1, model2 = parts[0], parts[1]
        else:
            # Para outras pastas como "Human_vs_LLM", extrair dos cabeçalhos dos jogos
            model1 = model2 = None
            
        for fname in os.listdir(folder_path):
            if fname.endswith('.pgn'):
                file_path = os.path.join(folder_path, fname)
                pgn_text = read_pgn_file(file_path)
                pgn_io = StringIO(pgn_text)
                
                while True:
                    game = chess.pgn.read_game(pgn_io)
                    if game is None:
                        break
                    
                    # Se não temos modelos do nome da pasta, pegar dos cabeçalhos
                    if model1 is None or model2 is None:
                        model1 = game.headers.get('White', 'Unknown')
                        model2 = game.headers.get('Black', 'Unknown')
                        
                    result = game.headers.get('Result', '*')
                    
                    # Update stats based on result
                    if result == "1-0":
                        model_stats[model1]['wins'] += 1
                        model_stats[model2]['losses'] += 1
                    elif result == "0-1":
                        model_stats[model1]['losses'] += 1
                        model_stats[model2]['wins'] += 1
                    elif result == "1/2-1/2":
                        model_stats[model1]['draws'] += 1
                        model_stats[model2]['draws'] += 1
    
    # Convert to list format similar to get_results_by_model
    results = []
    for model, stats in model_stats.items():
        results.append({
            'model': model,
            'wins': stats['wins'],
            'draws': stats['draws'],
            'losses': stats['losses']
        })
    
    return results

def get_active_models():
    models = {
        "OpenAI": os.getenv("OPENAI_API_KEY"),
        "Google": os.getenv("GOOGLE_API_KEY"),
        "DeepSeek": os.getenv("DEEPSEEK_API_KEY"),
        "Groq": os.getenv("GROQ_API_KEY"),
        "Claude": os.getenv("CLAUDE_API_KEY"),
    }
    # Conta quantos modelos têm chave preenchida
    return [name for name, key in models.items() if key and key.strip()]
