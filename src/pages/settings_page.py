import streamlit as st
import os
import json
from datetime import datetime
from src.models import ModelManager   

def get_secret_or_env(key):
    # Prioriza st.secrets, depois getenv
    try:
        return st.secrets[key]
    except Exception:
        return os.getenv(key, "")

def read_env_keys(keys):
    # Caminho absoluto para o .env na raiz do projeto
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
    """Salva as chaves em um arquivo .env.temp oculto na raiz do projeto (apenas local)."""
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


def get_api_key_from_all_sources(input_value, key):
    """
    Prioridade:
    1. Valor digitado no input (input_value)
    2. st.secrets (secrets.toml do Streamlit Cloud)
    3. .env (apenas local)
    """
    if input_value:
        return input_value
    try:
        return st.secrets[key]
    except Exception:
        pass
    # Busca no .env local
    env_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '.env'))
    if os.path.exists(env_path):
        with open(env_path, "r", encoding="utf-8") as f:
            for line in f:
                if line.strip().startswith(f"{key}="):
                    return line.strip().split("=", 1)[1].strip().strip('"').strip("'")
    return ""


def show_settings(model_manager, lichess_api, db):
    st.markdown("## ⚙️ Configurações")

    # Inicializa o estado da sessão para as chaves de API se não existir
    if 'api_keys' not in st.session_state:
        st.session_state.api_keys = {}

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

    # Função auxiliar para obter a chave prioritária
    def get_key_priority(key):
        # 1. Primeiro verifica se tem na session state
        session_value = st.session_state.api_keys.get(key)
        if session_value:
            return session_value
        
        # 2. Depois verifica no secrets.toml
        try:
            secrets_value = st.secrets[key]
            return secrets_value
        except Exception:
            pass
        
        # 3. Depois verifica no .env
        env_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '.env'))
        env_value = ""
        try:
            with open(env_path, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line.startswith(key + "="):
                        env_value = line.split("=")[1].strip().strip('"').strip("'")
                        break
            if env_value:
                return env_value
        except Exception:
            pass
        
        # 4. Por último verifica no ambiente
        return os.getenv(key, "")

    with tab1:
        st.markdown("### 🤖 Configuração dos Modelos")
        st.markdown("#### 🔑 Chaves de API")

        # Explicação sobre as chaves com informações atualizadas
        st.info("""
        🔒 **Chaves de API Necessárias para Modelos 2025:**

        **🚀 NOVOS MODELOS DISPONÍVEIS:**
        - **OpenAI**: GPT-4.1, GPT-4.1-Mini, GPT-4.1-Nano (mais recentes)
        - **Google**: Gemini 2.5 Flash, Gemini 2.5 Pro, Gemini 2.5 Flash-Lite
        - **Anthropic**: Claude 4 Opus, Claude 4 Sonnet (mais inteligentes)
        - **DeepSeek**: DeepSeek-R1 (raciocínio), DeepSeek-V3 (geral)
        - **Groq**: Llama 3.3-70B, Llama 3.1-8B (mais rápidos)

        **💡 Como obter as chaves:**
        1. 📝 Digite diretamente nos campos abaixo (prioridade máxima)
        2. 🔒 Defina no arquivo `secrets.toml` (Streamlit Cloud)
        3. 📁 Defina no arquivo `.env` local
        4. 🌐 Defina como variáveis de ambiente do sistema

        ⚠️ **Importante:** As chaves digitadas aqui são temporárias durante sua sessão
        """)

        # Inputs para cada chave de API com valores prioritários
        openai_key_input = st.text_input(
            "🔑 OpenAI API Key (GPT-4.1, GPT-4o, GPT-3.5)",
            type="password",
            value=get_key_priority("OPENAI_API_KEY"),
            help="Necessária para GPT-4.1, GPT-4o, GPT-4o-Mini, GPT-3.5-Turbo"
        )
        google_key_input = st.text_input(
            "🔑 Google API Key (Gemini 2.5)",
            type="password",
            value=get_key_priority("GOOGLE_API_KEY"),
            help="Necessária para Gemini 2.5 Flash, Gemini 2.5 Pro, Gemini 1.5 Pro/Flash"
        )
        deepseek_key_input = st.text_input(
            "🔑 DeepSeek API Key (R1, V3)",
            type="password",
            value=get_key_priority("DEEPSEEK_API_KEY"),
            help="Necessária para DeepSeek-R1 (raciocínio), DeepSeek-V3 (geral), DeepSeek-Coder"
        )
        groq_key_input = st.text_input(
            "🔑 Groq API Key (Llama 3.3, Mixtral)",
            type="password",
            value=get_key_priority("GROQ_API_KEY"),
            help="Necessária para Llama 3.3-70B, Llama 3.1-8B, Mixtral-8x7B"
        )
        claude_key_input = st.text_input(
            "🔑 Claude API Key (Claude 4)",
            type="password",
            value=get_key_priority("CLAUDE_API_KEY"),
            help="Necessária para Claude 4 Opus, Claude 4 Sonnet, Claude 3.5 Sonnet/Haiku"
        )

        # Atualiza o estado da sessão quando as chaves são alteradas
        st.session_state.api_keys = {
            "OPENAI_API_KEY": openai_key_input,
            "GOOGLE_API_KEY": google_key_input,
            "DEEPSEEK_API_KEY": deepseek_key_input,
            "GROQ_API_KEY": groq_key_input,
            "CLAUDE_API_KEY": claude_key_input
        }

        # Cria uma nova instância do ModelManager com as chaves da sessão
        model_manager = ModelManager(api_keys=st.session_state.api_keys)

        # Status das chaves com informações sobre os modelos
        st.markdown("#### 📊 Status das Chaves e Modelos Disponíveis:")
        
        # Informações de preços (aproximados)
        pricing_info = {
            "OPENAI_API_KEY": {
                "models": ["GPT-4.1", "GPT-4.1-Mini", "GPT-4o", "GPT-4o-Mini", "GPT-3.5-Turbo"],
                "pricing": "GPT-4.1: $5-20/1M tokens | GPT-4o: $2.50-10/1M | GPT-4o-Mini: $0.15-0.60/1M"
            },
            "GOOGLE_API_KEY": {
                "models": ["Gemini-2.5-Flash", "Gemini-2.5-Pro", "Gemini-1.5-Pro", "Gemini-1.5-Flash"],
                "pricing": "Gemini 2.5 Pro: $1.25-15/1M tokens | Gemini 2.5 Flash: $0.10-0.40/1M"
            },
            "DEEPSEEK_API_KEY": {
                "models": ["DeepSeek-R1", "DeepSeek-V3", "DeepSeek-Coder"],
                "pricing": "DeepSeek-R1: $0.55-2.19/1M tokens | DeepSeek-V3: $0.14-0.28/1M (muito barato!)"
            },
            "GROQ_API_KEY": {
                "models": ["Llama-3.3-70B", "Llama-3.1-8B", "Mixtral-8x7B"],
                "pricing": "Llama 3.3-70B: $0.59-0.79/1M tokens | Llama 3.1-8B: $0.05-0.08/1M (rápido!)"
            },
            "CLAUDE_API_KEY": {
                "models": ["Claude-4-Opus", "Claude-4-Sonnet", "Claude-3.5-Sonnet", "Claude-3.5-Haiku"],
                "pricing": "Claude 4 Opus: $15-75/1M tokens | Claude 4 Sonnet: $3-15/1M"
            }
        }

        for key, info in pricing_info.items():
            value = st.session_state.api_keys.get(key, "")
            if value:
                st.success(f"✅ **{key}**: Presente")
                st.info(f"📋 **Modelos**: {', '.join(info['models'])}")
                st.info(f"💰 **Preços**: {info['pricing']}")
            else:
                st.warning(f"❌ **{key}**: Ausente")
                st.info(f"📋 **Modelos perdidos**: {', '.join(info['models'])}")

        # Recomendações de modelos
        st.markdown("#### 🎯 Recomendações de Modelos para Xadrez:")
        
        recommendations = model_manager.get_recommended_models("chess")
        
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("**🏆 Melhor Performance:**")
            st.code(recommendations["best_performance"])
            st.markdown("**⚖️ Equilibrado:**")
            st.code(recommendations["balanced"])
        
        with col2:
            st.markdown("**💰 Custo-Benefício:**")
            st.code(recommendations["cost_effective"])
            st.markdown("**🧠 Raciocínio:**")
            st.code(recommendations["reasoning"])

        st.markdown("#### 🎛️ Parâmetros dos Modelos")
        
        col1, col2 = st.columns(2)
        with col1:
            temperature = st.slider(
                "Temperatura (criatividade):",
                0.0, 2.0, 0.1, 0.1,
                help="Valores mais altos tornam as respostas mais criativas"
            )
            max_tokens = st.slider(
                "Máximo de tokens:",
                100, 8000, 1000, 100,
                help="Limite de tokens para as respostas dos modelos"
            )
        
        with col2:
            thinking_time = st.slider(
                "Tempo de reflexão (segundos):",
                1, 60, 5, 1,
                help="Tempo que o modelo tem para 'pensar' antes de fazer um lance"
            )
            use_reasoning = st.checkbox(
                "Usar modelos de raciocínio",
                value=True,
                help="Ativa o modo de raciocínio avançado para modelos como DeepSeek-R1 e Claude 4"
            )

        # Model testing com informações detalhadas
        st.markdown("#### 🧪 Teste dos Modelos")
        
        available_models = list(model_manager.get_available_models().keys())
        if available_models:
            test_model = st.selectbox(
                "Modelo para teste:",
                available_models,
                key="test_model",
                help="Selecione um modelo para testar sua conectividade e performance"
            )
            
            # Mostra informações do modelo selecionado
            if test_model:
                model_info = model_manager.get_model_info(test_model)
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Provider", model_info.get("provider", "N/A"))
                with col2:
                    st.metric("Nível de Preço", model_info.get("pricing_tier", "N/A"))
                with col3:
                    capabilities = model_info.get("capabilities", [])
                    st.metric("Capacidades", len(capabilities))
                
                if capabilities:
                    st.info(f"🎯 **Capacidades**: {', '.join(capabilities)}")
            
            if st.button("🧪 Testar Modelo Selecionado"):
                with st.spinner(f"Testando {test_model}..."):
                    test_result = model_manager.test_model(test_model)
                    if test_result['success']:
                        st.success(f"✅ Modelo **{test_model}** funcionando corretamente!")
                        st.info(f"⚡ Tempo de resposta: {test_result['response_time']:.2f}s")
                        st.info(f"💬 Resposta: {test_result['response']}")
                    else:
                        st.error(f"❌ Erro no modelo **{test_model}**: {test_result['error']}")
        else:
            st.warning("⚠️ Nenhum modelo disponível. Verifique suas chaves de API.")

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
                "OPENAI_API_KEY": openai_key_input,
                "GOOGLE_API_KEY": google_key_input,
                "DEEPSEEK_API_KEY": deepseek_key_input,
                "GROQ_API_KEY": groq_key_input,
                "CLAUDE_API_KEY": claude_key_input,
            }
            if lichess_token:
                temp_keys["LICHESS_API_TOKEN"] = lichess_token
            
            save_temp_env_keys(temp_keys)
            st.success("✅ Chaves salvas temporariamente! Reinicie a página para recarregar os modelos.")

    with tab2:
        st.markdown("### 🌐 Configuração de APIs")

        # Lichess API
        st.markdown("#### ♟️ Lichess API")
        
        st.info("""
        🔗 **Como obter seu token do Lichess:**
        1. Acesse: https://lichess.org/account/oauth/token
        2. Faça login na sua conta
        3. Clique em "Create a new personal access token"
        4. Dê um nome ao token (ex: "Chess AI Bot")
        5. Selecione os escopos necessários
        6. Copie o token gerado e cole abaixo
        """)
        
        lichess_token = st.text_input(
            "Token do Lichess:",
            type="password",
            value="",
            key="lichess_token",
            help="Token necessário para jogar partidas automaticamente no Lichess"
        )
        
        if st.button("🔗 Conectar ao Lichess"):
            if lichess_token:
                success = lichess_api.test_connection(lichess_token)
                if success:
                    # Salva a chave do Lichess no .env.temp junto com as outras
                    temp_keys = {
                        "OPENAI_API_KEY": openai_key_input,
                        "GOOGLE_API_KEY": google_key_input,
                        "DEEPSEEK_API_KEY": deepseek_key_input,
                        "GROQ_API_KEY": groq_key_input,
                        "CLAUDE_API_KEY": claude_key_input,
                        "LICHESS_API_TOKEN": lichess_token,
                    }
                    save_temp_env_keys(temp_keys)
                    st.success("✅ Conectado ao Lichess com sucesso! Token salvo temporariamente.")
                else:
                    st.error("❌ Erro na conexão com o Lichess. Verifique o token.")
            else:
                st.warning("⚠️ Insira um token válido.")

        # Informações sobre limites e custos
        st.markdown("#### 💰 Informações de Custos dos Modelos")
        
        cost_comparison = {
            "🥇 Mais Baratos": {
                "DeepSeek-V3": "$0.14-0.28/1M tokens",
                "Llama-3.1-8B": "$0.05-0.08/1M tokens",
                "GPT-4o-Mini": "$0.15-0.60/1M tokens"
            },
            "⚖️ Equilibrados": {
                "Gemini-2.5-Flash": "$0.10-0.40/1M tokens",
                "Claude-4-Sonnet": "$3-15/1M tokens",
                "GPT-4o": "$2.50-10/1M tokens"
            },
            "💎 Premium": {
                "Claude-4-Opus": "$15-75/1M tokens",
                "GPT-4.1": "$5-20/1M tokens",
                "DeepSeek-R1": "$0.55-2.19/1M tokens"
            }
        }
        
        for category, models in cost_comparison.items():
            st.markdown(f"**{category}:**")
            for model, price in models.items():
                st.write(f"- {model}: {price}")

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
        if st.button("🔄 Atualizar Banco de Dados"):
            with st.spinner("Sincronizando arquivos e recalculando estatísticas..."):
                # Caminho raiz do projeto (ajuste se necessário)
                root_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
                total_imported = db.sync_filesystem_and_database(root_path=root_path)
                db.fill_opening_and_analysis()
                db.update_avg_accuracy()
                st.success(
                    f"✅ Banco de dados atualizado! {total_imported} partidas importadas dos arquivos .pgn. "
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
                    st.success("✅ Banco de dados resetado e campos recalculados com sucesso!")
                    st.info("🔄 Reinicie a aplicação para garantir que todas as alterações sejam aplicadas.")