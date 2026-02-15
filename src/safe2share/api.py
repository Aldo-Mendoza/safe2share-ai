from fastapi import FastAPI, HTTPException

from .models import AnalyzeRequest, AnalysisResult
from .service import Safe2ShareService

app = FastAPI(title="Safe2Share", version="0.1.0")


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


@app.post("/analyze", response_model=AnalysisResult)
def analyze(req: AnalyzeRequest) -> AnalysisResult:
    try:
        svc = Safe2ShareService(provider=req.provider)
        return svc.analyze(req.text)
    except RuntimeError as e:
        # Configuration issues / provider unavailable
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        # Unexpected errors
        raise HTTPException(status_code=500, detail="Internal error")
