import streamlit as st
import chess
import chess.svg
import chess.pgn
from typing import Optional, List, Dict, Any
import pandas as pd
from io import StringIO


class UIComponents:
    """Reusable UI components for the chess application"""

    def __init__(self):
        self.board_size = 480

    def display_board(self, board: chess.Board, flipped: bool = False,
                      key: str = None, highlight_squares: List[int] = None,
                      arrows: List[tuple] = None) -> None:
        """Display a chess board with optional highlights and arrows"""

        # Prepare highlights using colors dict
        colors = {}
        if highlight_squares:
            for sq in highlight_squares:
                colors[sq] = "#7fff7f80"  # Verde translúcido
        arrow_list = arrows or []
        board_svg = chess.svg.board(
            board=board,
            size=self.board_size,
            orientation=chess.BLACK if flipped else chess.WHITE,
            arrows=arrow_list,
            colors=colors
        )

        # Display centered
        st.markdown(
            f'<div style="display: flex; justify-content: center; margin: 20px 0;">{board_svg}</div>',
            unsafe_allow_html=True
        )

    def display_interactive_game(self, game: chess.pgn.Game, key: str = "interactive_game"):
        """Display an interactive game viewer with move navigation"""

        # Get all moves
        moves = list(game.mainline_moves())
        max_moves = len(moves)
        # Slider para navegação
        move_number = st.slider(
            "Move",
            0, max_moves,
            0,
            key=f"{key}_slider"
        )
        # Cria o board na posição do lance
        board = chess.Board()
        for i, move in enumerate(moves):
            if i < move_number:
                board.push(move)
        # Destaca o último movimento
        highlight = []
        if move_number > 0:
            last_move = moves[move_number - 1]
            highlight = [last_move.from_square, last_move.to_square]
        self.display_board(
            board, key=f"{key}_board", highlight_squares=highlight)
        # Info do lance atual
        if move_number > 0:
            move_index = move_number - 1
            current_move = moves[move_index]
            temp_board = chess.Board()
            for i, move in enumerate(moves):
                if i == move_index:
                    san_move = temp_board.san(move)
                    break
                temp_board.push(move)
            move_num = (move_index // 2) + 1
            color = "White" if move_index % 2 == 0 else "Black"
            st.info(f"Move {move_num}: {color} plays {san_move}")
        # Game status
        if board.is_checkmate():
            winner = "Black" if board.turn == chess.WHITE else "White"
            st.error(f"Checkmate! {winner} wins!")
        elif board.is_stalemate():
            st.warning("Stalemate! The game is a draw.")
        elif board.is_check():
            color = "White" if board.turn == chess.WHITE else "Black"
            st.warning(f"{color} is in check!")

    def display_game_info(self, game: chess.pgn.Game) -> None:
        """Display game information in a formatted way"""

        headers = game.headers

        col1, col2 = st.columns(2)

        with col1:
            st.markdown("**Players**")
            st.write(f"White: {headers.get('White', 'Unknown')}")
            st.write(f"Black: {headers.get('Black', 'Unknown')}")

            st.markdown("**Game Info**")
            st.write(f"Result: {headers.get('Result', 'Unknown')}")
            st.write(f"Date: {headers.get('Date', 'Unknown')}")

        with col2:
            st.markdown("**Opening**")
            st.write(f"Opening: {headers.get('Opening', 'Unknown')}")
            st.write(f"ECO: {headers.get('ECO', 'Unknown')}")

            st.markdown("**Event**")
            st.write(f"Event: {headers.get('Event', 'Unknown')}")
            st.write(f"Site: {headers.get('Site', 'Unknown')}")

    def display_move_list(self, game: chess.pgn.Game, current_move: int = 0) -> None:
        """Display a formatted move list"""

        moves = []
        board = chess.Board()
        move_number = 1

        for node in game.mainline():
            if node.move:
                san = board.san(node.move)

                if board.turn == chess.WHITE:  # This was a black move
                    moves.append({
                        'Move': move_number,
                        'White': moves[-1]['White'] if moves else '',
                        'Black': san
                    })
                    move_number += 1
                else:  # This was a white move
                    moves.append({
                        'Move': move_number,
                        'White': san,
                        'Black': ''
                    })

                board.push(node.move)

        if moves:
            df = pd.DataFrame(moves)

            # Highlight current move
            if current_move > 0:
                current_row = (current_move - 1) // 2

                def highlight_current_move(row):
                    if row.name == current_row:
                        return ['background-color: #ffff99'] * len(row)
                    return [''] * len(row)

                styled_df = df.style.apply(highlight_current_move, axis=1)
                st.dataframe(styled_df, use_container_width=True,
                             hide_index=True)
            else:
                st.dataframe(df, use_container_width=True, hide_index=True)

    def display_analysis_chart(self, evaluations: List[float], title: str = "Position Evaluation"):
        """Display a chart of position evaluations"""

        if not evaluations:
            st.info("No evaluation data available")
            return

        import plotly.graph_objects as go

        fig = go.Figure()

        fig.add_trace(go.Scatter(
            x=list(range(len(evaluations))),
            y=evaluations,
            mode='lines+markers',
            name='Evaluation',
            line=dict(color='blue', width=2),
            marker=dict(size=4)
        ))

        fig.update_layout(
            title=title,
            xaxis_title="Move Number",
            yaxis_title="Evaluation (pawns)",
            hovermode='x unified',
            height=400
        )

        # Add horizontal line at 0
        fig.add_hline(y=0, line_dash="dash", line_color="gray")

        st.plotly_chart(fig, use_container_width=True)

    def display_model_comparison_table(self, comparison_data: Dict[str, Any]):
        """Display a comparison table between two models"""

        model1 = comparison_data.get('model1', 'Model 1')
        model2 = comparison_data.get('model2', 'Model 2')

        # Head-to-head record
        st.markdown("### Head-to-Head Record")

        col1, col2, col3 = st.columns(3)

        with col1:
            st.metric(
                f"{model1} Wins",
                comparison_data.get('model1_wins', 0),
                delta=None
            )

        with col2:
            st.metric(
                "Draws",
                comparison_data.get('draws', 0),
                delta=None
            )

        with col3:
            st.metric(
                f"{model2} Wins",
                comparison_data.get('model2_wins', 0),
                delta=None
            )

        # Performance metrics
        st.markdown("### Performance Metrics")

        metrics_data = {
            'Metric': [
                'Average Accuracy (%)',
                'Average Moves per Game',
                'Error Rate (%)',
                'Average Time per Move (s)'
            ],
            model1: [
                f"{comparison_data.get('model1_accuracy', 0):.1f}",
                f"{comparison_data.get('model1_avg_moves', 0):.1f}",
                f"{comparison_data.get('model1_error_rate', 0):.1f}",
                f"{comparison_data.get('model1_avg_time', 0):.1f}"
            ],
            model2: [
                f"{comparison_data.get('model2_accuracy', 0):.1f}",
                f"{comparison_data.get('model2_avg_moves', 0):.1f}",
                f"{comparison_data.get('model2_error_rate', 0):.1f}",
                f"{comparison_data.get('model2_avg_time', 0):.1f}"
            ]
        }

        df = pd.DataFrame(metrics_data)
        st.dataframe(df, use_container_width=True, hide_index=True)

    def display_tournament_bracket(self, tournament_data: Dict[str, Any]):
        """Display a tournament bracket"""

        participants = tournament_data.get('participants', [])
        results = tournament_data.get('results', [])

        st.markdown("### Tournament Participants")

        # Display participants in a grid
        cols = st.columns(min(4, len(participants)))

        for i, participant in enumerate(participants):
            with cols[i % len(cols)]:
                st.markdown(f"**{participant}**")

                # Show participant stats if available
                participant_results = [r for r in results if r.get(
                    'white') == participant or r.get('black') == participant]

                if participant_results:
                    wins = sum(1 for r in participant_results if
                               (r.get('white') == participant and r.get('result') == '1-0') or
                               (r.get('black') == participant and r.get('result') == '0-1'))

                    st.write(f"Wins: {wins}")
                    st.write(f"Games: {len(participant_results)}")

        # Display results table
        if results:
            st.markdown("### Tournament Results")

            results_df = pd.DataFrame(results)
            st.dataframe(results_df, use_container_width=True)

    def display_elo_chart(self, elo_data: List[Dict[str, Any]]):
        """Display ELO rating progression chart"""

        if not elo_data:
            st.info("No ELO data available")
            return

        import plotly.express as px

        df = pd.DataFrame(elo_data)

        fig = px.line(
            df,
            x='date',
            y='elo',
            color='model',
            title='ELO Rating Progression',
            markers=True
        )

        fig.update_layout(
            xaxis_title="Date",
            yaxis_title="ELO Rating",
            hovermode='x unified',
            height=500
        )

        st.plotly_chart(fig, use_container_width=True)

    def display_opening_stats(self, opening_data: List[Dict[str, Any]]):
        """Display opening statistics"""

        if not opening_data:
            st.info("No opening data available")
            return

        df = pd.DataFrame(opening_data)

        # Sort by games played
        df = df.sort_values('games_played', ascending=False)

        st.dataframe(
            df,
            column_config={
                'opening': 'Opening',
                'games_played': 'Games',
                'win_rate': st.column_config.ProgressColumn(
                    'Win Rate',
                    min_value=0,
                    max_value=1,
                    format="%.1f%%"
                ),
                'avg_accuracy': 'Avg Accuracy (%)',
                'avg_game_length': 'Avg Length'
            },
            use_container_width=True,
            hide_index=True
        )

    def display_game_status(self, status: str, details: Dict[str, Any] = None):
        """Display game status with appropriate styling"""

        if status == "playing":
            st.markdown(
                f"""
                <div style="background: #d4edda; color: #155724; padding: 15px; 
                           border-radius: 10px; border: 1px solid #c3e6cb; 
                           text-align: center; font-weight: bold; margin: 10px 0;">
                    🎮 Game in Progress
                    {f"<br>{details.get('info', '')}" if details and details.get('info') else ""}
                </div>
                """,
                unsafe_allow_html=True
            )

        elif status == "finished":
            result = details.get('result', 'Unknown') if details else 'Unknown'
            st.markdown(
                f"""
                <div style="background: #f8d7da; color: #721c24; padding: 15px; 
                           border-radius: 10px; border: 1px solid #f5c6cb; 
                           text-align: center; font-weight: bold; margin: 10px 0;">
                    🏁 Game Finished - Result: {result}
                </div>
                """,
                unsafe_allow_html=True
            )

        elif status == "error":
            error_msg = details.get(
                'error', 'Unknown error') if details else 'Unknown error'
            st.markdown(
                f"""
                <div style="background: #f8d7da; color: #721c24; padding: 15px; 
                           border-radius: 10px; border: 1px solid #f5c6cb; 
                           text-align: center; font-weight: bold; margin: 10px 0;">
                    ❌ Error: {error_msg}
                </div>
                """,
                unsafe_allow_html=True
            )

    def create_model_selection_widget(self, available_models: List[str],
                                      key: str, label: str = "Select Model") -> str:
        """Create a model selection widget with status indicators"""

        # Add status indicators to model names
        model_options = []
        for model in available_models:
            # You could add status checking here
            status_icon = "🟢"  # Assume available for now
            model_options.append(f"{status_icon} {model}")

        selected = st.selectbox(label, model_options, key=key)

        # Extract model name without status icon
        if selected:
            return selected.split(" ", 1)[1]
        return ""
