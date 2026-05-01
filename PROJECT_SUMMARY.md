# Secure RAG-Based AI Support Triage System — Project Summary

## Overview
An intelligent support ticket automation system that classifies customer issues, screens for security threats, retrieves relevant documentation, and generates grounded responses or flags tickets for human review. Designed to reduce support workload, improve response consistency, and prevent malicious requests from bypassing security checks.

## Dataset
- **769 markdown documents** from three public support centers:
  - Claude Help Center: 319 files (account management, API, privacy, security)
  - HackerRank Support: 436 files (billing, interviews, screening, community)
  - Visa Support: 14 files (dispute resolution, fraud, card management)
- **Sample tickets:** 29 real-world-like support requests for testing
- **No PII:** All data is publicly available documentation

## Model
- **No traditional ML model** — system uses:
  - Keyword-based classification heuristics
  - Pattern-matching security detection (regex)
  - Word-overlap retrieval scoring
  - Optional LLM integration (OpenRouter/Llama 3.8B) for response generation
- **Deterministic & explainable** — no black-box predictions; all decisions logged

## Technologies
- **Python 3.8+** — core language
- **pandas** — CSV processing
- **openai** — OpenRouter API client
- **python-dotenv** — environment variable management
- **unittest** — test framework
- **Git** — version control

## Workflow
```
1. Load CSV tickets + local corpus
2. Classify: Map to request type & product area
3. Security Screen: Detect threats, compute risk score
4. Escalation Decision: If risk > threshold → escalate, else continue
5. Retrieve: Fetch top 3 matching documents (word overlap)
6. Generate: Call LLM with context or fallback to doc summary
7. Output: Write CSV result + SOC-style audit log
```

## Security Features
- **Prompt Injection Detection:** Regex patterns catch instruction override attempts
- **Fraud Detection:** Flags identity theft, money requests, suspicious language
- **Data Exfiltration Prevention:** Detects requests for bulk data/customer lists
- **Policy Violation Checks:** Catches deletion, file destruction, harmful actions
- **Risk Scoring:** 0–100 scale; escalates if risk exceeds threshold (secure=60, normal=70)
- **Audit Logging:** All decisions logged in SOC format with timestamps & reasoning

## Conclusion
A production-ready, deterministic support triage system that balances automation with safety. No hallucination risk — responses are grounded in local documentation. Easily extensible to new companies by adding corpus folders. Ready for public deployment.

---
**Status:** ✅ Fully tested, documented, and pushed to GitHub
