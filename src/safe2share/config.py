# settings (Pydantic)

from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional


class Settings(BaseSettings):
    # Global Application Settings
    MODE: str = "local" 
    LOG_LEVEL: str = "INFO"

    # --- API-BASED ANALYZER CONFIG (OpenAI Protocol) ---
    # Used for any external service compatible with the OpenAI API (OpenAI, Azure, Proxies)
    OPENAI_API_KEY: Optional[str] = None
    OPENAI_MODEL: str = "gpt-4o-mini"
    OPENAI_BASE_URL: Optional[str] = None

    # --- LOCAL LLAMA/OLLAMA CONFIG (TODO) ---
    # These would be accessed by a separate LlamaLocalAnalyzer class
    LLAMA_HOST: Optional[str] = None
    LLAMA_MODEL: Optional[str] = None


    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=True 
    )


settings = Settings()
