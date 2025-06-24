import os
import chess.pgn
from typing import List, Dict

PGN_FOLDERS = [
    "Gemini-Pro vs GPT-4o",
    "gpt-4 vs Deepseek",
    "GPT-4o vs Gemini-Pro"
]


def import_all_pgn_games(base_path: str) -> List[Dict]:
    """
    Varre as subpastas de PGN e importa todas as partidas.
    Retorna uma lista de dicts com 'game', 'file', 'folder', 'index'.
    """
    games = []
    for folder in PGN_FOLDERS:
        folder_path = os.path.join(base_path, folder)
        if not os.path.exists(folder_path):
            continue
        for fname in os.listdir(folder_path):
            if fname.endswith('.pgn'):
                file_path = os.path.join(folder_path, fname)
                with open(file_path, 'r', encoding='utf-8') as f:
                    pgn_text = f.read()
                pgn_io = chess.pgn.StringIO(pgn_text)
                idx = 0
                while True:
                    game = chess.pgn.read_game(pgn_io)
                    if game is None:
                        break
                    games.append({
                        'game': game,
                        'file': fname,
                        'folder': folder,
                        'index': idx
                    })
                    idx += 1
    return games
