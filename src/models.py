import os
from typing import Dict, Any
from langchain_openai import ChatOpenAI
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.messages import HumanMessage
from dotenv import load_dotenv
import time
import streamlit as st

# Adicione a importação do Anthropic/Claude
try:
    from langchain_anthropic import ChatAnthropic
    CLAUDE_AVAILABLE = True
except ImportError:
    CLAUDE_AVAILABLE = False

load_dotenv()

# Substitua get_env_var por:
def get_env_var(key):
    # Busca primeiro no .env.temp, depois .env, depois variável de ambiente
    env_temp_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '.env.temp'))
    if os.path.exists(env_temp_path):
        with open(env_temp_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                if "=" in line:
                    k, val = line.split("=", 1)
                    if k.strip().replace(" ", "") == key:
                        return val.strip().strip('"').strip("'")
    # Fallback para o método antigo
    v = os.getenv(key)
    if v is not None:
        return v.strip()
    # Busca manualmente no .env se não achou
    env_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '.env'))
    try:
        with open(env_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                if "=" in line:
                    k, val = line.split("=", 1)
                    if k.strip().replace(" ", "") == key:
                        return val.strip().strip('"').strip("'")
    except Exception:
        pass
    return ""

class ModelManager:
    """Manages all available LLM models and their configurations"""

    def __init__(self, api_keys: dict = None, trust_cached: bool = False, cache_expiration: int = 3600):
        self.models = {}
        self.model_configs = {}
        self.api_keys = api_keys or {}
        self._last_api_keys = {}  # Para rastrear mudanças nas chaves
        self._trust_cached = trust_cached  # Modo de confiança
        # Tempo (segundos) até considerar o status de um modelo expirado.
        # Pode ser ajustado via parâmetro; padrão = 3600 s (1 hora).
        self._cache_expiration = cache_expiration
        self._initialize_models()
        
        # Usa cache compartilhado no session_state, se existir, para evitar repetir testes em cada rerender.
        self._model_status_cache = st.session_state.get('model_status_cache', {})  # Cache para status dos modelos
        
        # Executa testes se ainda não há cache salvo nesta sessão
        if not trust_cached and not self._model_status_cache:
            self._test_all_models()
            st.session_state['models_tested'] = True
            # Persiste o cache para as próximas instâncias nesta sessão
            st.session_state['model_status_cache'] = self._model_status_cache

    def _get_key(self, key):
        # Prioriza o dicionário passado (input), senão busca no ambiente/arquivo
        if self.api_keys and key in self.api_keys and self.api_keys[key]:
            return self.api_keys[key]
        return get_env_var(key)

    def _initialize_models(self):
        """Initialize all available models based on API keys"""
        
        # OpenAI Models - Atualizados para 2025
        openai_key = self._get_key("OPENAI_API_KEY")
        if openai_key:
            try:
                self.models.update({
                    # Novos modelos GPT-4.1 (mais recentes)
                    "GPT-4.1": ChatOpenAI(temperature=0.1, model='gpt-4.1', openai_api_key=openai_key),
                    "GPT-4.1-Mini": ChatOpenAI(temperature=0.1, model='gpt-4.1-mini', openai_api_key=openai_key),
                    "GPT-4.1-Nano": ChatOpenAI(temperature=0.1, model='gpt-4.1-nano', openai_api_key=openai_key),
                    # Modelos GPT-4o (ainda disponíveis)
                    "GPT-4o": ChatOpenAI(temperature=0.1, model='gpt-4o', openai_api_key=openai_key),
                    "GPT-4o-Mini": ChatOpenAI(temperature=0.1, model='gpt-4o-mini', openai_api_key=openai_key),
                    # GPT-3.5 Turbo (ainda disponível)
                    "GPT-3.5-Turbo": ChatOpenAI(temperature=0.1, model='gpt-3.5-turbo', openai_api_key=openai_key),
                })
            except Exception as e:
                print(f"Error initializing OpenAI models: {e}")
        
        # Google Models - Atualizados para Gemini 2.5
        google_key = self._get_key("GOOGLE_API_KEY")
        if google_key:
            try:
                self.models.update({
                    # Novos modelos Gemini 2.5 (mais recentes)
                    "Gemini-2.5-Flash": ChatGoogleGenerativeAI(
                        temperature=0.1, 
                        model="gemini-2.5-flash", 
                        google_api_key=google_key
                    ),
                    "Gemini-2.5-Pro": ChatGoogleGenerativeAI(
                        temperature=0.1, 
                        model="gemini-2.5-pro", 
                        google_api_key=google_key
                    ),
                    "gemini-2.5-flash-lite-preview-06-17": ChatGoogleGenerativeAI(
                        temperature=0.1, 
                        model="gemini-2.5-flash-lite-preview-06-17", 
                        google_api_key=google_key
                    ),
                })
            except Exception as e:
                print(f"Error initializing Google models: {e}")
        
        # DeepSeek Models - Atualizados para R1 e V3
        deepseek_key = self._get_key("DEEPSEEK_API_KEY")
        if deepseek_key:
            try:
                self.models.update({
                    # Novos modelos DeepSeek R1 e V3
                    "DeepSeek-R1": ChatOpenAI(
                        temperature=0.1,
                        model="deepseek-reasoner",
                        openai_api_key=deepseek_key,
                        openai_api_base="https://api.deepseek.com/v1"
                    ),
                    "DeepSeek-V3": ChatOpenAI(
                        temperature=0.1,
                        model="deepseek-chat",
                        openai_api_key=deepseek_key,
                        openai_api_base="https://api.deepseek.com/v1"
                    ),
                    # Modelos legados (ainda disponíveis)
                    "DeepSeek-Coder": ChatOpenAI(
                        temperature=0.1,
                        model="deepseek-coder",
                        openai_api_key=deepseek_key,
                        openai_api_base="https://api.deepseek.com/v1"
                    ),
                })
            except Exception as e:
                print(f"Error initializing DeepSeek models: {e}")
        
        # Groq Models - Atualizados para Llama 3.3 e modelos mais recentes
        groq_key = self._get_key("GROQ_API_KEY")
        if groq_key:
            try:
                self.models.update({
                    # Novos modelos Llama 3.3 (mais recentes)
                    "Llama-3.3-70B": ChatGroq(
                        temperature=0, 
                        model_name="llama-3.3-70b-versatile", 
                        groq_api_key=groq_key
                    ),
                    "Llama-3.1-8B": ChatGroq(
                        temperature=0, 
                        model_name="llama-3.1-8b-instant", 
                        groq_api_key=groq_key
                    ),
                })
            except Exception as e:
                print(f"Error initializing Groq models: {e}")
        
        # Claude (Anthropic) - Atualizados para Claude 4
        claude_key = self._get_key("CLAUDE_API_KEY")
        if claude_key and CLAUDE_AVAILABLE:
            try:
                self.models.update({
                    # Modelos Claude 4 (mais recentes)
                    "Claude-4-Opus": ChatAnthropic(
                        temperature=0.1,
                        model_name="claude-opus-4-20250514",
                        anthropic_api_key=claude_key
                    ),
                    "Claude-4-Sonnet": ChatAnthropic(
                        temperature=0.1,
                        model_name="claude-sonnet-4-20250514",
                        anthropic_api_key=claude_key
                    ),
                    # Modelo Claude 3.7 Sonnet (intermediário)
                    "Claude-3.7-Sonnet": ChatAnthropic(
                        temperature=0.1,
                        model_name="claude-3-7-sonnet-20250219",
                        anthropic_api_key=claude_key
                    ),
                    # Modelo Claude 3.5 Haiku (ainda disponível)
                    "Claude-3.5-Haiku": ChatAnthropic(
                        temperature=0.1,
                        model_name="claude-3-5-haiku-20241022",
                        anthropic_api_key=claude_key
                    ),
                })
            except Exception as e:
                print(f"Error initializing Claude models: {e}")
    
    def _test_all_models(self):
        """Test all models once and cache the results"""
        # Se já existe cache salvo, não retesta
        if st.session_state.get('model_status_cache'):
            self._model_status_cache = st.session_state['model_status_cache']
            return
        
        print("🧪 Testando modelos disponíveis...")
        current_time = time.time()
        for name, model in self.models.items():
            try:
                # Teste rápido do modelo
                test_result = self._quick_test_model(model)
                self._model_status_cache[name] = (test_result, current_time)
                status_icon = "✅" if test_result else "❌"
                print(f"{status_icon} {name}: {'Funcionando' if test_result else 'Falhou'}")
            except Exception as e:
                print(f"❌ {name}: Erro - {str(e)}")
                self._model_status_cache[name] = (False, current_time)
        
        working_count = sum(1 for status, _ in self._model_status_cache.values() if status)
        print(f"📊 Resultado: {working_count}/{len(self.models)} modelos funcionando")
        
        # Persiste cache e flag
        st.session_state['model_status_cache'] = self._model_status_cache
        st.session_state['models_tested'] = True
    
    def get_available_models(self, trust_cached: bool = None) -> Dict[str, bool]:
        """Get cached status of all models (tested once on initialization)"""
        if trust_cached is None:
            trust_cached = self._trust_cached
            
        if trust_cached:
            # Em modo de confiança, sempre retorna True para modelos disponíveis
            return {name: True for name in self.models.keys()}
            
        current_time = time.time()
        expired_models = []
        
        # Verifica se algum cache expirou
        for model_name, (status, timestamp) in self._model_status_cache.items():
            if current_time - timestamp > self._cache_expiration:
                expired_models.append(model_name)
        
        # Remove modelos expirados
        for model_name in expired_models:
            del self._model_status_cache[model_name]
            
        # Retorna uma cópia do cache atual
        return {name: status for name, (status, _) in self._model_status_cache.items()}
    
    def retest_models(self):
        """Re-test all models and update cache (call this when needed)"""
        print("🔄 Re-testando todos os modelos...")
        self._test_all_models()
        return self._model_status_cache.copy()
    
    def _quick_test_model(self, model) -> bool:
        """Quickly test if a model is working by making a simple call"""
        try:
            # Cria uma mensagem de teste simples
            test_message = HumanMessage(content="Say 'OK' - nothing else.")
            
            # Tenta fazer a chamada com timeout
            response = model.invoke([test_message])
            
            # Verifica se a resposta não está vazia
            if hasattr(response, 'content'):
                return bool(response.content and response.content.strip())
            elif isinstance(response, str):
                return bool(response.strip())
            else:
                return bool(str(response).strip())
                
        except Exception as e:
            print(f"Quick test failed: {e}")
            return False
    
    def get_model(self, model_name: str):
        """Get a specific model instance"""
        return self.models.get(model_name)
    
    def test_model(self, model_name: str, force_retest: bool = False, trust_cached: bool = None) -> Dict[str, Any]:
        """Test a specific model with detailed results"""
        if trust_cached is None:
            trust_cached = self._trust_cached
            
        model = self.get_model(model_name)
        if not model:
            return {"success": False, "error": "Model not found"}
        
        # Em modo de confiança, sempre retorna sucesso
        if trust_cached:
            return {
                "success": True,
                "response_time": 0.0,
                "response": "e4",
                "cached": True
            }
        
        # Se não forçar re-teste, usa o cache
        if not force_retest and model_name in self._model_status_cache:
            cached_status, _ = self._model_status_cache[model_name]
            if cached_status:
                return {
                    "success": True,
                    "response_time": 0.0,
                    "response": "e4",
                    "cached": True
                }
            else:
                return {
                    "success": False,
                    "error": "Model failed in initial test (cached result)",
                    "cached": True
                }
        
        try:
            start_time = time.time()
            test_prompt = ChatPromptTemplate.from_messages([
                ("system", "You are a chess player. Respond with just 'e4' - nothing else."),
                ("human", "What is your first move as white?")
            ])
            # Gera as mensagens do prompt
            messages = test_prompt.format_messages(input="test")
            # Chama o modelo diretamente com as mensagens
            response = model.invoke(messages)
            response_time = time.time() - start_time
            # Garante que o retorno é string
            if hasattr(response, "content"):
                resp_content = response.content.strip()
            elif isinstance(response, str):
                resp_content = response.strip()
            else:
                resp_content = str(response)
            
            # Atualiza o cache
            self._model_status_cache[model_name] = (True, time.time())
            
            return {
                "success": True,
                "response_time": response_time,
                "response": resp_content,
                "cached": False
            }
        except Exception as e:
            # Atualiza o cache
            self._model_status_cache[model_name] = (False, time.time())
            return {"success": False, "error": str(e), "cached": False}
    
    def get_working_models_only(self, trust_cached: bool = None) -> Dict[str, bool]:
        """Get only models that are actually working (from cache)"""
        if trust_cached is None:
            trust_cached = self._trust_cached
            
        if trust_cached:
            # Em modo de confiança, retorna todos os modelos disponíveis
            return {name: True for name in self.models.keys()}
            
        # Retorna apenas os modelos que foram testados e estão funcionando
        return {name: True for name, (status, _) in self._model_status_cache.items() if status}
    
    def is_model_working(self, model_name: str) -> bool:
        """Check if a specific model is working (from cache)"""
        return self._model_status_cache.get(model_name, (False, 0))[0]
    
    def get_chess_prompt(self, color: str) -> ChatPromptTemplate:
        """Get chess-specific prompt template"""
        system_template = """
        You are a Chess Grandmaster playing in a tournament.
        You are playing with the {color} pieces.
        I will give you the current game state and you must analyze the position and find the best move.
        
        # CRITICAL RULES:
        1. You MUST respond with a valid chess move in Standard Algebraic Notation (SAN)
        2. Do not include move numbers (like "1." or "2...")
        3. Examples of valid moves: e4, Nf3, O-O, Qh5+, Rxe8#
        4. Think strategically about piece development, center control, and king safety
        
        # REQUIRED OUTPUT FORMAT:
        My move: "Move"
        
        Then provide a brief explanation in Portuguese (max 2 sentences) of why you chose this move.
        """
        return ChatPromptTemplate.from_messages([
            ("system", system_template.format(color=color)),
            ("human", "{input}")
        ])
    
    def update_model_config(self, model_name: str, config: Dict[str, Any]):
        self.model_configs[model_name] = config
        if model_name in self.models:
            pass
    
    def get_model_info(self, model_name: str) -> Dict[str, Any]:
        if model_name not in self.models:
            return {}
        return {
            "name": model_name,
            "provider": self._get_provider(model_name),
            "available": model_name in self.get_available_models(),
            "config": self.model_configs.get(model_name, {}),
            "pricing_tier": self._get_pricing_tier(model_name),
            "capabilities": self._get_capabilities(model_name)
        }
    
    def _get_provider(self, model_name: str) -> str:
        if "GPT" in model_name:
            return "OpenAI"
        elif "Gemini" in model_name:
            return "Google"
        elif "DeepSeek" in model_name:
            return "DeepSeek"
        elif "Llama" in model_name or "Mixtral" in model_name:
            return "Groq"
        elif "Claude" in model_name:
            return "Anthropic"
        else:
            return "Unknown"
    
    def _get_pricing_tier(self, model_name: str) -> str:
        """Get pricing tier information for the model"""
        high_cost_models = ["GPT-4.1", "Claude-4-Opus", "Gemini-2.5-Pro", "DeepSeek-R1"]
        mid_cost_models = ["GPT-4o", "Claude-4-Sonnet", "Claude-3.5-Sonnet", "Gemini-2.5-Flash"]
        low_cost_models = ["GPT-4o-Mini", "GPT-3.5-Turbo", "Claude-3-Haiku", "Llama", "Mixtral"]
        
        if any(high_model in model_name for high_model in high_cost_models):
            return "High"
        elif any(mid_model in model_name for mid_model in mid_cost_models):
            return "Medium"
        elif any(low_model in model_name for low_model in low_cost_models):
            return "Low"
        else:
            return "Unknown"
    
    def _get_capabilities(self, model_name: str) -> list:
        """Get model capabilities"""
        capabilities = []
        
        # Multimodal capabilities
        if any(model in model_name for model in ["GPT-4", "Gemini", "Claude-4", "Claude-3.5"]):
            capabilities.append("multimodal")
        
        # Reasoning capabilities
        if any(model in model_name for model in ["DeepSeek-R1", "GPT-4.1", "Claude-4-Opus", "Gemini-2.5-Pro"]):
            capabilities.append("advanced_reasoning")
        
        # Coding capabilities
        if any(model in model_name for model in ["DeepSeek", "Claude-4", "GPT-4", "Gemini-2.5"]):
            capabilities.append("coding")
        
        # Fast inference
        if any(model in model_name for model in ["Llama", "Mixtral", "GPT-4o-Mini", "Gemini-2.5-Flash"]):
            capabilities.append("fast_inference")
        
        # Long context
        if any(model in model_name for model in ["Claude", "Gemini", "GPT-4.1"]):
            capabilities.append("long_context")
        
        return capabilities
    
    def get_recommended_models(self, use_case: str = "chess") -> Dict[str, str]:
        """Get recommended models for specific use cases"""
        recommendations = {
            "chess": {
                "best_performance": "Claude-4-Opus",
                "balanced": "Claude-4-Sonnet",
                "cost_effective": "GPT-4o-Mini",
                "reasoning": "DeepSeek-R1"
            },
            "coding": {
                "best_performance": "Claude-4-Opus",
                "balanced": "DeepSeek-V3",
                "cost_effective": "DeepSeek-Coder",
                "reasoning": "DeepSeek-R1"
            },
            "general": {
                "best_performance": "GPT-4.1",
                "balanced": "GPT-4o",
                "cost_effective": "GPT-4o-Mini",
                "multimodal": "Gemini-2.5-Flash"
            }
        }
        return recommendations.get(use_case, recommendations["general"])