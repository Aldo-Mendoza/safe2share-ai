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

        logger.info("Safe2Share initialized with provider=%s analyzer=%s",
                    self.provider.value, self.analyzer.__class__.__name__)

    def analyze(self, text: str):
        return self.analyzer.analyze(text)

    def _build_analyzer(self, provider: Provider):
        if provider == Provider.LOCAL:
            return RuleBasedAnalyzer()

        if provider == Provider.LLM:
            # Uses OpenAI-compatible endpoint (OpenAI, Ollama, LM Studio, etc.)
            return OpenAICompatibleAnalyzer()

        if provider == Provider.AUTO:
            # Day 5: implement "local-first then escalate to LLM" behavior.
            # Day 4: keep predictable by defaulting to LOCAL behavior.
            return RuleBasedAnalyzer()

        raise ValueError(f"Unsupported provider: {provider}")

    @staticmethod
    def _unavailable_error(provider: Provider) -> RuntimeError:
        if provider == Provider.LLM:
            return RuntimeError(
                "Provider 'llm' selected but no LLM configuration is available.\n"
                "Set these environment variables:\n"
                "  S2S_LLM_BASE_URL (e.g., http://127.0.0.1:11434/v1)\n"
                "  S2S_LLM_MODEL (e.g., llama3.1:latest)\n"
                "Optional:\n"
                "  S2S_LLM_API_KEY (required for some hosted providers)\n"
                "Or use: --provider local"
            )

        # For completeness, though LOCAL should never be unavailable.
        return RuntimeError(f"Provider '{provider.value}' selected but analyzer is unavailable.")
