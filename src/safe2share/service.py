# Orchestrator holds a reference to the active Strategy
import logging
from .config import settings
from .providers import Provider

from .analyzers.base import BaseAnalyzer
from .analyzers.rule_based import RuleBasedAnalyzer
from .analyzers.llm_openai_compat import OpenAICompatibleAnalyzer
from .analyzers.auto_combined import AutoCombinedAnalyzer
from .models import AnalysisResult

logger = logging.getLogger(__name__)


class Safe2ShareService:
    def __init__(self, provider: Provider | None = None):
        self.provider = provider or settings.provider

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