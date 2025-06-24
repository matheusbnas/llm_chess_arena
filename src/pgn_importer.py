import os
import chess.pgn
from typing import List, Dict
import hashlib
from io import StringIO
import sqlite3

PGN_FOLDERS = [
    "Gemini-Pro vs GPT-4o",
    "gpt-4 vs Deepseek",
    "GPT-4o vs Gemini-Pro"
]


def read_pgn_file(file_path):
    """Tenta ler o arquivo como utf-8, se falhar tenta latin-1."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()
    except UnicodeDecodeError:
        with open(file_path, 'r', encoding='latin-1') as f:
            return f.read()


def import_all_pgn_games(base_path: str) -> List[Dict]:
    """
    Varre as subpastas de PGN e importa todas as partidas.
    Retorna uma lista de dicts com 'game', 'file', 'folder', 'index', 'pgn'.
    """
    games = []
    for folder in PGN_FOLDERS:
        folder_path = os.path.join(base_path, folder)
        if not os.path.exists(folder_path):
            continue
        for fname in os.listdir(folder_path):
            if fname.endswith('.pgn'):
                file_path = os.path.join(folder_path, fname)
                pgn_text = read_pgn_file(file_path)
                pgn_io = StringIO(pgn_text)
                idx = 0
                while True:
                    game = chess.pgn.read_game(pgn_io)
                    if game is None:
                        break
                    # Extrair o PGN da partida
                    game_pgn = str(game)
                    games.append({
                        'game': game,
                        'file': fname,
                        'folder': folder,
                        'index': idx,
                        'pgn': game_pgn
                    })
                    idx += 1
    return games


def import_pgns_to_db(base_path: str, db) -> int:
    """
    Importa todas as partidas PGN das pastas e salva no banco de dados, evitando duplicatas.
    Usa uma única conexão SQLite para evitar database locked.
    Retorna o número de partidas realmente importadas.
    """
    games = import_all_pgn_games(base_path)
    count = 0
    db_path = getattr(db, 'db_path', 'chess_arena.db')
    import json
    from datetime import datetime
    import time
    # Buscar todos os PGNs já salvos
    existing_pgns = set()
    with sqlite3.connect(db_path, timeout=30) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT pgn FROM games")
        for row in cursor.fetchall():
            existing_pgns.add(hashlib.sha256(
                row[0].encode('utf-8')).hexdigest())
        for g in games:
            pgn_hash = hashlib.sha256(g['pgn'].encode('utf-8')).hexdigest()
            if pgn_hash in existing_pgns:
                continue
            headers = g['game'].headers
            cursor.execute("""
                INSERT INTO games (white, black, result, pgn, moves, opening, date, tournament_id, analysis_data, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                headers.get('White', 'Unknown'),
                headers.get('Black', 'Unknown'),
                headers.get('Result', ''),
                g['pgn'],
                len(list(g['game'].mainline_moves())),
                headers.get('Opening', ''),
                headers.get('Date', ''),
                None,
                json.dumps({}),
                datetime.now().isoformat()
            ))
            count += 1
            # Pequeno delay para evitar lock em grandes lotes
            if count % 100 == 0:
                time.sleep(0.1)
        conn.commit()
    return count
