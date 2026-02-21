
# Safe2Share Confidentiality & Escalation Policy

Safe2Share is designed to minimize accidental data leakage when interacting with AI systems.
It uses a layered detection approach balancing privacy, performance, and accuracy.


##  Threat Model

Primary risk addressed:

• Sensitive information unintentionally pasted into AI tools  
• Credentials, secrets, PII, and proprietary data leaving secure environments  

This tool is not a full enterprise DLP replacement — it is a fast preflight safety layer.


##  Local Rule Engine

The local analyzer uses deterministic patterns to detect:

• passwords, tokens, API keys  
• emails and phone numbers  
• cryptographic material  
• high-entropy secrets  

### Advantages
✔️ fast  
✔️ offline  
✔️ zero data exposure  
✔️ predictable behavior  

### Limitations
• may miss obfuscated or non-standard secrets  
• limited semantic understanding  


## LLM Analyzer

Optional LLM analysis provides:

• semantic interpretation  
• contextual risk detection  
• complex PII recognition  

LLM usage is fully optional and configurable.


##  AUTO Escalation Strategy

AUTO mode runs local analysis first and escalates only when:

### Confirmed Risk
• local engine reports CONFIDENTIAL or HIGHLY_CONFIDENTIAL

### High-Risk Intent Hints
Examples:
• “safe code”
• “PIN”
• “one-time password”
• “security token”
• “vault code”

This ensures privacy-first behavior while catching subtle cases.


## Failure Handling

If LLM provider is unavailable:

AUTO mode safely falls back to local analysis.

No failures block usage.


## False Positives & Negatives

All detection systems trade precision and recall:

| Risk | Explanation |
|--||
| False positives | benign content flagged |
| False negatives | sensitive content missed |

Safe2Share prioritizes:

✔️ strong signal detection  
✔️ transparent output  
✔️ safe defaults  


## Privacy Principles

• local-first by default  
• no telemetry  
• no cloud dependency required  
• explicit opt-in for LLM usage  


##  Extensibility

Future enhancements include:

• NER-based detection models  
• policy-aware classification via RAG  
• organization-specific rule tuning  


Safe2Share is intended as a safety guardrail, not a compliance product.
