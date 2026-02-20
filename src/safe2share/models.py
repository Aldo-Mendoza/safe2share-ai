from typing import Dict, List, Literal, Optional

from pydantic import BaseModel, Field

from .providers import Provider


# Risk level definitions
RiskLevel = Literal["PUBLIC", "INTERNAL",
                    "CONFIDENTIAL", "HIGHLY_CONFIDENTIAL"]

# Thresholds (score -> risk)
RISK_THRESHOLDS: List[tuple[int, RiskLevel]] = [
    (85, "HIGHLY_CONFIDENTIAL"),
    (60, "CONFIDENTIAL"),
    (25, "INTERNAL"),
    (0, "PUBLIC"),
]


def map_score_to_risk(score: int) -> RiskLevel:
    """Maps a numerical score (0-100) to a RiskLevel."""
    for threshold, risk in RISK_THRESHOLDS:
        if score >= threshold:
            return risk
    return "PUBLIC"


class Detection(BaseModel):
    label: str = Field(...,
                       description="Detection category (e.g., SECRET, EMAIL, JWT).")
    span: str = Field(..., description="Exact matched text span.")
    score: int = Field(..., ge=0, le=100,
                       description="Severity score for this detection (0-100).")

    # Optional offsets (useful for UI highlighting later)
    start: Optional[int] = Field(
        None, ge=0, description="Start char index of span in the original text.")
    end: Optional[int] = Field(
        None, ge=0, description="End char index (exclusive) of span in the original text.")


class AnalysisResult(BaseModel):
    risk: RiskLevel = Field(..., description="Final risk classification.")
    score: int = Field(..., ge=0, le=100,
                       description="Overall risk score (0-100).")

    reasons: List[str] = Field(
        default_factory=list, description="Human-readable explanations.")
    detections: List[Detection] = Field(
        default_factory=list, description="Structured detections.")
    suggested_rewrites: List[str] = Field(
        default_factory=list, description="Safer rewritten variants.")
    metadata: Dict[str, str] = Field(
        default_factory=dict, description="Extra info (provider, model, analyzer, etc.).")


class AnalyzeRequest(BaseModel):
    text: str = Field(..., min_length=1, description="Text to analyze.")
    provider: Provider = Field(
        default=Provider.LOCAL, description="Analysis provider (local|llm|auto).")
