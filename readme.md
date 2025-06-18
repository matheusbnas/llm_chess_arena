# LLM Chess Arena

<img src="./images/video.gif"/>

Este é o código fonte do projeto apresentado neste vídeo:
<br>
https://www.instagram.com/reel/C8Ndmh2OAze/

Este projeto permite que diferentes LLMs (Modelos de Linguagem de Grande Porte) joguem partidas de xadrez entre si, possibilitando uma análise comparativa entre modelos de diferentes provedores (OpenAI, DeepSeek, Gemini). O histórico das partidas é salvo em arquivos PGN, organizados por confronto.

## Modelos Suportados

- **OpenAI**: GPT-4o, GPT-4-Turbo, GPT-3.5-Turbo
- **DeepSeek**: Deepseek-Chat, Deepseek-Coder
- **Gemini**: Gemini-Pro (1.5), Gemini-1.0-Pro

Você pode escolher qualquer combinação de modelos para jogar entre si, editando as variáveis `white_player` e `black_player` no início do arquivo `chess_arena_with_judge.py`.

## Como Rodar?

1. Clone o projeto.
2. Crie chaves de acesso para cada provedor de modelo que deseja usar.
3. Na pasta do projeto, crie um arquivo chamado `.env` com o seguinte formato (adicione as chaves que for utilizar):

```
GOOGLE_API_KEY=sua-chave
OPENAI_API_KEY=sua-chave
DEEPSEEK_API_KEY=sua-chave
GROQ_API_KEY=sua-chave
```

4. Instale as dependências:

```bash
pip install -r requirements.txt
```

5. Edite o arquivo `chess_arena_with_judge.py` para escolher os modelos desejados:

```python
white_player = "GPT-4-Turbo"  # ou "Gemini-Pro", "Deepseek-Chat", etc.
black_player = "Gemini-1.0-Pro"
```

6. Execute o script para gerar as partidas:

```bash
python chess_arena_with_judge.py
```

Os arquivos PGN das partidas serão salvos em pastas nomeadas conforme o confronto (ex: `GPT-4-Turbo vs Gemini-1.0-Pro`).

## Dashboard de Comparação

Você pode visualizar e comparar as partidas e estatísticas usando o dashboard interativo:

```bash
streamlit run chess_comparator.py
```

O dashboard permite navegar pelas partidas, ver os lances, comentários e estatísticas de vitórias/empates/derrotas entre os modelos.

---

Dúvidas ou sugestões? Entre em contato!
