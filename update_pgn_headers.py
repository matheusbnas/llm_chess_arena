import os
import re
from datetime import datetime
import chess.pgn

def update_pgn_headers(directory):
    """
    Update PGN files in the given directory and all subdirectories to ensure 
    they have correct Event, Date, and Round headers.
    """
    # Get current date in PGN format (YYYY.MM.DD)
    today = datetime.now().strftime("%Y.%m.%d")
    
    # Count of updated files
    updated_count = 0
    error_count = 0
    
    # Walk through all directories
    for root, dirs, files in os.walk(directory):
        for file in files:
            if file.endswith('.pgn'):
                filepath = os.path.join(root, file)
                
                # Extract round number from filename (e.g., 1_game.pgn -> 1)
                round_number = None
                filename_match = re.match(r'(\d+)_game\.pgn', file)
                if filename_match:
                    round_number = filename_match.group(1)
                
                # Try different encodings to read the file
                content = None
                encodings = ['utf-8', 'latin-1', 'windows-1252', 'iso-8859-1']
                
                for encoding in encodings:
                    try:
                        with open(filepath, 'r', encoding=encoding) as f:
                            content = f.read()
                        break  # If successful, break the loop
                    except UnicodeDecodeError:
                        continue  # Try the next encoding
                
                if content is None:
                    print(f"Error: Could not decode {filepath} with any of the attempted encodings")
                    error_count += 1
                    continue  # Skip this file
                
                modified = False
                
                # Check and update Event tag
                if '[Event ' not in content or '[Event "?"]' in content:
                    # Replace existing Event tag or add a new one
                    if '[Event ' in content:
                        content = re.sub(r'\[Event "[^"]*"\]', '[Event "LLM Chess Arena"]', content)
                    else:
                        # Add Event tag at the beginning
                        content = '[Event "LLM Chess Arena"]\n' + content
                    modified = True
                
                # Check and update Date tag
                if '[Date ' not in content or '[Date "????.??.??"]' in content or '[Date "?"]' in content:
                    # Replace existing Date tag or add a new one
                    if '[Date ' in content:
                        content = re.sub(r'\[Date "[^"]*"\]', f'[Date "{today}"]', content)
                    else:
                        # Add Date tag after Event or at the beginning
                        if '[Event ' in content:
                            content = content.replace('[Event "LLM Chess Arena"]', 
                                                      f'[Event "LLM Chess Arena"]\n[Date "{today}"]')
                        else:
                            content = f'[Date "{today}"]\n' + content
                    modified = True
                
                # Check and update Round tag if round_number was extracted
                if round_number and ('[Round ' not in content or '[Round "?"]' in content):
                    # Replace existing Round tag or add a new one
                    if '[Round ' in content:
                        content = re.sub(r'\[Round "[^"]*"\]', f'[Round "{round_number}"]', content)
                    else:
                        # Add Round tag after Date or Event tag
                        if '[Date ' in content:
                            content = content.replace(f'[Date "{today}"]', 
                                                     f'[Date "{today}"]\n[Round "{round_number}"]')
                        elif '[Event ' in content:
                            content = content.replace('[Event "LLM Chess Arena"]', 
                                                     f'[Event "LLM Chess Arena"]\n[Round "{round_number}"]')
                        else:
                            content = f'[Round "{round_number}"]\n' + content
                    modified = True
                
                # Write updated content back if modified
                if modified:
                    try:
                        # Use the same encoding that successfully read the file
                        with open(filepath, 'w', encoding=encoding) as f:
                            f.write(content)
                        updated_count += 1
                        print(f"Updated: {filepath}")
                    except Exception as e:
                        print(f"Error writing to {filepath}: {str(e)}")
                        error_count += 1
    
    return updated_count, error_count

if __name__ == "__main__":
    # Base directory - adjust if needed
    base_dir = os.path.dirname(os.path.abspath(__file__))
    
    print(f"Scanning for PGN files in: {base_dir}")
    updated, errors = update_pgn_headers(base_dir)
    print(f"Updated {updated} PGN files with proper Event, Date, and Round headers.")
    if errors > 0:
        print(f"Encountered {errors} errors during processing.")
    
    # Count PGN files
    base_path = os.getcwd()
    pgn_count = 0
    pgn_files = []

    for root, dirs, files in os.walk(base_path):
        for file in files:
            if file.endswith('.pgn'):
                pgn_count += 1
                pgn_files.append(os.path.join(root, file))

    print(f"Total PGN files found: {pgn_count}")
    for path in pgn_files:
        print(path)
    
    # Count total number of games in all PGN files
    total_games = 0
    for root, dirs, files in os.walk(base_path):
        for file in files:
            if file.endswith('.pgn'):
                file_path = os.path.join(root, file)
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    while True:
                        game = chess.pgn.read_game(f)
                        if game is None:
                            break
                        total_games += 1

    print(f"Total de partidas (jogos) em todos os arquivos .pgn: {total_games}")