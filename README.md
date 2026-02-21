# 🛡️ Safe2Share AI — Local-First Confidentiality Scanner for AI Workflows

[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg?style=flat-square&logo=python)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/Framework-FastAPI-009688.svg?style=flat-square&logo=fastapi)](https://fastapi.tiangolo.com/)
[![Testing](https://img.shields.io/badge/Tests-Pytest-009688.svg?style=flat-square&logo=pytest)](https://docs.pytest.org/)
![CI](https://github.com/Aldo-Mendoza/safe2share-ai/actions/workflows/ci.yml/badge.svg)
[![License](https://img.shields.io/badge/License-MIT-green.svg?style=flat-square)](LICENSE)

Local-first tool that detects and redacts sensitive information before text is shared with AI systems.

**Modes**
- **local**: deterministic rule engine (offline & fast)
- **llm**: OpenAI-compatible provider (Ollama / OpenAI / LM Studio)
- **auto**: runs local first, escalates to LLM only when needed

---

## 🚀 Quickstart

## Installation

Create a virtual environment (recommended):

```bash
python -m venv .venv
source .venv/bin/activate   # macOS/Linux
# .\.venv\Scripts\Activate.ps1   # Windows
```
Istall in editable mode:

```bash
pip install -e ".[dev]"
```


### Web UI (recommended demo)

```bash
safe2share-api --reload
````

Open: `http://127.0.0.1:8000/`

---

### CLI — local rules (offline)

```bash
safe2share "My password is Mac&Cheese4" --provider local --json
```

Example output:
```json
{
  "risk": "HIGHLY_CONFIDENTIAL",
  "score": 100,
  "reasons": [
    "Detected CREDENTIAL: 'Mac&Cheese4...'"
  ],
  "detections": [
    {
      "label": "CREDENTIAL",
      "span": "Mac&Cheese4",
      "score": 100,
      "start": 15,
      "end": 26
    }
  ],
  "suggested_rewrites": [
    "My password is [REDACTED]"
  ],
  "metadata": {
    "analyzer": "rule_engine_v3"
  }
}
```

Scan a file:

```bash
safe2share --file notes.txt --provider local --json
```

---

### CLI — LLM provider (OpenAI-compatible)

LLM mode needs runtime config in the **same terminal session** running the command (or use Docker).

**macOS/Linux**

```bash
export S2S_LLM_BASE_URL=http://127.0.0.1:11434/v1
export S2S_LLM_MODEL=llama3.1:latest
# export S2S_LLM_API_KEY=... (only for hosted providers)
```

**Windows PowerShell**

```powershell
$env:S2S_LLM_BASE_URL="http://127.0.0.1:11434/v1"
$env:S2S_LLM_MODEL="llama3.1:latest"
# $env:S2S_LLM_API_KEY="..."  # only for hosted providers
```

Run:

```bash
safe2share "My password is 12345" --provider llm --json
```

---

### AUTO mode (recommended)

AUTO runs locally first and escalates to LLM only when:

* sensitive patterns are detected, or
* high-risk intent phrases appear (e.g., “safe code”, “PIN”, “secret”)

```bash
safe2share "the code to my safe is 87362" --provider auto --json
```

Falls back safely if the LLM is unavailable.

---

## 🐳 Docker demo

Run API + UI (local-only):

```bash
docker compose up --build
```

Open: `http://127.0.0.1:8000/`

Optional: run API + UI + local LLM (Ollama):

```bash
docker compose -f docker-compose.ollama.yml up --build
```

Note: Docker is the easiest way to demo the project without installing Python or models manually.

---

## Core features

* Local regex-based detection (secrets, credentials, keys, basic PII patterns)
* Optional LLM classification via OpenAI-compatible APIs (Ollama/OpenAI/LM Studio)
* Policy-driven auto escalation (minimizes data exposure)
* Safe-to-share redacted rewrite
* CLI + FastAPI + browser UI
* Unit tests for rule engine and auto policy

---

## Architecture

Strategy pattern:

* `RuleBasedAnalyzer` (local)
* `OpenAICompatibleAnalyzer` (LLM)
* `AutoCombinedAnalyzer` (policy orchestrator)

Diagrams: `docs/architecture.md`
Policy: `docs/policy.md`

---

## Tests

```bash
pytest -q
```