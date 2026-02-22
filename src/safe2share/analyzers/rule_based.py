import re
from typing import List

from ..models import AnalysisResult, Detection, map_score_to_risk
from .base import BaseAnalyzer


class PatternDetector:
    def __init__(self, label: str, regex: str, base_score: int, redact_group: int = 0):
        self.label = label
        self.regex = re.compile(regex, re.IGNORECASE | re.MULTILINE)
        self.base_score = base_score
        self.redact_group = redact_group

    def find(self, text: str) -> List[Detection]:
        results: List[Detection] = []
        for m in self.regex.finditer(text):
            # Choose which part of the match is the sensitive span
            try:
                span = m.group(self.redact_group)
                start, end = m.span(self.redact_group)
            except IndexError:
                span = m.group(0)
                start, end = m.span(0)

            results.append(
                Detection(
                    label=self.label,
                    span=span,
                    score=self.base_score,
                    start=start,
                    end=end,
                )
            )
        return results


class RuleBasedAnalyzer(BaseAnalyzer):
    """
    Deterministic local confidentiality scanner using regex-based detectors.
    """

    DETECTORS = [
        # Password-like fields
        PatternDetector(
            "CREDENTIAL",
            r"(?:password|pass|pwd)\s*(?:[:=]|is)\s*([^\s,.;]+)",
            90,
            redact_group=1,
        ),
        # Generic tokens/secrets
        PatternDetector(
            "SECRET",
            r"(?:token|secret|api[_\s]?key)\s*[:=]\s*([^\s,.;]+)",
            85,
            redact_group=1,
        ),
        # JWT tokens
        PatternDetector(
            "JWT", r"eyJ[A-Za-z0-9_-]{20,}\.[A-Za-z0-9_-]{20,}\.[A-Za-z0-9_-]{10,}", 95
        ),
        # OpenAI-like keys
        PatternDetector("API_KEY", r"(sk-[A-Za-z0-9]{20,})", 95, redact_group=1),
        # Emails
        PatternDetector("EMAIL", r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}", 40),
        # Phone numbers
        PatternDetector("PHONE", r"\+?\d[\d\s\-\(\)]{8,}\d", 35),
        # Private key blocks
        PatternDetector(
            "PRIVATE_KEY", r"-----BEGIN (?:RSA|DSA|EC|OPENSSH)?\s*PRIVATE KEY-----", 100
        ),
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

    HIGH_ENTROPY_HINT_WORDS = (
        "token",
        "secret",
        "api",
        "key",
        "password",
        "bearer",
        "credential",
        "jwt",
    )

    @property
    def is_available(self) -> bool:
        # Local deterministic analyzer is always available
        return True

    def analyze(self, text: str) -> AnalysisResult:
        detections: List[Detection] = []

        # 1) Run all detectors
        for detector in self.DETECTORS:
            detections.extend(detector.find(text))

        # Early return if nothing matched
        if not detections:
            return AnalysisResult(
                risk="PUBLIC",
                score=0,
                reasons=["No sensitive patterns found"],
                detections=[],
                suggested_rewrites=[],
                metadata={"analyzer": "rule_engine_v3"},
            )

        lower = text.lower()

        # 2) False-positive guard for HIGH_ENTROPY:
        # Keep HIGH_ENTROPY only if hint words exist somewhere in the text.
        has_entropy_hints = any(w in lower for w in self.HIGH_ENTROPY_HINT_WORDS)
        filtered: List[Detection] = []
        for d in detections:
            if d.label == "HIGH_ENTROPY" and not has_entropy_hints:
                continue
            filtered.append(d)
        detections = filtered

        # If filtering removed everything, treat as safe
        if not detections:
            return AnalysisResult(
                risk="PUBLIC",
                score=0,
                reasons=["No sensitive patterns found"],
                detections=[],
                suggested_rewrites=[],
                metadata={"analyzer": "rule_engine_v3"},
            )

        # 3) Keyword boosters (contextual bump)
        for det in detections:
            for kw, boost in self.KEYWORD_BOOSTERS.items():
                if kw in lower:
                    det.score = min(100, det.score + boost)

        # 4) Aggregate score (max + mild stacking)
        max_score = max(d.score for d in detections)
        stacked_bonus = min(15, len(detections) * 5)
        final_score = min(100, max_score + stacked_bonus)

        risk = map_score_to_risk(final_score)

        reasons = [f"Detected {d.label}: '{d.span[:40]}...'" for d in detections]

        # 5) Rewrite using offsets (safer than global replace)
        spans = sorted(
            [d for d in detections if d.start is not None and d.end is not None],
            key=lambda x: x.start,
        )

        if spans:
            redacted_parts: List[str] = []
            cursor = 0
            for d in spans:
                if d.start < cursor:
                    # Overlapping span; skip (merge logic can be added later)
                    continue
                redacted_parts.append(text[cursor : d.start])
                redacted_parts.append("[REDACTED]")
                cursor = d.end
            redacted_parts.append(text[cursor:])
            redacted = "".join(redacted_parts)
        else:
            # Fallback if offsets are missing for any reason
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
