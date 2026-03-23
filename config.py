import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(dotenv_path=Path(__file__).with_name(".env"))


@dataclass
class ProviderModelConfig:
    provider: str
    model: str
    fast_model: str
    provider_api_key_env: str
    runtime_api_key_env: str

    @property
    def api_key(self) -> str | None:
        return os.getenv(self.provider_api_key_env)

    def apply_runtime_env(self) -> None:
        api_key = self.api_key
        if not api_key:
            raise RuntimeError(
                f"Missing {self.provider_api_key_env} in environment or .env"
            )
        os.environ[self.runtime_api_key_env] = api_key

    @property
    def qualified_model(self) -> str:
        return f"{self.provider}:{self.fast_model}"


@dataclass
class AppConfig:
    groq: ProviderModelConfig
    google: ProviderModelConfig
    nebius: ProviderModelConfig
    default_provider: str
    temperature: float
    timeout: int
    max_tokens: int
    max_retries: int

    def get_provider(self, name: str) -> ProviderModelConfig:
        providers = {
            "groq": self.groq,
            "google": self.google,
            "nebius": self.nebius,
        }
        try:
            return providers[name]
        except KeyError as exc:
            raise ValueError(f"Unsupported provider: {name}") from exc


config = AppConfig(
    groq=ProviderModelConfig(
        provider="groq",
        model=os.getenv("GROQ__MODEL", "openai/gpt-oss-120b"),
        fast_model=os.getenv("GROQ__FAST_MODEL", "moonshotai/kimi-k2-instruct-0905"),
        provider_api_key_env="GROQ__API_KEY",
        runtime_api_key_env="GROQ_API_KEY",
    ),
    google=ProviderModelConfig(
        provider="google_genai",
        model=os.getenv("GOOGLE__MODEL", "gemini-2.5-flash"),
        fast_model=os.getenv("GOOGLE__FAST_MODEL", "gemini-2.5-flash"),
        provider_api_key_env="GOOGLE__API_KEY",
        runtime_api_key_env="GOOGLE_API_KEY",
    ),
    nebius=ProviderModelConfig(
        provider="openai",
        model=os.getenv("NEBIUS__MODEL", "MiniMaxAI/MiniMax-M2.1"),
        fast_model=os.getenv("NEBIUS__FAST_MODEL", "zai-org/GLM-4.7-FP8"),
        provider_api_key_env="NEBIUS__API_KEY",
        runtime_api_key_env="OPENAI_API_KEY",
    ),
    default_provider=os.getenv("DEFAULT_PROVIDER", "groq"),
    temperature=float(os.getenv("MODEL_TEMPERATURE", "0.7")),
    timeout=int(os.getenv("MODEL_TIMEOUT", "30")),
    max_tokens=int(os.getenv("MODEL_MAX_TOKENS", "1000")),
    max_retries=int(os.getenv("MODEL_MAX_RETRIES", "6")),
)
