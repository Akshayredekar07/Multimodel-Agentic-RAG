
import os
from dotenv import load_dotenv

load_dotenv()

class Config:

    OPENAI_API_KEY: str | None       = os.getenv("OPENAI_API_KEY")
    ANTHROPIC_API_KEY: str | None    = os.getenv("ANTHROPIC_API_KEY")
    GOOGLE_API_KEY: str | None       = os.getenv("GOOGLE_API_KEY")
    GROQ_API_KEY: str | None         = os.getenv("GROQ_API_KEY")
    NVIDIA_API_KEY: str | None       = os.getenv("NVIDIA_API_KEY")
    CEREBRAS_API_KEY: str | None     = os.getenv("CEREBRAS_API_KEY")
    NEBIUS_API_KEY: str | None       = os.getenv("NEBIUS_API_KEY")
    OPENROUTER_API_KEY: str | None   = os.getenv("OPENROUTER_API_KEY")
    HUGGINGFACE_API_KEY: str | None  = os.getenv("HUGGINGFACEHUB_API_TOKEN")
    # Ollama and vLLM run locally — no key needed

    @classmethod
    def get_key(cls, key_name: str) -> str:
        """Get a key and raise clear error if missing."""
        value = getattr(cls, key_name, None)
        if not value:
            raise ValueError(
                f"{key_name} is not set in your .env file"
            )
        return value