# 🛡️ Safe2Share AI: Confidentiality Guard for AI Workflows

[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg?style=flat-square&logo=python)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/Framework-FastAPI-009688.svg?style=flat-square&logo=fastapi)](https://fastapi.tiangolo.com/)
[![Testing](https://img.shields.io/badge/Tests-Pytest-009688.svg?style=flat-square&logo=pytest)](https://docs.pytest.org/)
[![License](https://img.shields.io/badge/License-MIT-green.svg?style=flat-square)](LICENSE)

Local-first Confidential Information Checker that analyzes text before it is shared with AI tools or external services. Includes rule-based detection, optional AI analyzer, FastAPI demo, and extensible architecture.

## 1. Project Overview

Safe2Share AI is a **confidentiality analysis service** designed to act as a crucial gatekeeper *before* text is submitted to external or proprietary AI systems (like OpenAI, Claude, or internal LLMs).

Its primary purpose is to **mitigate data leakage** by identifying sensitive information—such including personal data, academic or institutional data, credentials, and proprietary code—and providing immediate, actionable guidance to the user.

### Aligned with Responsible AI & Privacy

* **Responsible AI:** The project enforces the principle of **privacy by design**. Instead of relying on a black-box AI to police sensitive data, Safe2Share aims to use predictable rules and clear risk scoring to prevent the exposure of data to *any* downstream system, promoting ethical and safe use of GenAI tools.
* **University Context:** This tool directly addresses confidentiality risks within an academic setting where sensitive student or research data must never leave a secure environment. It supports staff and students in safe prompt engineering practices.

***

## 2. Why This Project Matters (Addressing Confidentiality Risks)

The integration of AI into modern workflows presents a critical new attack vector: **accidental data exposure via prompts.**

Safe2Share AI is a proof-of-concept that demonstrates a scalable solution to this risk:

1.  **Eliminates Accidental Exposure:** By analyzing text *locally* (via the Rule-based analyzer) or securely (via a configurable API), the tool guides users to redact sensitive details, ensuring clean, safe inputs for the AI system.
2.  **Mitigates Hallucinations:** The project addresses the core AI challenge of **hallucinations** indirectly. Since the output of the *Analyzer* is deterministic and auditable, it is a **trustworthy source** for security decisions, unlike relying on an LLM for classification.
3.  **Supports Developer Workflow:** It provides both a powerful **CLI** for batch processing and a **FastAPI** endpoint for easy integration into web applications or CI/CD pipelines.

***

## 3. Architecture Overview & Features

Safe2Share AI is built on the **Strategy Pattern** 

```mermaid
classDiagram
    direction TB
    
    class AnalysisResult {
        + risk: RiskLevel
        + score: int
        + detections: List<Detection>
    }

    class BaseAnalyzer {
        <<interface>>
        + analyze(text): AnalysisResult
    }
    
    class Safe2ShareService {
        + analyzer: BaseAnalyzer
        + __init__(mode)
        + analyze(text): AnalysisResult
    }
    
    class RuleBasedAnalyzer {
        + analyze(text): AnalysisResult
    }
    
    class AIAnalyzer {
        + analyze(text): AnalysisResult
    }
    
    class HybridAnalyzer {
        + analyze(text): AnalysisResult
    }
    
    
    %% Relationships
    
    %% Safe2ShareService (Context) has a reference to BaseAnalyzer (Composition/Association)
    Safe2ShareService "1" *-- "1" BaseAnalyzer : uses >
    
    %% Concrete Strategies implement the BaseAnalyzer interface
    BaseAnalyzer <|-- RuleBasedAnalyzer : implements
    BaseAnalyzer <|-- AIAnalyzer : implements
    BaseAnalyzer <|-- HybridAnalyzer : implements
    
    %% Analyzers produce an AnalysisResult
    RuleBasedAnalyzer --> AnalysisResult : produces
    AIAnalyzer --> AnalysisResult : produces
    HybridAnalyzer --> AnalysisResult : produces

 to achieve **Modularity** and **Separation of Concerns**. This design allows the core service logic to seamlessly swap analysis engines without modification.

### Core Architecture Components

* **Strategy Pattern:** The `Safe2ShareService` (Context) delegates the analysis task to different `Analyzer` implementations (Strategies).
* **BaseAnalyzer (Interface):** Defines the contract (`analyze(text) -> AnalysisResult`).
* **RuleBasedAnalyzer (Concrete Strategy):** **Local, deterministic, and always available.** Uses regex and keywords to calculate risk (0-100 score). This is the default, most private, and fastest mode.
* **AIAnalyzer (Concrete Strategy):** Uses the OpenAI API (or a configurable local LLM) for enhanced, contextual classification.

```mermaid
flowchart TD
    A[User Input] --> B[Safe2ShareService]
    B --> C{Select Analyzer}

    C -->|rule| D[RuleBasedAnalyzer]
    C -->|ai| E[AIAnalyzer]
    C -->|hybrid| F[HybridAnalyzer]

    D --> G[AnalysisResult]
    E --> G
    F --> G

    G --> H[Output]

