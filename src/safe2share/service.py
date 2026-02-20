import logging

from .config import settings
from .providers import Provider

from .analyzers.rule_based import RuleBasedAnalyzer
from .analyzers.llm_openai_compat import OpenAICompatibleAnalyzer

logger = logging.getLogger(__name__)


class Safe2ShareService:
    """
    Orchestrator that selects an analyzer strategy based on Provider
    and exposes a single analyze(text) entrypoint.
    """

    def __init__(self, provider: Provider | None = None):
        self.provider: Provider = provider or settings.provider
        self.analyzer = self._build_analyzer(self.provider)

        # Uniform readiness check (local is always available; llm depends on config/endpoint)
        if hasattr(self.analyzer, "is_available") and not self.analyzer.is_available:
            raise self._unavailable_error(self.provider)

        if self.provider == Provider.LOCAL:
            self.analyzer = RuleBasedAnalyzer()
        elif self.provider == Provider.LLM:
            self.analyzer = OpenAICompatibleAnalyzer()
            if hasattr(self.analyzer, "is_available") and not self.analyzer.is_available:
                raise RuntimeError(
                    "Provider 'llm' selected but no LLM configuration is available.\n"
                    "Set these environment variables:\n"
                    "  S2S_LLM_BASE_URL (e.g., http://localhost:11434/v1)\n"
                    "  S2S_LLM_MODEL (e.g., llama3.1)\n"
                    "Optional:\n"
                    "  S2S_LLM_API_KEY (required for some hosted providers)\n"
                    "Or use: --provider local"
                )
        elif self.provider == Provider.AUTO:
            self.analyzer = AutoCombinedAnalyzer()
        else:
            raise ValueError(f"Unsupported provider: {self.provider}")

    def analyze(self, text: str):
        return self.analyzer.analyze(text)
