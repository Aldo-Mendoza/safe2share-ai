from __future__ import annotations

from .base import BaseAnalyzer
from ..config import settings


class OpenAIGPTAnalyzer(BaseAnalyzer):
    """
    Day 1 behavior: config-aware and non-crashing.
    Day 2: will become OpenAI-compatible provider (base_url, model, api_key).
    """

    def __init__(self) -> None:
        # Consider "available" if we have at least base_url + model.
        # api_key may be optional for some local providers (Ollama / LM Studio),
        # so we do NOT require it here.
        self._is_ready = bool(settings.llm_base_url and settings.llm_model)

    @property
    def is_available(self) -> bool:
        return self._is_ready

    def analyze(self, text: str):
        # Day 1: keep it explicit that it's not implemented.
        # Service should prevent reaching here when not configured.
        raise NotImplementedError(
            "LLM analyzer is not implemented yet. Day 2 will add OpenAI-compatible support."
        )
