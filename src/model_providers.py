import logging
import sys
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Optional, Literal
from langchain_core.language_models.chat_models import BaseChatModel
from langchain.chat_models import init_chat_model
from langchain_cerebras import ChatCerebras

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from config import Config


logger = logging.getLogger(__name__)

class LLMProvider(ABC):
    @abstractmethod
    def get_llm(
        self,
        model_name: Optional[str] = None,
        **kwargs,
    ) -> BaseChatModel:
        """Return a BaseChatModel. Use .bind_tools() on result to attach tools."""
        pass

    def get_api_key(self, key_name: str) -> str:
        """Fetch provider credentials from central config."""
        return Config.get_key(key_name)

    def _build_params(
        self,
        model: str,
        temperature: float,
        max_tokens: Optional[int],
        timeout: Optional[int],
        base_url: Optional[str],
        configurable_fields: Optional[Literal["any"] | list[str] | tuple[str, ...]],
        config_prefix: Optional[str],
        **kwargs,
    ) -> dict:
        """Shared param builder — filters out None values for all providers."""
        params = {
            "model": model,
            "temperature": temperature,
            **kwargs,
        }
        if max_tokens is not None:
            params["max_tokens"] = max_tokens
        if timeout is not None:
            params["timeout"] = timeout
        if base_url is not None:
            params["base_url"] = base_url
        if configurable_fields is not None:
            params["configurable_fields"] = configurable_fields
        if config_prefix is not None:
            params["config_prefix"] = config_prefix
        return params

    def _init(self, provider_name: str, model: str, params: dict) -> BaseChatModel:
        """Shared init + logging for all providers."""
        try:
            logger.info(f"[{provider_name}] Initializing model: {model}")
            llm = init_chat_model(**params)
            logger.info(f"[{provider_name}] Model '{model}' initialized successfully.")
            return llm
        except Exception as e:
            logger.error(f"[{provider_name}] Failed to initialize model '{model}': {e}")
            raise


class OpenAIProvider(LLMProvider):
    def get_llm(
        self,
        model_name: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        timeout: Optional[int] = None,
        base_url: Optional[str] = None,
        configurable_fields: Optional[Literal["any"] | list[str] | tuple[str, ...]] = None,
        config_prefix: Optional[str] = None,
        **kwargs,
    ) -> BaseChatModel:
        model = model_name or "gpt-4o"
        api_key = self.get_api_key("OPENAI_API_KEY")
        params = self._build_params(
            f"openai:{model}", temperature,
            max_tokens, timeout, base_url, configurable_fields, config_prefix,
            api_key=api_key,
            **kwargs
        )
        return self._init("OpenAI", model, params)


class AnthropicProvider(LLMProvider):
    def get_llm(
        self,
        model_name: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        timeout: Optional[int] = None,
        base_url: Optional[str] = None,
        configurable_fields: Optional[Literal["any"] | list[str] | tuple[str, ...]] = None,
        config_prefix: Optional[str] = None,
        **kwargs,
    ) -> BaseChatModel:
        model = model_name or "claude-sonnet-4-5-20250929"
        api_key = self.get_api_key("ANTHROPIC_API_KEY")
        params = self._build_params(
            f"anthropic:{model}", temperature,
            max_tokens, timeout, base_url, configurable_fields, config_prefix,
            api_key=api_key,
            **kwargs
        )
        return self._init("Anthropic", model, params)


class GeminiProvider(LLMProvider):
    def get_llm(
        self,
        model_name: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        timeout: Optional[int] = None,
        base_url: Optional[str] = None,
        configurable_fields: Optional[Literal["any"] | list[str] | tuple[str, ...]] = None,
        config_prefix: Optional[str] = None,
        **kwargs,
    ) -> BaseChatModel:
        model = model_name or "gemini-2.5-flash"
        api_key = self.get_api_key("GOOGLE_API_KEY")
        params = self._build_params(
            f"google_genai:{model}", temperature,
            max_tokens, timeout, base_url, configurable_fields, config_prefix,
            api_key=api_key,
            **kwargs
        )
        return self._init("Gemini", model, params)


class GroqProvider(LLMProvider):
    def get_llm(
        self,
        model_name: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        timeout: Optional[int] = None,
        base_url: Optional[str] = None,
        configurable_fields: Optional[Literal["any"] | list[str] | tuple[str, ...]] = None,
        config_prefix: Optional[str] = None,
        **kwargs,
    ) -> BaseChatModel:
        model = model_name or "llama-3.3-70b-versatile"
        api_key = self.get_api_key("GROQ_API_KEY")
        params = self._build_params(
            f"groq:{model}", temperature,
            max_tokens, timeout, base_url, configurable_fields, config_prefix,
            api_key=api_key,
            **kwargs
        )
        return self._init("Groq", model, params)


class OllamaProvider(LLMProvider):
    def get_llm(
        self,
        model_name: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        timeout: Optional[int] = None,
        base_url: Optional[str] = None,
        configurable_fields: Optional[Literal["any"] | list[str] | tuple[str, ...]] = None,
        config_prefix: Optional[str] = None,
        **kwargs,
    ) -> BaseChatModel:
        model = model_name or "llama3.2"
        params = self._build_params(
            f"ollama:{model}", temperature,
            max_tokens, timeout, base_url, configurable_fields, config_prefix, **kwargs
        )
        return self._init("Ollama", model, params)


class NvidiaProvider(LLMProvider):
    def get_llm(
        self,
        model_name: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        timeout: Optional[int] = None,
        base_url: Optional[str] = None,
        configurable_fields: Optional[Literal["any"] | list[str] | tuple[str, ...]] = None,
        config_prefix: Optional[str] = None,
        **kwargs,
    ) -> BaseChatModel:
        model = model_name or "meta/llama-3.3-70b-instruct"
        api_key = self.get_api_key("NVIDIA_API_KEY")
        params = self._build_params(
            f"nvidia:{model}", temperature,
            max_tokens, timeout, base_url, configurable_fields, config_prefix,
            api_key=api_key,
            **kwargs
        )
        return self._init("Nvidia", model, params)


from langchain_cerebras import ChatCerebras  

class CerebrasProvider(LLMProvider):
    def get_llm(
        self,
        model_name: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        timeout: Optional[int] = None,
        **kwargs,
    ) -> BaseChatModel:
        model = model_name or "llama-3.3-70b"
        api_key = self.get_api_key("CEREBRAS_API_KEY")

        params = {
            "model": model,
            "temperature": temperature,
            "api_key": api_key,
        }
        if max_tokens is not None:
            params["max_tokens"] = max_tokens
        if timeout is not None:
            params["timeout"] = timeout

        try:
            logger.info(f"[Cerebras] Initializing model: {model}")
            llm = ChatCerebras(**params, **kwargs) 
            logger.info(f"[Cerebras] Model '{model}' initialized successfully.")
            return llm
        except Exception as e:
            logger.error(f"[Cerebras] Failed to initialize model '{model}': {e}")
            raise


class NeblusProvider(LLMProvider):
    def get_llm(
        self,
        model_name: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        timeout: Optional[int] = None,
        configurable_fields: Optional[Literal["any"] | list[str] | tuple[str, ...]] = None,
        config_prefix: Optional[str] = None,
        **kwargs,
    ) -> BaseChatModel:
        model = model_name or "Qwen/Qwen3-235B-A22B"
        api_key = self.get_api_key("NEBIUS_API_KEY")

        params = self._build_params(
            model=model,          
            temperature=temperature,
            max_tokens=max_tokens,
            timeout=timeout,
            base_url="https://api.tokenfactory.nebius.com/v1", 
            configurable_fields=configurable_fields,
            config_prefix=config_prefix,
            api_key=api_key,        
            model_provider="openai", 
            **kwargs,
        )
        return self._init("Nebius", model, params)


class OpenRouterProvider(LLMProvider):
    def get_llm(
        self,
        model_name: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        timeout: Optional[int] = None,
        configurable_fields: Optional[Literal["any"] | list[str] | tuple[str, ...]] = None,
        config_prefix: Optional[str] = None,
        **kwargs,
    ) -> BaseChatModel:
        model = model_name or "openai/gpt-4o"
        api_key = self.get_api_key("OPENROUTER_API_KEY")

        params = self._build_params(
            f"openai:{model}", temperature,
            max_tokens, timeout,
            base_url="https://openrouter.ai/api/v1",
            configurable_fields=configurable_fields,
            config_prefix=config_prefix,
            api_key=api_key,        
            **kwargs,
        )
        return self._init("OpenRouter", model, params)

class HuggingFaceProvider(LLMProvider):
    def get_llm(
        self,
        model_name: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        timeout: Optional[int] = None,
        base_url: Optional[str] = None,
        configurable_fields: Optional[Literal["any"] | list[str] | tuple[str, ...]] = None,
        config_prefix: Optional[str] = None,
        **kwargs,
    ) -> BaseChatModel:
        model = model_name or "HuggingFaceH4/zephyr-7b-beta"
        api_key = self.get_api_key("HUGGINGFACE_API_KEY")
        params = self._build_params(
            f"huggingface:{model}", temperature,
            max_tokens, timeout, base_url, configurable_fields, config_prefix,
            api_key=api_key,
            **kwargs
        )
        return self._init("HuggingFace", model, params)


class VLLMProvider(LLMProvider):
    # vLLM runs locally and exposes an OpenAI-compatible API
    def get_llm(
        self,
        model_name: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        timeout: Optional[int] = None,
        base_url: str = "http://localhost:8000/v1",   # vLLM default local server
        configurable_fields: Optional[Literal["any"] | list[str] | tuple[str, ...]] = None,
        config_prefix: Optional[str] = None,
        **kwargs,
    ) -> BaseChatModel:
        model = model_name or "meta-llama/Llama-3-8b-instruct"
        params = self._build_params(
            f"openai:{model}", temperature,
            max_tokens, timeout, base_url, configurable_fields, config_prefix, **kwargs
        )
        return self._init("vLLM", model, params)


class LLMFactory:
    """
    Single class to access all providers.

    Usage:
        factory = LLMFactory()
        llm = factory.get_llm("openai", model_name="gpt-4o")
        llm = factory.get_llm("anthropic", model_name="claude-sonnet-4-5-20250929")
        llm = factory.get_llm("groq", temperature=0.3)
    """

    _providers: dict[str, LLMProvider] = {
        "openai":      OpenAIProvider(),
        "anthropic":   AnthropicProvider(),
        "gemini":      GeminiProvider(),
        "groq":        GroqProvider(),
        "ollama":      OllamaProvider(),
        "nvidia":      NvidiaProvider(),
        "cerebras":    CerebrasProvider(),
        "nebius":      NeblusProvider(),
        "openrouter":  OpenRouterProvider(),
        "huggingface": HuggingFaceProvider(),
        "vllm":        VLLMProvider(),
    }

    def get_llm(
        self,
        provider: str,
        model_name: Optional[str] = None,
        **kwargs,
    ) -> BaseChatModel:
        provider = provider.lower()
        if provider not in self._providers:
            available = list(self._providers.keys())
            raise ValueError(f"Unknown provider '{provider}'. Available: {available}")
        return self._providers[provider].get_llm(model_name=model_name, **kwargs)

    @property
    def available_providers(self) -> list[str]:
        return list(self._providers.keys())
