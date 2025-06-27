import streamlit as st
import chess
import chess.pgn
import os
from io import StringIO


def initialize_human_game(opponent_model, player_color, difficulty, time_control):
    st.session_state.human_game = {
        'opponent': opponent_model,
        'player_color': player_color,
        'difficulty': difficulty,
        'time_control': time_control,
        'board': chess.Board(),
        'move_history': [],
        'pgn_game': chess.pgn.Game(),
        'current_node': None
    }
    st.session_state.human_game['current_node'] = st.session_state.human_game['pgn_game']


def save_human_game():
    game = st.session_state.human_game.get('pgn_game')
    if not game:
        st.error("Nenhuma partida para salvar.")
        return
    folder_name = "Human_vs_LLM"
    if not os.path.exists(folder_name):
        os.makedirs(folder_name)
    game_num = len(os.listdir(folder_name)) + 1
    game.headers["White"] = "Humano" if st.session_state.human_game['player_color'] == "Brancas" else st.session_state.human_game['opponent']
    game.headers["Black"] = st.session_state.human_game['opponent'] if st.session_state.human_game['player_color'] == "Brancas" else "Humano"
    game.headers["Result"] = st.session_state.human_game['board'].result()
    with open(f"{folder_name}/{game_num}_game.pgn", "w", encoding="utf-8") as f:
        f.write(str(game))
    st.success(f"Partida salva em {folder_name}/{game_num}_game.pgn")


def show_ai_hint():
    st.info("Stub: mostrar dica da IA.")
    # TODO: implementar lógica de dica da IA
    pass


def make_human_move(move_input, human_explanation=None):
    game = st.session_state.human_game
    board = game['board']
    try:
        move = board.parse_san(move_input)
        from_square = move.from_square
        to_square = move.to_square
        board.push(move)
        # Atualiza PGN
        node = game['current_node'].add_variation(move)
        if human_explanation:
            node.comment = human_explanation
        game['current_node'] = node
        # Salva histórico
        game['move_history'].append({
            'move': move_input,
            'by': 'human',
            'from_square': from_square,
            'to_square': to_square,
            'explanation': human_explanation
        })
        st.session_state.human_game = game
    except Exception as e:
        st.error(f"Lance inválido: {e}")


def make_ai_move(opponent, model_manager, game_engine):
    game = st.session_state.human_game
    board = game['board']
    color = 'white' if (game['player_color'] == 'Pretas') else 'black'
    model_name = opponent
    # Chama o motor para obter o lance e explicação
    # Aqui você deve adaptar para usar seu modelo LLM real
    # Exemplo fictício:
    move, explanation = get_llm_move_with_explanation(board, model_name, color)
    if move:
        from_square = move.from_square
        to_square = move.to_square
        move_san = board.san(move)  # Pegue a SAN ANTES do push!
        board.push(move)
        # Atualiza PGN
        node = game['current_node'].add_variation(move)
        node.comment = explanation
        game['current_node'] = node
        # Salva histórico
        game['move_history'].append({
            'move': move_san,
            'by': 'llm',
            'from_square': from_square,
            'to_square': to_square,
            'explanation': explanation
        })
        st.session_state.human_game = game
        return explanation
    else:
        st.error("A LLM não conseguiu gerar um lance válido.")
        return None


def get_llm_move_with_explanation(board, model_name, color):
    # Monte o contexto do tabuleiro, histórico, etc.
    context = montar_contexto_para_llm(board, color)
    # Chame a LLM (pode ser via API, LangChain, etc.)
    resposta = chamar_llm(context, model_name)
    resposta_texto = resposta.content.strip()  # ou resposta["text"].strip()
    # Extraia o lance e a explicação da resposta da LLM
    move = extrair_move_da_resposta(resposta_texto, board)
    explicacao = extrair_explicacao_da_resposta(resposta_texto)
    return move, explicacao


def montar_contexto_para_llm(board, color):
    """
    Monta o contexto para enviar à LLM: histórico de lances e posição atual.
    """
    import chess.pgn
    import io

    # Cria um objeto PGN temporário para extrair o histórico
    game = chess.pgn.Game.from_board(board)
    pgn_io = io.StringIO()
    print(game, file=pgn_io, end="\n")
    history = pgn_io.getvalue()

    # Remove cabeçalhos do PGN, deixa só os lances
    moves_section = history.split("\n\n", 1)[-1].strip()

    # Estado do tabuleiro em ASCII
    board_ascii = str(board)

    contexto = (
        f"Você está jogando com as peças {color}.\n"
        f"Histórico de lances:\n{moves_section}\n\n"
        f"Posição atual do tabuleiro:\n{board_ascii}\n"
    )
    return contexto


def chamar_llm(context, model_name):
    """
    Chama o modelo LLM para obter uma resposta.
    """
    from src.models import ModelManager
    from langchain_core.messages import HumanMessage

    model_manager = ModelManager()
    model = model_manager.get_model(model_name)
    
    # Usando o formato de mensagem para a invocação do modelo
    message = HumanMessage(content=context)
    response = model.invoke([message])
    
    return response


def extrair_move_da_resposta(resposta_texto, board):
    """
    Extrai o lance da resposta da LLM.
    Procura por padrões comuns como "My move: e4" ou simplesmente um lance válido.
    """
    import re
    
    # Lista de movimentos válidos no formato SAN
    movimentos_validos = [board.san(move) for move in board.legal_moves]
    
    # Padrões para encontrar o lance na resposta
    padroes = [
        r'My move: "([^"]+)"',  # Formato padrão do prompt: My move: "e4"
        r'My move: ([a-zA-Z0-9\+\-\=\#]+)',  # My move: e4
        r'move: ([a-zA-Z0-9\+\-\=\#]+)',  # move: e4
        r'lance: ([a-zA-Z0-9\+\-\=\#]+)',  # lance: e4 (versão em português)
        r'\b([a-zA-Z][a-zA-Z0-9\+\-\=\#]{1,7})\b'  # Qualquer texto que pareça um lance: e4, Nf3, O-O, etc.
    ]
    
    # Tenta encontrar o lance usando os padrões
    for padrao in padroes:
        matches = re.findall(padrao, resposta_texto)
        for match in matches:
            # Verifica se o texto encontrado é um lance válido
            if match in movimentos_validos:
                try:
                    return board.parse_san(match)
                except ValueError:
                    continue
    
    # Se não encontrou um lance válido, tenta extrair qualquer coisa que pareça um lance
    # e verifica se é válido
    palavras = re.findall(r'\b([a-zA-Z][a-zA-Z0-9\+\-\=\#]{1,7})\b', resposta_texto)
    for palavra in palavras:
        try:
            move = board.parse_san(palavra)
            return move
        except ValueError:
            continue
    
    # Se chegamos aqui, não encontramos um lance válido
    return None


def extrair_explicacao_da_resposta(resposta_texto):
    """
    Extrai a explicação da resposta da LLM.
    Basicamente, remove a parte do lance e retorna o resto como explicação.
    """
    import re
    
    # Remove padrões comuns de lance
    explicacao = resposta_texto
    padroes_lance = [
        r'My move: "([^"]+)"',
        r'My move: ([a-zA-Z0-9\+\-\=\#]+)',
        r'move: ([a-zA-Z0-9\+\-\=\#]+)',
        r'lance: ([a-zA-Z0-9\+\-\=\#]+)'
    ]
    
    for padrao in padroes_lance:
        explicacao = re.sub(padrao, '', explicacao, flags=re.IGNORECASE)
    
    # Limpa a explicação: remove linhas vazias e espaços extras
    linhas = [linha.strip() for linha in explicacao.split('\n') if linha.strip()]
    explicacao = ' '.join(linhas)
    
    # Se a explicação estiver vazia, retorna um valor padrão
    if not explicacao:
        return "Movimento estratégico escolhido pelo modelo."
    
    return explicacao
