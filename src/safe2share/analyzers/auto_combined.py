from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from ..models import AnalysisResult
from .base import BaseAnalyzer
from .llm_openai_compat import OpenAICompatibleAnalyzer
from .rule_based import RuleBasedAnalyzer


@dataclass
class AutoPolicy:
    # Escalate to LLM when local result indicates meaningful risk
    escalate_risks: tuple[str, ...] = ("CONFIDENTIAL", "HIGHLY_CONFIDENTIAL")
    escalate_hints: tuple[str, ...] = (
        "code to my safe",
        "safe code",
        "passcode",
        "pin",
        "otp",
        "one-time code",
        "security code",
        "vault code",
        "door code",
    )


class AutoCombinedAnalyzer(BaseAnalyzer):
    """
    Local-first analyzer. Runs rule-based detection first, then optionally escalates to LLM.
    """

    def __init__(
        self,
        local: Optional[BaseAnalyzer] = None,
        llm: Optional[BaseAnalyzer] = None,
        policy: Optional[AutoPolicy] = None,
    ):
        self.local = local or RuleBasedAnalyzer()
        self.llm = llm or OpenAICompatibleAnalyzer()
        self.policy = policy or AutoPolicy()

    @property
    def is_available(self) -> bool:
        # AUTO is always "available" because local is always available.
        # LLM might not be available, but we can still run local.
        return True

    def analyze(self, text: str) -> AnalysisResult:
        local_res = self.local.analyze(text)

        text_l = text.lower()
        hint_trigger = any(h in text_l for h in self.policy.escalate_hints)

        should_escalate = (local_res.risk in self.policy.escalate_risks) or hint_trigger

        # Always record local result in metadata
        local_meta = {
            "auto_local_risk": local_res.risk,
            "auto_local_score": str(local_res.score),
            "auto_escalated": str(should_escalate).lower(),
            "auto_hint_triggered": str(hint_trigger).lower(),
        }

        # If not escalating, return local
        if not should_escalate:
            local_res.metadata = {
                **(local_res.metadata or {}),
                **local_meta,
                "provider": "auto",
                "auto_path": "local_only",
            }
            return local_res

        # Escalate only if LLM is available
        if hasattr(self.llm, "is_available") and not self.llm.is_available:
            local_res.metadata = {
                **(local_res.metadata or {}),
                **local_meta,
                "provider": "auto",
                "auto_path": "local_only_llm_unavailable",
            }
            return local_res

        llm_res = self.llm.analyze(text)

        # Attach auto metadata + preserve LLM metadata (model/base_url)
        llm_res.metadata = {
            **(llm_res.metadata or {}),
            **local_meta,
            "provider": "auto",
            "auto_path": "escalated_to_llm",
        }
        return llm_res
