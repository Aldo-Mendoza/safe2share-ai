# Pydantic models (requests/responses)

from pydantic import BaseModel, Field, BeforeValidator
from typing import List, Literal, Dict, Any, Annotated
from .providers import  Provider


# Risk level definitions
RiskLevel = Literal["PUBLIC", "INTERNAL", "CONFIDENTIAL", "HIGHLY_CONFIDENTIAL"]

# Thresholds
RISK_THRESHOLDS: List[tuple[int, RiskLevel]] = [
    (85, "HIGHLY_CONFIDENTIAL"),
    (60, "CONFIDENTIAL"),
    (25, "INTERNAL"),
    (0, "PUBLIC"),
]


def map_score_to_risk(score: int) -> RiskLevel:
    """Maps a numerical score to a defined RiskLevel."""
    for threshold, risk in RISK_THRESHOLDS:
        if score >= threshold:
            return risk
    return "PUBLIC"  # Default fallback


class Detection(BaseModel):
    label: str
    span: str
    score: int


class AnalysisResult(BaseModel):
    risk: RiskLevel = Field(..., description="The final risk classification.")
    score: int = Field(..., description="The overall risk score (0-100).")
    reasons: List[str]
    detections: List[Detection] = []
    suggested_rewrites: List[str] = []
    metadata: Dict[str, str] = {}


class AnalyzeRequest(BaseModel):
    text: str = Field(..., min_length=1, description="Text to analyze")
    provider: Provider = Field(
        default=Provider.LOCAL, description="Analysis provider")


class AnalyzeResponse(BaseModel):
    pass
