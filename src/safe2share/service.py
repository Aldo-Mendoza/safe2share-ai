# Orchestrator holds a reference to the active Strategy
import logging
from .config import settings
from .providers import Provider

from .analyzers.base import BaseAnalyzer
from .analyzers.rule_based import RuleBasedAnalyzer
from .analyzers.openai_analyzer import OpenAIGPTAnalyzer
from .analyzers.auto_combined import AutoCombinedAnalyzer
from .models import AnalysisResult

logger = logging.getLogger(__name__)


class Safe2ShareService:
    def __init__(self, provider: Provider | None = None):
        self.provider = provider or settings.provider

        # Day 1: Keep behavior simple.
        # Map provider to analyzer.
        if self.provider == Provider.LOCAL:
            self.analyzer = RuleBasedAnalyzer()
        elif self.provider == Provider.LLM:
            self.analyzer = OpenAIGPTAnalyzer()
            if hasattr(self.analyzer, "is_available") and not self.analyzer.is_available:
                raise RuntimeError(
                    "Provider 'llm' selected but no LLM configuration is available. "
                    "Set S2S_LLM_BASE_URL / S2S_LLM_MODEL (and S2S_LLM_API_KEY if required), "
                    "or use --provider local."
                )
        elif self.provider == Provider.AUTO:
            # For Day 1: start with local to keep it predictable.
            # Day 3+ can combine.
            self.analyzer = RuleBasedAnalyzer()
        else:
            raise ValueError(f"Unsupported provider: {self.provider}")

    def analyze(self, text: str):
        return self.analyzer.analyze(text)


# class Safe2ShareService:

#     ANALYZER_REGISTRY_CLASSES = {
#         "rule": RuleBasedAnalyzer,
#         "local": RuleBasedAnalyzer,  # Alias for rule
#         "openai": OpenAIGPTAnalyzer,
#         # "llama": LlamaLocalAnalyzer,
#         # "azure": AzureGPTAnalyzer,
#     }

#     def __init__(self, mode: str | None = None, ):
#         self.mode = mode or settings.MODE
#         # Central Registry
#         self.analyzers: dict[str, BaseAnalyzer] = {
#             mode_key: AnalyzerClass()
#             for mode_key, AnalyzerClass in self.ANALYZER_REGISTRY_CLASSES.items()
#         }

#         self.analyzer = self._get_active_analyzer()

#         logger.info(
#             f"Service initialized. Requested mode: {self.mode}. Active Analyzer: {self.analyzer.__class__.__name__}")


#     def _get_active_analyzer(self) -> BaseAnalyzer:
#         """Selects the appropriate analyzer model based on mode and availability."""

#         # Handle explicit AI mode
#         if self.mode in self.analyzers:
#             ai_model = self.analyzers[self.mode]
#             if ai_model.is_available:
#                 return ai_model
#             else:
#                 logger.warning(
#                     f"{self.mode.upper()} Analyzer is unavailable. Falling back to Rule-Based.")
#                 return self.analyzers["rule"]

#         if self.mode == "auto":
#             # Combined strategy
#             ai_instance = self.analyzers["openai"] 
#             rule_instance = self.analyzers["rule"]
            
#             # If AI is available, use AutoCombined, otherwise fall back to RuleBased
#             if ai_instance.is_available:
#                  # TODO: Refactor to take instances
#                 return AutoCombinedAnalyzer(rule_instance, ai_instance)
#             else:
#                 return rule_instance
        
#         # Default fallback
#         return self.analyzers["rule"]
        
#     def analyze(self, text: str) -> AnalysisResult:
#         return self.analyzer.analyze(text)
    
#     def analyze_with_info(self, text: str) -> tuple[AnalysisResult, str]:
#         """
#         Executes analysis and returns the result along with the name 
#         of the concrete analyzer strategy that was actually used.
#         """
#         result = self.analyzer.analyze(text)
        
#         analyzer_name = self.analyzer.__class__.__name__.replace('Analyzer', '').lower()
        
#         if isinstance(self.analyzer, AutoCombinedAnalyzer):
#             analyzer_name = "auto"
        
#         return result, analyzer_name