import logging
from fastapi import Request
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from pathlib import Path
from fastapi import FastAPI, HTTPException

from .models import AnalyzeRequest, AnalysisResult
from .service import Safe2ShareService


app = FastAPI(title="Safe2Share")

BASE_DIR = Path(__file__).resolve().parent
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))
app.mount("/static", StaticFiles(directory=str(BASE_DIR / "static")), name="static")

MAX_TEXT_CHARS = 200_000
logger = logging.getLogger(__name__)


@app.get("/", response_class=HTMLResponse)
def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})



@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


@app.post("/analyze", response_model=AnalysisResult)
def analyze(req: AnalyzeRequest) -> AnalysisResult:
    try:
        if len(req.text) > MAX_TEXT_CHARS:
            raise HTTPException(
                status_code=413,
                detail=f"Text too large ({len(req.text)} chars). Limit is {MAX_TEXT_CHARS}."
            )
        svc = Safe2ShareService(provider=req.provider)
        return svc.analyze(req.text)
    except HTTPException:
        raise
    except RuntimeError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception:
        logger.exception("Unhandled error in /analyze")
        raise HTTPException(status_code=500, detail="Internal error")


