import os
from typing import Dict, Any, Optional
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_groq import ChatGroq
from langchain_nebius import ChatNebius
from langchain_core.language_models.chat_models import BaseChatModel
from langsmith import traceable

load_dotenv()  # Loads your .env file

class ModelProvider:
    """Base class for model providers. Loads env vars and initializes chat models."""
    
    def __init__(self, model_name: str, fast_model_name: str, api_key_prefix: str):
        self.model_name = model_name
        self.fast_model_name = fast_model_name
        self.api_prefix = api_key_prefix
        self.api_key = os.getenv(f"{api_prefix}__API_KEY")
        
        if not self.api_key:
            raise ValueError(f"Missing {api_prefix}__API_KEY in .env")
    
    def get_model(self, fast: bool = False) -> BaseChatModel:
        """Returns initialized chat model (fast or regular)."""
        model_name = self.fast_model_name if fast else self.model_name
        return self._init_model(model_name)
    
    def _init_model(self, model_name: str) -> BaseChatModel:
        """Initialize specific chat model - override in subclasses."""
        raise NotImplementedError("Subclasses must implement _init_model")
    
    @property
    def model_info(self) -> Dict[str, Any]:
        """Provider info for debugging."""
        return {
            "provider": self.api_prefix,
            "model": self.model_name,
            "fast_model": self.fast_model_name,
            "api_key_set": bool(self.api_key)
        }

class GoogleProvider(ModelProvider):
    """Google Gemini provider."""
    
    def _init_model(self, model_name: str) -> BaseChatModel:
        return ChatGoogleGenerativeAI(
            model=model_name,
            google_api_key=self.api_key,
            temperature=0.1
        )

class GroqProvider(ModelProvider):
    """Groq provider."""
    
    def _init_model(self, model_name: str) -> BaseChatModel:
        return ChatGroq(
            model=model_name,
            groq_api_key=self.api_key,
            temperature=0.1
        )

class NebiusProvider(ModelProvider):
    """Nebius provider."""
    
    def _init_model(self, model_name: str) -> BaseChatModel:
        return ChatNebius(
            model=model_name,
            nebius_api_key=self.api_key,
            temperature=0.1
        )

class ModelManager:
    """Manages all providers and easy model selection."""
    
    def __init__(self):
        self.providers = {
            "google": GoogleProvider(
                model_name=os.getenv("GOOGLE__MODEL", "gemini/gemini-2.5-flash"),
                fast_model_name=os.getenv("GOOGLE__FAST_MODEL", "gemini/gemini-2.5-flash"),
                api_key_prefix="GOOGLE"
            ),
            "groq": GroqProvider(
                model_name=os.getenv("GROQ__MODEL", "groq/openai/gpt-oss-120b"),
                fast_model_name=os.getenv("GROQ__FAST_MODEL", "moonshotai/kimi-k2-instruct-0905"),
                api_key_prefix="GROQ"
            ),
            "nebius": NebiusProvider(
                model_name=os.getenv("NEBIUS__MODEL", "MiniMaxAI/MiniMax-M2.1"),
                fast_model_name=os.getenv("NEBIUS__FAST_MODEL", "zai-org/GLM-4.7-FP8"),
                api_key_prefix="NEBIUS"
            )
        }
    
    @traceable
    def get_model(self, provider: str, fast: bool = False) -> BaseChatModel:
        """Get model by provider name (google/groq/nebius)."""
        if provider not in self.providers:
            raise ValueError(f"Provider '{provider}' not found. Available: {list(self.providers.keys())}")
        
        return self.providers[provider].get_model(fast=fast)
    
    def list_providers(self) -> Dict[str, Dict[str, Any]]:
        """List all available providers and their info."""
        return {name: prov.model_info for name, prov in self.providers.items()}
    
    def get_fast_model(self, provider: str) -> BaseChatModel:
        """Shortcut for fast models."""
        return self.get_model(provider, fast=True)

# Usage example
if __name__ == "__main__":
    manager = ModelManager()
    
    # List providers
    print("Available providers:", manager.list_providers())
    
    # Get regular model
    google_model = manager.get_model("google")
    print("Google model:", google_model)
    
    # Get fast model
    groq_fast = manager.get_fast_model("groq")
    print("Groq fast model:", groq_fast)
    
    # Invoke example
    response = google_model.invoke("Hello!")
    print("Response:", response.content)