# Analizer that runs multiple models and merges their results.

import logging
from ..analyzers.base import BaseAnalyzer
from ..analyzers.rule_based import RuleBasedAnalyzer

from ..analyzers.llm_openai_compat import OpenAICompatibleAnalyzer
from ..models import AnalysisResult, map_score_to_risk

logger = logging.getLogger(__name__)


class AutoCombinedAnalyzer(BaseAnalyzer):
    """
    A composite analyzer that runs multiple strategies (AI and Rule-Based) 
    and merges the results, taking the most severe outcome.
    """

    def __init__(self, rule_analyzer: RuleBasedAnalyzer, ai_analyzer: OpenAICompatibleAnalyzer):
        self.rule_analyzer = rule_analyzer
        self.ai_analyzer = ai_analyzer

    def analyze(self, text: str) -> AnalysisResult:
        """Runs both AI and Rule-Based analysis and merges the results."""
        
        try:
            ai_res = self.ai_analyzer.analyze(text)
        except Exception as exc:
            logger.warning("AI analyzer failed, returning Rule-Based result: %s", exc)
            # Fallback
            return self.rule_analyzer.analyze(text)

        rule_res = self.rule_analyzer.analyze(text)

        final_score = max(ai_res.score, rule_res.score)
        final_risk = map_score_to_risk(final_score)
        
        merged_reasons = list(dict.fromkeys(ai_res.reasons + rule_res.reasons))
        merged_detections = ai_res.detections + rule_res.detections
        
        # Prefer AI suggested rewrites if they exist
        suggested = ai_res.suggested_rewrites or rule_res.suggested_rewrites

        return AnalysisResult(
            risk=final_risk,
            score=final_score,
            reasons=merged_reasons,
            detections=merged_detections,
            suggested_rewrites=suggested,
            metadata={
                "mode": "auto", 
                "ai_score": str(ai_res.score), 
                "rule_score": str(rule_res.score)
            },
        )