# FastAPI app

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from .models import AnalyzeRequest, AnalysisResult
from .service import Safe2ShareService
from .logconfig import logger
import uvicorn
from pathlib import Path
import os

BASE_DIR = Path(__file__).resolve().parent
TEMPLATES_DIR = BASE_DIR / "templates"
templates = Jinja2Templates(directory=TEMPLATES_DIR)

app = FastAPI(title="Safe2Share AI", version="1.2")
service = Safe2ShareService()


@app.get("/", response_class=HTMLResponse)
async def root(request: Request):
    """Serves the index.html page."""
    return templates.TemplateResponse("index.html", {"request": request})


@app.post("/analyze", response_model=AnalysisResult)
async def analyze(req: AnalyzeRequest):
    try:
        if req.mode:
            svc = Safe2ShareService(mode=req.mode)
            result = svc.analyze(req.text)
        else:
            result = service.analyze(req.text)
        return result
    except Exception as exc:
        logger.exception("analyze failed")
        raise HTTPException(status_code=500, detail=str(exc))


if __name__ == "__main__":
    uvicorn.run("src.safe2share.main:app",
                host="0.0.0.0", port=8000, reload=True)
