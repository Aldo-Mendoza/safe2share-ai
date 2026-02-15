import re
from typing import List, Dict
from .base import BaseAnalyzer
from ..models import AnalysisResult, Detection, map_score_to_risk


class PatternDetector:
    def __init__(self, label: str, regex: str, base_score: int):
        self.label = label
        self.regex = re.compile(regex, re.IGNORECASE | re.MULTILINE)
        self.base_score = base_score

    def find(self, text: str) -> List[Detection]:
        results = []
        for match in self.regex.finditer(text):
            span = match.group(0)
            results.append(
                Detection(
                    label=self.label,
                    span=span,
                    score=self.base_score,
                )
            )
        return results


class RuleBasedAnalyzer(BaseAnalyzer):
    """
    Deterministic local confidentiality scanner using regex-based detectors.
    """

    DETECTORS = [
        # Password-like fields
        PatternDetector("CREDENTIAL", r"(password|pass|pwd)\s*[:=]\s*\S+", 90),

        # Generic tokens/secrets
        PatternDetector(
            "SECRET", r"(token|secret|api[_\s]?key)\s*[:=]\s*\S+", 85),

        # JWT tokens
        PatternDetector(
            "JWT", r"eyJ[A-Za-z0-9_-]{20,}\.[A-Za-z0-9_-]{20,}\.[A-Za-z0-9_-]{10,}", 95),

        # OpenAI-like keys
        PatternDetector("API_KEY", r"sk-[A-Za-z0-9]{20,}", 95),

        # Emails
        PatternDetector(
            "EMAIL", r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}", 40),

        # Phone numbers
        PatternDetector("PHONE", r"\+?\d[\d\s\-\(\)]{8,}\d", 35),

        # Private key blocks
        PatternDetector(
            "PRIVATE_KEY", r"-----BEGIN (RSA|DSA|EC|OPENSSH)? PRIVATE KEY-----", 100),

        # High-entropy long strings (possible secrets)
        PatternDetector("HIGH_ENTROPY", r"[A-Za-z0-9+/]{32,}={0,2}", 60),
    ]

    KEYWORD_BOOSTERS = {
        "password": 20,
        "secret": 15,
        "token": 15,
        "private": 20,
        "api": 10,
        "key": 10,
        "credential": 15,
    }

    @property
    def is_available(self) -> bool:
        # Local deterministic analyzer is always available
        return True


    def analyze(self, text: str) -> AnalysisResult:
        detections: List[Detection] = []

        for detector in self.DETECTORS:
            detections.extend(detector.find(text))

        if not detections:
            return AnalysisResult(
                risk="PUBLIC",
                score=0,
                reasons=["No sensitive patterns found"],
                detections=[],
                suggested_rewrites=[],
                metadata={"analyzer": "rule_engine_v3"},
            )

        # Boost scores if contextual keywords appear
        lower = text.lower()
        for det in detections:
            for kw, boost in self.KEYWORD_BOOSTERS.items():
                if kw in lower:
                    det.score = min(100, det.score + boost)

        # Aggregate score (max + mild stacking)
        max_score = max(d.score for d in detections)
        stacked_bonus = min(15, len(detections) * 5)
        final_score = min(100, max_score + stacked_bonus)

        risk = map_score_to_risk(final_score)

        reasons = [
            f"Detected {d.label}: '{d.span[:40]}...'" for d in detections]

        # Basic rewrite (replace sensitive spans)
        redacted = text
        for d in detections:
            redacted = redacted.replace(d.span, "[REDACTED]")

        return AnalysisResult(
            risk=risk,
            score=final_score,
            reasons=reasons,
            detections=detections,
            suggested_rewrites=[redacted],
            metadata={"analyzer": "rule_engine_v3"},
        )
