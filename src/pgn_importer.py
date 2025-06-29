import os
import chess.pgn
from typing import List, Dict
import hashlib
from io import StringIO
import sqlite3


def get_pgn_folders(base_path: str) -> List[str]:
    """
    Identifica dinamicamente todas as pastas que contêm arquivos PGN.
    Retorna uma lista com os nomes das pastas.
    """
    pgn_folders = []
    
    # Lista todos os itens no diretório base
    for item in os.listdir(base_path):
        item_path = os.path.join(base_path, item)
        
        # Verifica se é um diretório
        if os.path.isdir(item_path):
            # Verifica se o diretório contém arquivos PGN
            has_pgn = False
            for filename in os.listdir(item_path):
                if filename.endswith('.pgn'):
                    has_pgn = True
                    break
            
            if has_pgn:
                pgn_folders.append(item)
    
    return pgn_folders


def read_pgn_file(file_path):
    """Tenta ler o arquivo como utf-8, se falhar tenta latin-1."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()
    except UnicodeDecodeError:
        try:
            with open(file_path, 'r', encoding='latin-1') as f:
                return f.read()
        except Exception as e:
            print(f"Error reading file {file_path}: {e}")
            return ""


def import_all_pgn_games(base_path: str) -> List[Dict]:
    """
    Varre as subpastas de PGN e importa todas as partidas.
    Retorna uma lista de dicts com 'game', 'file', 'folder', 'index', 'pgn'.
    """
    games = []
    pgn_folders = get_pgn_folders(base_path)
    
    for folder in pgn_folders:
        folder_path = os.path.join(base_path, folder)
        for fname in os.listdir(folder_path):
            if fname.endswith('.pgn'):
                file_path = os.path.join(folder_path, fname)
                pgn_text = read_pgn_file(file_path)
                if not pgn_text:
                    continue
                    
                pgn_io = StringIO(pgn_text)
                idx = 0
                while True:
                    try:
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
                    except Exception as e:
                        print(f"Error processing game in {file_path}: {e}")
                        break
    return games


def import_pgns_to_db(base_path: str, db) -> int:
    """
    Importa todas as partidas PGN das pastas e salva no banco de dados, evitando duplicatas
    usando file_name e folder_name.
    """
    games = import_all_pgn_games(base_path)
    count = 0
    db_path = getattr(db, 'db_path', 'chess_arena.db')
    import json
    from datetime import datetime
    import time

    with sqlite3.connect(db_path, timeout=30) as conn:
        cursor = conn.cursor()
        for g in games:
            # Checa se já existe pelo nome do arquivo e pasta
            cursor.execute(
                "SELECT 1 FROM games WHERE file_name=? AND folder_name=?",
                (g['file'], g['folder'])
            )
            if cursor.fetchone():
                continue  # já existe, pula

            headers = g['game'].headers
            cursor.execute("""
                INSERT INTO games (
                    white, black, result, pgn, moves, opening, date, tournament_id, analysis_data, created_at, file_name, folder_name
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
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
                datetime.now().isoformat(),
                g['file'],
                g['folder']
            ))
            count += 1
            # Pequeno delay para evitar lock em grandes lotes
            if count % 100 == 0:
                time.sleep(0.1)
        conn.commit()
    return count
