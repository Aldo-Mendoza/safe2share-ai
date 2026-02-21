import logging

from .config import settings
from .providers import Provider

from .analyzers.rule_based import RuleBasedAnalyzer
from .analyzers.llm_openai_compat import OpenAICompatibleAnalyzer
from .analyzers.auto_combined import AutoCombinedAnalyzer

logger = logging.getLogger(__name__)


class Safe2ShareService:
    """
    Orchestrator that selects an analyzer strategy based on Provider
    and exposes a single analyze(text) entrypoint.
    """

    def __init__(self, provider: Provider | None = None):
        self.provider: Provider = provider or settings.provider
        self.analyzer = self._build_analyzer(self.provider)

        # Enforce readiness for explicit LLM provider.
        # AUTO is always usable because local runs even if LLM is unavailable.
        if self.provider == Provider.LLM:
            if hasattr(self.analyzer, "is_available") and not self.analyzer.is_available:
                raise self._unavailable_error()

    def _build_analyzer(self, provider: Provider):
        if provider == Provider.LOCAL:
            return RuleBasedAnalyzer()

        if provider == Provider.LLM:
            return OpenAICompatibleAnalyzer()

        if provider == Provider.AUTO:
            return AutoCombinedAnalyzer()

        raise ValueError(f"Unsupported provider: {provider}")

    def _unavailable_error(self) -> RuntimeError:
        return RuntimeError(
            "Provider 'llm' selected but no LLM configuration is available.\n"
            "Set these environment variables:\n"
            "  S2S_LLM_BASE_URL (e.g., http://127.0.0.1:11434/v1)\n"
            "  S2S_LLM_MODEL (e.g., llama3.1:latest)\n"
            "Optional:\n"
            "  S2S_LLM_API_KEY (required for some hosted providers)\n"
            "Or use: --provider local or --provider auto"
        )

    def analyze(self, text: str):
        return self.analyzer.analyze(text)
