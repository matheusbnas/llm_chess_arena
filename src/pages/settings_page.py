import streamlit as st
import os
import json
from datetime import datetime


def show_settings(model_manager, lichess_api, db):
    st.markdown("## ⚙️ Configurações")

    tab1, tab2, tab3, tab4 = st.tabs(
        ["🤖 Modelos", "🌐 APIs", "🎮 Jogo", "💾 Dados"])

    with tab1:
        st.markdown("### 🤖 Configuração dos Modelos")

        # API Keys configuration
        st.markdown("#### 🔑 Chaves de API")

        openai_key = st.text_input(
            "OpenAI API Key:",
            type="password",
            value=os.getenv("OPENAI_API_KEY", ""),
            key="openai_key"
        )

        google_key = st.text_input(
            "Google API Key:",
            type="password",
            value=os.getenv("GOOGLE_API_KEY", ""),
            key="google_key"
        )

        deepseek_key = st.text_input(
            "DeepSeek API Key:",
            type="password",
            value=os.getenv("DEEPSEEK_API_KEY", ""),
            key="deepseek_key"
        )

        groq_key = st.text_input(
            "Groq API Key:",
            type="password",
            value=os.getenv("GROQ_API_KEY", ""),
            key="groq_key"
        )

        claude_key = st.text_input(
            "Claude API Key:",
            type="password",
            value=os.getenv("CLAUDE_API_KEY", ""),
            key="claude_key"
        )

        if st.button("💾 Salvar Chaves de API"):
            # Save API keys to .env file
            env_content = f"""
OPENAI_API_KEY={openai_key}
GOOGLE_API_KEY={google_key}
DEEPSEEK_API_KEY={deepseek_key}
GROQ_API_KEY={groq_key}
CLAUDE_API_KEY={claude_key}
"""
            with open('.env', 'w') as f:
                f.write(env_content)

            st.success("✅ Chaves de API salvas com sucesso!")
            st.info("🔄 Reinicie a aplicação para aplicar as mudanças.")

        # Model parameters
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
                    st.success("✅ Conectado ao Lichess com sucesso!")
                else:
                    st.error(
                        "❌ Erro na conexão com o Lichess. Verifique o token.")
            else:
                st.warning("⚠️ Insira um token válido.")

    with tab3:
        st.markdown("### 🎮 Configurações de Jogo")

        # Default game settings
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

        # Analysis settings
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
                    st.success("✅ Dados importados com sucesso!")
                else:
                    st.error("❌ Erro ao importar dados.")
            except Exception as e:
                st.error(f"❌ Erro ao processar arquivo: {str(e)}")

        # Clear data
        st.markdown("#### 🗑️ Limpeza de Dados")

        st.warning("⚠️ Atenção: As operações abaixo são irreversíveis!")

        if st.button("🗑️ Limpar Partidas Antigas (>30 dias)", type="secondary"):
            if st.checkbox("Confirmo que quero deletar partidas antigas"):
                deleted_count = db.delete_old_games(days=30)
                st.success(f"✅ {deleted_count} partidas antigas removidas.")

        if st.button("💥 Resetar Banco de Dados", type="secondary"):
            if st.checkbox("Confirmo que quero resetar TODOS os dados"):
                if st.text_input("Digite 'CONFIRMAR' para prosseguir:") == "CONFIRMAR":
                    db.reset_database()
                    st.success("✅ Banco de dados resetado com sucesso!")
                    st.info("🔄 Reinicie a aplicação.")
