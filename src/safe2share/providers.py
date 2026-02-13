from enum import Enum


class Provider(str, Enum):
    LOCAL = "local"
    # OpenAI-compatible endpoint (OpenAI, Ollama, LM Studio, etc.)
    LLM = "llm"
    AUTO = "auto"
