import streamlit as st
import os
import json
from datetime import datetime


def get_secret_or_env(key):
    # Prioriza st.secrets, depois getenv
    try:
        return st.secrets[key]
    except Exception:
        return os.getenv(key, "")


def read_env_keys(keys):
    # Caminho absoluto para o .env na raiz do1 projeto
    env_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '.env'))
    env_vars = {k: "" for k in keys}
    try:
        with open(env_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                if "=" in line:
                    k, v = line.split("=", 1)
                    k = k.strip().replace(" ", "")
                    v = v.strip().strip('"').strip("'")
                    if k in env_vars:
                        env_vars[k] = v
    except Exception:
        pass
    return env_vars


def save_temp_env_keys(keys_dict):
    """Salva as chaves em um arquivo .env.temp oculto na raiz do projeto."""
    env_temp_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '.env.temp'))
    with open(env_temp_path, "w", encoding="utf-8") as f:
        for k, v in keys_dict.items():
            f.write(f"{k}={v}\n")


def get_env_var_prioritized(key):
    """Prioriza .env.temp, depois .env, depois variável de ambiente."""
    env_temp_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '.env.temp'))
    if os.path.exists(env_temp_path):
        with open(env_temp_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                if "=" in line:
                    k, v = line.split("=", 1)
                    if k.strip().replace(" ", "") == key:
                        return v.strip().strip('"').strip("'")
    # Fallback para o método antigo
    return get_secret_or_env(key) or read_env_keys([key]).get(key, "")


def show_settings(model_manager, lichess_api, db):
    st.markdown("## ⚙️ Configurações")

    # Flag para mostrar ou ocultar a aba de jogo
    SHOW_GAME_TAB = False  # Altere para True se quiser mostrar

    # Monta as abas dinamicamente
    tab_labels = ["🤖 Modelos", "🌐 APIs", "💾 Dados"]
    if SHOW_GAME_TAB:
        tab_labels.insert(2, "🎮 Jogo")
    tabs = st.tabs(tab_labels)

    tab1 = tabs[0]
    tab2 = tabs[1]
    if SHOW_GAME_TAB:
        tab3 = tabs[2]
        tab4 = tabs[3]
    else:
        tab3 = None
        tab4 = tabs[2]

    # --- LEITURA DAS CHAVES ---
    model_keys = [
        "OPENAI_API_KEY",
        "GOOGLE_API_KEY",
        "DEEPSEEK_API_KEY",
        "GROQ_API_KEY",
        "CLAUDE_API_KEY"
    ]
    # Prioriza secrets, depois .env, depois getenv
    env_keys = {k: get_secret_or_env(k) for k in model_keys}
    if not any(env_keys.values()):
        env_keys = read_env_keys(model_keys)

    with tab1:
        st.markdown("### 🤖 Configuração dos Modelos")
        st.markdown("#### 🔑 Chaves de API")

        openai_key = st.text_input(
            "OpenAI API Key:",
            type="password",
            value=env_keys["OPENAI_API_KEY"],
            key="openai_key"
        )
        google_key = st.text_input(
            "Google API Key:",
            type="password",
            value=env_keys["GOOGLE_API_KEY"],
            key="google_key"
        )
        deepseek_key = st.text_input(
            "DeepSeek API Key:",
            type="password",
            value=env_keys["DEEPSEEK_API_KEY"],
            key="deepseek_key"
        )
        groq_key = st.text_input(
            "Groq API Key:",
            type="password",
            value=env_keys["GROQ_API_KEY"],
            key="groq_key"
        )
        claude_key = st.text_input(
            "Claude API Key:",
            type="password",
            value=env_keys["CLAUDE_API_KEY"],
            key="claude_key"
        )

        st.info("As chaves são lidas automaticamente do ambiente, secrets ou do arquivo .env. Não são salvas pelo dashboard.")

        st.markdown("#### Status das Chaves de API:")
        for k, v in env_keys.items():
            if v:
                st.success(f"{k}: ✅ Presente")
            else:
                st.warning(f"{k}: ❌ Ausente")

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
                    st.success(
                        f"✅ Modelo {test_model} funcionando corretamente!")
                    st.info(
                        f"Tempo de resposta: {test_result['response_time']:.2f}s")
                else:
                    st.error(
                        f"❌ Erro no modelo {test_model}: {test_result['error']}")

        # Botão para salvar as chaves temporariamente
        if st.button("💾 Salvar Chaves Temporariamente"):
            # Recupera o token do Lichess já salvo, se existir
            env_temp_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '.env.temp'))
            lichess_token = ""
            if os.path.exists(env_temp_path):
                with open(env_temp_path, "r", encoding="utf-8") as f:
                    for line in f:
                        if line.startswith("LICHESS_API_TOKEN="):
                            lichess_token = line.split("=", 1)[1].strip().strip('"').strip("'")
                            break
            temp_keys = {
                "OPENAI_API_KEY": openai_key,
                "GOOGLE_API_KEY": google_key,
                "DEEPSEEK_API_KEY": deepseek_key,
                "GROQ_API_KEY": groq_key,
                "CLAUDE_API_KEY": claude_key,
            }
            if lichess_token:
                temp_keys["LICHESS_API_TOKEN"] = lichess_token
            save_temp_env_keys(temp_keys)
            st.success("Chaves salvas temporariamente! Reinicie a página para recarregar os modelos.")

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
                    # Salva a chave do Lichess no .env.temp junto com as outras
                    temp_keys = {
                        "OPENAI_API_KEY": openai_key,
                        "GOOGLE_API_KEY": google_key,
                        "DEEPSEEK_API_KEY": deepseek_key,
                        "GROQ_API_KEY": groq_key,
                        "CLAUDE_API_KEY": claude_key,
                        "LICHESS_API_TOKEN": lichess_token,
                    }
                    save_temp_env_keys(temp_keys)
                    st.success("✅ Conectado ao Lichess com sucesso! Token salvo temporariamente.")
                else:
                    st.error("❌ Erro na conexão com o Lichess. Verifique o token.")
            else:
                st.warning("⚠️ Insira um token válido.")

    if SHOW_GAME_TAB and tab3:
        with tab3:
            st.markdown("### 🎮 Configurações de Jogo")
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
            st.markdown("#### 📊 Configurações de Análise")
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

        # Recalculate stats and ELO, and sincronize with filesystem
        if st.button("Atualizar banco de dados (sincronizar arquivos e recalcular estatísticas/ELO)"):
            # Caminho raiz do projeto (ajuste se necessário)
            root_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
            total_imported = db.sync_filesystem_and_database(root_path=root_path)
            db.fill_opening_and_analysis()
            db.update_avg_accuracy()
            st.success(
                f"Banco de dados atualizado! {total_imported} partidas importadas dos arquivos .pgn. "
                "Estatísticas, ELO, aberturas e análises recalculados."
            )

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
                    db.fill_opening_and_analysis()
                    db.update_avg_accuracy()
                    st.success("✅ Dados importados e campos recalculados com sucesso!")
                else:
                    st.error("❌ Erro ao importar dados.")
            except Exception as e:
                st.error(f"❌ Erro ao processar arquivo: {str(e)}")

        # Clear data
        st.markdown("#### 🗑️ Limpeza de Dados")
        st.warning("⚠️ Atenção: As operações abaixo são irreversíveis!")
        if st.button("💥 Resetar Banco de Dados", type="secondary"):
            if st.checkbox("Confirmo que quero resetar TODOS os dados"):
                if st.text_input("Digite 'CONFIRMAR' para prosseguir:") == "CONFIRMAR":
                    db.reset_database()
                    db.fill_opening_and_analysis()
                    db.update_avg_accuracy()
                    st.success("✅ Banco de dados resetado e campos recalculados com sucesso! Estrutura atualizada.")
                    st.info("🔄 Reinicie a aplicação para garantir que todas as alterações de estrutura sejam aplicadas.")
