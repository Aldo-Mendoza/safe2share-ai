from __future__ import annotations

import json
import re
from typing import Any, Dict, List

from openai import OpenAI

from .base import BaseAnalyzer
from ..config import settings
from ..models import AnalysisResult, Detection, map_score_to_risk
from .prompts import (PROMPT_V1, PROMPT_V2_REDACT_FULL)


SYSTEM_PROMPT = PROMPT_V2_REDACT_FULL


class OpenAICompatibleAnalyzer(BaseAnalyzer):
    """
    LLM analyzer that talks to any OpenAI-compatible endpoint.

    Works with:
      - OpenAI cloud (base_url=https://api.openai.com/v1)
      - Ollama OpenAI-compat (base_url=http://localhost:11434/v1)
      - LM Studio OpenAI-compat (base_url=http://localhost:1234/v1)
    """

    def __init__(self) -> None:
        self._is_ready = bool(settings.llm_base_url and settings.llm_model)

        # Some local servers don't require a key; OpenAI client needs a string.
        api_key = settings.llm_api_key or "local"

        self._client = OpenAI(base_url=settings.llm_base_url, api_key=api_key)

    @property
    def is_available(self) -> bool:
        return self._is_ready

    def analyze(self, text: str) -> AnalysisResult:
        if not self.is_available:
            raise RuntimeError(
                "LLM analyzer not configured. Set S2S_LLM_BASE_URL and S2S_LLM_MODEL."
            )

        resp = self._client.chat.completions.create(
            model=settings.llm_model,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": text},
            ],
            temperature=0,
            response_format={"type": "json_object"},
        )

        content = resp.choices[0].message.content or ""
        data = self._safe_parse_json(content)

        if not data or "score" not in data:
            raise RuntimeError(
                "LLM returned an unparseable response (expected strict JSON). "
                "Try again, switch model, or use --provider local."
            )

        score = int(data.get("score", 0))
        reasons = self._to_list_of_str(data.get("reasons", []))
        suggested_rewrites = self._to_list_of_str(
            data.get("suggested_rewrites", []))

        detections: List[Detection] = []
        for d in data.get("detections", []) or []:
            try:
                detections.append(
                    Detection(
                        label=str(d.get("label", "UNKNOWN")),
                        span=str(d.get("span", "")),
                        score=int(d.get("score", score)),
                    )
                )
            except Exception:
                # Don't let a malformed detection crash the tool
                continue

        return AnalysisResult(
            risk=map_score_to_risk(score),
            score=score,
            reasons=reasons,
            detections=detections,
            suggested_rewrites=suggested_rewrites,
            metadata={
                "provider": "llm",
                "model": settings.llm_model or "",
                "base_url": settings.llm_base_url or "",
            },
        )

    @staticmethod
    def _safe_parse_json(text: str) -> Dict[str, Any]:
        """
        Robust JSON extraction:
        - Models sometimes wrap JSON in ```json fences or include extra text.
        - We extract the first JSON object and parse it.
        """
        text = text.strip()

        # If model returned a fenced block, prefer it
        fenced = re.search(
            r"```(?:json)?\s*(\{.*?\})\s*```", text, flags=re.DOTALL | re.IGNORECASE)
        if fenced:
            candidate = fenced.group(1)
            try:
                return json.loads(candidate)
            except Exception:
                pass

        # Otherwise, grab first {...} block
        match = re.search(r"\{.*\}", text, flags=re.DOTALL)
        if not match:
            return {}

        candidate = match.group(0)
        try:
            return json.loads(candidate)
        except Exception:
            return {}

    @staticmethod
    def _to_list_of_str(value: Any) -> List[str]:
        if isinstance(value, list):
            return [str(v) for v in value]
        if value is None:
            return []
        return [str(value)]
