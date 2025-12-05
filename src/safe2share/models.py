# Pydantic models (requests/responses)

from pydantic import BaseModel, Field, BeforeValidator
from typing import List, Literal, Dict, Any, Annotated


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
    text: str = Field(..., description="The text content to be analyzed for sensitive data.")
    
    # Optional field that aligns with the mode parameter in your service
    mode: Literal["rule", "ai", "hybrid", "default"] = Field(
        None, 
        description="Optional: Overrides the default analyzer mode (rule, ai, hybrid)."
    )