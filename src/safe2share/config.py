from pydantic import BaseModel
from pydantic_settings import BaseSettings, SettingsConfigDict

from .providers import Provider


class Settings(BaseSettings):
    """
    Central configuration for Safe2Share.
    """
    model_config = SettingsConfigDict(env_prefix="S2S_", extra="ignore")

    provider: Provider = Provider.LOCAL

    # LLM / OpenAI-compatible configuration (used starting Day 2)
    llm_base_url: str | None = None
    llm_api_key: str | None = None
    llm_model: str | None = None


settings = Settings()
