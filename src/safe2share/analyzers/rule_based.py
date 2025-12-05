# RuleBasedAnalyzer
import re
import logging

from ..analyzers.base import BaseAnalyzer
from ..models import AnalysisResult, Detection, map_score_to_risk

logger = logging.getLogger(__name__)


# Simple keyword lists and regex for demo purposes
KEYWORDS = {
    "HIGHLY_CONFIDENTIAL": [
        "password", "social security", "ssn", "credit card", "cvv", "private key", "secret key"
    ],
    "CONFIDENTIAL": [
        "internal use only", "confidential", "salary", "employee id", "contract", "ssn"
    ],
    "INTERNAL": [
        "do not distribute", "internal", "proprietary", "restricted"
    ],
}

# Personally Identifiable Information
PII_PATTERNS = {
    "email": re.compile(r"[a-zA-Z0-9.\-_+]+@[a-zA-Z0-9\-_]+\.[a-zA-Z.\-]{2,}"),
    "phone": re.compile(r"\+?\d[\d\-\s]{7,}\d"),
    "credit_card": re.compile(r"(?:\d[ -]*?){13,16}"),
    "ssn_like": re.compile(r"\b\d{3}-\d{2}-\d{4}\b"),
}

# Weight applied for EACH instance of PII found.
PII_WEIGHTS = {
    "email": 2,
    "phone": 3,
    "credit_card": 15,
    "ssn_like": 20,
}


RISK_SCORES = {
    "PUBLIC": 0,
    "INTERNAL": 25,
    "CONFIDENTIAL": 60,
    "HIGHLY_CONFIDENTIAL": 90,
}


def find_keyword_matches(text: str):
    matches = []
    lowered = text.lower()
    for level, kws in KEYWORDS.items():
        for kw in kws:
            if kw in lowered:
                matches.append((level, kw))
    return matches


class RuleBasedAnalyzer(BaseAnalyzer):
    def __init__(self):
        self.keywords = KEYWORDS
        self.patterns = PII_PATTERNS

    @property
    def is_available(self) -> bool:
        """
        The rule-based analyzer relies only on internal constants. Always available.
        """
        return True

    def analyze(self, text: str) -> AnalysisResult:
        detections = []
        
        max_detection_score = 0  # Highest single score found (e.g., 90 for password)
        cumulative_weight_score = 0 # Score accumulated from multiple low-risk items

        reasons = []

        # PII checks: Calculates cumulative_weight_score
        for label, pat in self.patterns.items():
            for m in pat.finditer(text):
                base_score = RISK_SCORES['CONFIDENTIAL']
                
                # Apply base score and add to weight
                weight = PII_WEIGHTS.get(label, 5)
                cumulative_weight_score += weight
                
                # Update detection list and max score (if PII score is higher)
                detections.append(
                    Detection(label=label.upper(), span=m.group(0), score=base_score)
                )
                max_detection_score = max(max_detection_score, base_score)
                reasons.append(f"Detected {label} pattern: {m.group(0)} (Weight: +{weight})")
                logger.debug("PII match %s -> %s", label, m.group(0))

        # Keyword matches
        for level, kws in self.keywords.items():
            for kw in kws:
                if kw.lower() in text.lower():
                    level_score = RISK_SCORES.get(level, 50)
                    
                    # Keywords instantly update the max score
                    max_detection_score = max(max_detection_score, level_score)
                    
                    detections.append(
                        Detection(label=level, span=kw, score=level_score))
                    reasons.append(
                        f"Found keyword '{kw}' with sensitivity {level} (Score: {level_score})")
                    logger.debug("Keyword match %s -> %s", kw, level)

        # Heuristic: presence of many numeric sequences (could be credentials)
        numeric_sequences = re.findall(r"\b\d{6,}\b", text)
        if len(numeric_sequences) >= 1:
            seq_score = RISK_SCORES['CONFIDENTIAL']
            detections.append(Detection(label="NUMERIC_SEQUENCE", span=", ".join(numeric_sequences), score=seq_score))
            max_detection_score = max(max_detection_score, seq_score)
            reasons.append("Detected long numeric sequences that may be account numbers or tokens")

        # Simple entropy heuristic for secrets (base64-like)
        base64_like = re.findall(r"[A-Za-z0-9+/]{20,}={0,2}", text)
        if base64_like:
            secret_score = 85
            detections.append(Detection(label="POTENTIAL_SECRET", span=base64_like[0], score=secret_score))
            max_detection_score = max(max_detection_score, secret_score)
            reasons.append("Detected high-entropy token-like string (could be secret key)")

        # Calculate the potential score from aggregation
        aggregated_score = max_detection_score + cumulative_weight_score


        # TODO:
        # Apply bounds to prevent low-risk items from pushing score past critical levels
        # It also shouldn't jump from CONFIDENTIAL (60) to HIGHLY_CONFIDENTIAL (90)
        # just because of low-weight items, but for simplicity, we cap it at 100.
        final_score = min(100, aggregated_score)  # The score cannot go higher than 100.

        # Ensure the final score is at least the highest single score found
        score = max(final_score, max_detection_score)

        # Map score to risk label
        risk = map_score_to_risk(score)


        if cumulative_weight_score > 0 and score > max_detection_score:
            reasons.insert(
                0, f"Score increased by {cumulative_weight_score} due to multiple PII/sensitive items.")

        # Suggested rewrites: simple redaction examples
        suggested_rewrites = []
        if detections:
            redact = text
            for d in detections:
                redact = redact.replace(d.span, "[REDACTED]")
            suggested_rewrites.append(redact)
            suggested_rewrites.append("Remove personal identifiers (emails, phone numbers, account numbers).")

        return AnalysisResult(
            risk=risk,
            score=score,
            reasons=reasons or ["No sensitive patterns found"],
            detections=detections,
            suggested_rewrites=suggested_rewrites,
            metadata={"analyzer": "rule_based_v2_aggregated"},
        )
