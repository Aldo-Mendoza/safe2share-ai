# Safe2Share Architecture

Safe2Share is built using a Strategy-based modular design that cleanly separates:

• orchestration  
• detection engines  
• policy logic  


## Core Components

### Safe2ShareService (Orchestrator)

Selects analyzer strategy based on provider:

• LOCAL → RuleBasedAnalyzer  
• LLM → OpenAICompatibleAnalyzer  
• AUTO → AutoCombinedAnalyzer  

Provides single `analyze(text)` entrypoint.


### Analyzer Interface

All analyzers implement:

```python
analyze(text) -> AnalysisResult
is_available -> bool

```

This allows seamless swapping of detection engines.


### RuleBasedAnalyzer

Deterministic regex-based detection engine:

• secrets  
• credentials  
• PII  
• cryptographic artifacts

Local-first and always available.


### OpenAICompatibleAnalyzer

LLM-powered semantic classifier supporting:

• Ollama (local)  
• OpenAI  
• Azure OpenAI  
• any OpenAI-compatible endpoint


### AutoCombinedAnalyzer

Policy-based orchestrator that:

1.  runs local analysis
2.  evaluates escalation rules
3.  optionally invokes LLM
4.  safely falls back if unavailable


## System Flow Diagram

```mermaid
flowchart TD
    A[Input: text or file] --> B[CLI / API]
    B --> C[Safe2ShareService]
    C --> D{Provider?}

    D -->|local| E[RuleBasedAnalyzer]
    D -->|llm| F[OpenAICompatibleAnalyzer]
    D -->|auto| G[AutoCombinedAnalyzer]

    G --> H[RuleBasedAnalyzer]
    H --> I{Escalate?}
    I -->|no| J[Return local result]
    I -->|yes & LLM available| K[OpenAICompatibleAnalyzer]
    I -->|yes & LLM unavailable| L[Return local result + metadata]

    E --> M[AnalysisResult]
    F --> M
    J --> M
    K --> M
    L --> M

    M --> N[Output: JSON + suggested rewrites]

```

## UML Class Diagram

```mermaid
classDiagram
    direction TB

    class Settings {
      +provider: Provider
      +llm_base_url: str?
      +llm_model: str?
      +llm_api_key: str?
    }

    class Safe2ShareService {
      +provider: Provider
      +analyzer: BaseAnalyzer
      +analyze(text): AnalysisResult
    }

    class BaseAnalyzer {
      <<interface>>
      +is_available: bool
      +analyze(text): AnalysisResult
    }

    class RuleBasedAnalyzer {
      +DETECTORS
      +analyze(text): AnalysisResult
      +is_available: bool
    }

    class OpenAICompatibleAnalyzer {
      +base_url: str
      +model: str
      +analyze(text): AnalysisResult
      +is_available: bool
    }

    class AutoPolicy {
      +escalate_risks: tuple
      +escalate_hints: tuple
    }

    class AutoCombinedAnalyzer {
      +policy: AutoPolicy
      +local: BaseAnalyzer
      +llm: BaseAnalyzer
      +analyze(text): AnalysisResult
      +is_available: bool
    }

    class AnalysisResult {
      +risk: RiskLevel
      +score: int
      +reasons: List[str]
      +detections: List[Detection]
      +suggested_rewrites: List[str]
      +metadata: dict
    }

    class Detection {
      +label: str
      +span: str
      +score: int
      +start: int?
      +end: int?
    }

    Settings --> Safe2ShareService : config
    Safe2ShareService --> BaseAnalyzer : selects/uses
    BaseAnalyzer <|.. RuleBasedAnalyzer
    BaseAnalyzer <|.. OpenAICompatibleAnalyzer
    BaseAnalyzer <|.. AutoCombinedAnalyzer
    AutoCombinedAnalyzer --> AutoPolicy
    AutoCombinedAnalyzer --> BaseAnalyzer : local
    AutoCombinedAnalyzer --> BaseAnalyzer : llm
    AnalysisResult --> Detection

```


## Packaging

Safe2Share is distributed as a Python package with:

• CLI entrypoint  
• API server entrypoint  
• editable install for development


##  Testing Strategy

• rule engine unit tests  
• auto escalation policy tests  
• provider failure handling



This architecture enables future additions such as:

• ML classifiers  
• RAG policy engines  
• file scanning pipelines  
• agentic workflows