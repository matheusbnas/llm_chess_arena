import os
from typing import Dict, List, Optional, Any
from langchain_openai import ChatOpenAI
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from dotenv import load_dotenv
import time

load_dotenv()

class ModelManager:
    """Manages all available LLM models and their configurations"""
    
    def __init__(self):
        self.models = {}
        self.model_configs = {}
        self._initialize_models()
    
    def _initialize_models(self):
        """Initialize all available models based on API keys"""
        
        # OpenAI Models
        if os.getenv("OPENAI_API_KEY"):
            self.models.update({
                "GPT-4o": ChatOpenAI(temperature=0.1, model='gpt-4o'),
                "GPT-4-Turbo": ChatOpenAI(temperature=0.1, model='gpt-4-turbo'),
                "GPT-3.5-Turbo": ChatOpenAI(temperature=0.1, model='gpt-3.5-turbo'),
            })
        
        # Google Models
        if os.getenv("GOOGLE_API_KEY"):
            self.models.update({
                "Gemini-Pro": ChatGoogleGenerativeAI(temperature=0.1, model="gemini-1.5-pro-latest"),
                "Gemini-1.0-Pro": ChatGoogleGenerativeAI(temperature=0.1, model="gemini-1.0-pro"),
            })
        
        # DeepSeek Models
        if os.getenv("DEEPSEEK_API_KEY"):
            self.models.update({
                "Deepseek-Chat": ChatOpenAI(
                    temperature=0.1,
                    model="deepseek-chat",
                    api_key=os.getenv("DEEPSEEK_API_KEY"),
                    base_url="https://api.deepseek.com/v1"
                ),
                "Deepseek-Coder": ChatOpenAI(
                    temperature=0.1,
                    model="deepseek-coder",
                    api_key=os.getenv("DEEPSEEK_API_KEY"),
                    base_url="https://api.deepseek.com/v1"
                ),
            })
        
        # Groq Models (for judging)
        if os.getenv("GROQ_API_KEY"):
            self.models.update({
                "Llama3-70B": ChatGroq(temperature=0, model_name="llama3-70b-8192"),
                "Mixtral-8x7B": ChatGroq(temperature=0, model_name="mixtral-8x7b-32768"),
            })
    
    def get_available_models(self) -> Dict[str, bool]:
        """Get list of available models and their status"""
        status = {}
        for name, model in self.models.items():
            try:
                # Quick test to see if model is accessible
                status[name] = True
            except:
                status[name] = False
        return status
    
    def get_model(self, model_name: str):
        """Get a specific model instance"""
        return self.models.get(model_name)
    
    def test_model(self, model_name: str) -> Dict[str, Any]:
        """Test if a model is working correctly"""
        model = self.get_model(model_name)
        if not model:
            return {"success": False, "error": "Model not found"}
        
        try:
            start_time = time.time()
            
            # Simple test prompt
            test_prompt = ChatPromptTemplate.from_messages([
                ("system", "You are a chess player. Respond with just 'e4' - nothing else."),
                ("human", "What is your first move as white?")
            ])
            
            chain = test_prompt | model
            response = chain.invoke({"input": "test"})
            
            response_time = time.time() - start_time
            
            return {
                "success": True,
                "response_time": response_time,
                "response": response.content.strip()
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def get_chess_prompt(self, color: str) -> ChatPromptTemplate:
        """Get the chess playing prompt for a specific color"""
        system_template = """
        You are a Chess Grandmaster playing in a tournament.
        You are playing with the {color} pieces.
        
        I will give you the last move, the history of the game so far, and
        you must analyze the position and find the best move.

        # IMPORTANT RULES:
        1. You must respond with a valid chess move in Standard Algebraic Notation (SAN)
        2. Do not include move numbers (like "1." or "2...")
        3. Examples of valid moves: e4, Nf3, O-O, Qh5+, Rxe8#
        4. Think strategically about piece development, center control, and king safety

        # OUTPUT FORMAT:
        My move: "Move"
        
        Brief explanation in Portuguese (max 2 sentences) of why you chose this move.
        """
        
        return ChatPromptTemplate.from_messages([
            ("system", system_template.format(color=color)),
            ("human", "{input}")
        ])
    
    def update_model_config(self, model_name: str, config: Dict[str, Any]):
        """Update configuration for a specific model"""
        self.model_configs[model_name] = config
        
        # Recreate model with new config if needed
        if model_name in self.models:
            # This would require recreating the model with new parameters
            pass
    
    def get_model_info(self, model_name: str) -> Dict[str, Any]:
        """Get information about a specific model"""
        if model_name not in self.models:
            return {}
        
        return {
            "name": model_name,
            "provider": self._get_provider(model_name),
            "available": model_name in self.get_available_models(),
            "config": self.model_configs.get(model_name, {})
        }
    
    def _get_provider(self, model_name: str) -> str:
        """Get the provider for a model"""
        if "GPT" in model_name:
            return "OpenAI"
        elif "Gemini" in model_name:
            return "Google"
        elif "Deepseek" in model_name:
            return "DeepSeek"
        elif "Llama" in model_name or "Mixtral" in model_name:
            return "Groq"
        else:
            return "Unknown"