# Secure RAG-Based AI Support Triage System

An AI-driven support ticket triage system that classifies customer issues, retrieves relevant documentation, applies security screening, and autonomously generates grounded responses or flags tickets for human escalation.

---

## Table of Contents

- [Problem Statement](#problem-statement)
- [Proposed Solution](#proposed-solution)
- [How It Works](#how-it-works)
- [Pipeline](#pipeline)
- [Results and Metrics](#results-and-metrics)
- [Datasets](#datasets)
- [Project Structure](#project-structure)
- [Setup and Usage](#setup-and-usage)
- [Limitations](#limitations)
- [Future Improvements](#future-improvements)

---

## Problem Statement

Support teams across organizations handle thousands of incoming tickets daily, many of which are repetitive FAQs or routine requests that do not require human intervention. Manual triage is time-consuming and error-prone, leading to:

- **High operational cost** — human agents spend time on tickets that could be auto-resolved.
- **Slow response times** — common issues remain unaddressed in queues.
- **Inconsistent replies** — different team members answer the same question differently.
- **Security risk** — malicious or trick requests may not be caught in time.
- **Knowledge fragmentation** — support docs are scattered and hard to search at scale.

The goal is to automate the triage and initial response process while maintaining safety, consistency, and grounding in verified documentation.

---

## Proposed Solution

The Secure RAG-Based AI Support Triage System combines:

1. **Classification Engine** — routes tickets to the correct product area and request type using keyword-based heuristics.
2. **Security Layer** — detects prompt injection, fraud, data exfiltration, and policy violations before response generation.
3. **Retrieval-Augmented Generation (RAG)** — grounds responses in local, verified documentation.
4. **LLM Integration** — generates concise, contextual replies when confident; escalates when uncertain or unsafe.
5. **Logging & Auditability** — logs all decisions in SOC-style format for compliance and debugging.

The system is deterministic, offline-capable, and avoids hallucination by design.

---

## How It Works

The system processes support tickets in a linear pipeline:

```
CSV Input → Classification → Security Check → Risk Scoring
                                    ↓
                            Yes: Escalate
                                    ↓ No
                            Document Retrieval
                                    ↓
                    Grounded Response Generation
                                    ↓
                        CSV Output + Audit Log
```

**Step 1: Ticket Input**  
Reads `support_tickets/support_tickets.csv` with columns: `Issue`, `Subject`, `Company`.

**Step 2: Request Classification**  
Maps the ticket to:
- A **request type**: `product_issue`, `feature_request`, `bug`, or `invalid`.
- A **product area**: e.g., `account_management`, `billing`, `security`, `privacy`, etc.

Uses keyword matching and company context to route the ticket.

**Step 3: Security Screening**  
Evaluates the ticket for malicious or risky intent:
- Detects instruction override attempts.
- Flags fraud, data theft, or policy violation language.
- Computes a 0–100 **risk score**.
- Sets an **attack type** label: `prompt_injection`, `fraud_risk`, `data_exfiltration`, `policy_violation`, or `benign`.

**Step 4: Escalation Decision**  
If risk score exceeds the threshold (60 in secure mode, 70 in normal mode), the ticket is escalated. Otherwise, proceeds to retrieval.

**Step 5: Document Retrieval**  
Loads the local corpus and retrieves the top 3 matching documents using simple word overlap scoring:
- Scoped to the company's corpus first (HackerRank, Claude, or Visa).
- Falls back to global corpus if no strong match found.

**Step 6: Response Generation**  
If an OpenRouter API key is available, calls the LLM to generate a short response grounded in the retrieved docs. Otherwise, falls back to a summary of the best match.

**Step 7: Output & Logging**  
Writes the final decision row to the output CSV and logs the decision in SOC format.

---

## Pipeline

### Component: `code/classification.py`
- **Input:** Issue text, company name
- **Output:** request_type, product_area
- **Logic:** Keyword matching and company-specific heuristics

### Component: `code/security.py`
- **Input:** Issue text, request_type, company name
- **Output:** (escalate: bool, attack_type: str, risk_score: int)
- **Logic:** Regex pattern matching for malicious phrases, threat classification, risk scoring

### Component: `code/retrieval.py`
- **Input:** Issue text, domain corpus, company name
- **Output:** List of top 3 matching documents
- **Logic:** Word-overlap scoring, company-scoped fallback

### Component: `code/llm.py`
- **Input:** Issue text, retrieved docs, company name
- **Output:** Grounded response string
- **Logic:** Calls OpenRouter API if key is present; else returns doc summary

### Component: `code/main.py`
- **Orchestrates** the pipeline
- **Reads** CSV input and loads corpus
- **Writes** output CSV and SOC log
- **Handles** errors gracefully

---

## Results and Metrics

When running on a sample of 29 support tickets:

- **Total Tickets Processed:** 29
- **Successfully Replied:** 24 (83%)
- **Escalated:** 5 (17%)

**Escalation Breakdown:**
- Policy Violations: 2
- Fraud Risk: 3

**Example Output Row:**
```csv
ticket_id,status,product_area,request_type,response,justification,security_flag,attack_type,risk_score
1,replied,account_management,product_issue,"Thank you for contacting support...",Type='product_issue'...,false,benign,25
```

**Audit Log Example:**
```
[2026-05-01T17:20:51+05:30] [TRIAGE]
Ticket 1 | Company: Claude
Decision: REPLIED
Security Flag: false
Attack Type: benign
Risk Score: 25
Security Reason: No active security threat detected
Request Type: product_issue | Product Area: account_management
```

---

## Datasets

The system is bundled with local support documentation for three companies:

### Claude Support Corpus
- **Source:** Claude Help Center snapshots
- **Topics:** Account management, API integration, privacy, security, conversation management, platform reliability
- **Count:** ~320 markdown files

### HackerRank Support Corpus
- **Source:** HackerRank Support site snapshots
- **Topics:** Assessments, billing, interviews, hiring, account management, certifications, community
- **Count:** ~438 markdown files

### Visa Support Corpus
- **Source:** Visa consumer and small-business support
- **Topics:** Travel support, dispute resolution, fraud security, cash access, card policy, card access
- **Count:** ~14 markdown files

**Total:** ~772 markdown documents across all three corpora.

**Data Format:** Plain markdown with metadata headers (title, URL, timestamps).

**No Personal Data:** All support documentation is public-facing; no customer PII is included.

---

## Project Structure

```text
Secure RAG-Based AI Support Triage System/
├── README.md                           # This file
├── .env.example                        # Environment template
├── .gitignore                          # Git ignore rules
├── code/                               # Source code
│   ├── __init__.py
│   ├── main.py                         # Pipeline orchestration
│   ├── classification.py               # Ticket routing
│   ├── security.py                     # Threat detection & risk scoring
│   ├── retrieval.py                    # Document loading & ranking
│   └── llm.py                          # Response generation
├── data/                               # Local support corpus
│   ├── claude/                         # Claude Help Center docs
│   │   ├── index.md
│   │   ├── account-management/
│   │   ├── api-faq/
│   │   ├── privacy-and-legal/
│   │   └── ...
│   ├── hackerrank/                     # HackerRank support docs
│   │   ├── index.md
│   │   ├── billing/
│   │   ├── screen/
│   │   ├── interview/
│   │   └── ...
│   └── visa/                           # Visa support docs
│       ├── index.md
│       ├── support/
│       └── ...
└── support_tickets/                    # Input & output
    ├── support_tickets.csv             # Input: tickets to triage
    ├── sample_support_tickets.csv      # Reference examples
    └── output.csv                      # Output: final decisions (generated)
```

**Generated Files (not committed):**
- `support_tickets/output.csv`
- `log.txt`
- `code/__pycache__/`

---

## Setup and Usage

### Prerequisites

- Python 3.8 or later
- `pip` for package management
- Optional: OpenRouter / OpenAI API key for live response generation

### Installation (recommended)

1. Clone the repository and open the project root:
   ```bash
   git clone https://github.com/Mallikarjun501/Secure-RAG-Based-AI-Support-Triage-System.git
   cd "Secure RAG-Based AI Support Triage System"
   ```

2. Create and activate a virtual environment:

   - Windows PowerShell:
     ```powershell
     python -m venv .venv
     Set-ExecutionPolicy -Scope Process -ExecutionPolicy RemoteSigned; .\.venv\Scripts\Activate.ps1
     ```

   - Windows CMD:
     ```cmd
     python -m venv .venv
     .venv\Scripts\activate.bat
     ```

   - macOS / Linux:
     ```bash
     python -m venv .venv
     source .venv/bin/activate
     ```

3. Install dependencies from the bundled manifest:
   ```bash
   pip install -r "AI Support Triage System/requirements.txt"
   ```

4. Copy the environment template and set secrets:
   ```bash
   copy "AI Support Triage System\.env.example" "AI Support Triage System\.env"  # Windows
   ```
   Then edit `AI Support Triage System/.env` and set values, e.g.:
   ```text
   OPENAI_API_KEY=sk-...
   OPENROUTER_MODEL=meta-llama/llama-3-8b-instruct
   MODE=secure
   ```

### Running the Agent

Run from the repository root (recommended):

```bash
python run.py
```

Or run the pipeline module directly from inside the nested project folder:

```bash
python -m code.main
```

Outputs written by a run (by default) are placed under `AI Support Triage System/support_tickets/`:

- `output.csv` — generated decisions for the input tickets
- `log.txt` — SOC-style audit log

### Tests

Run the unit tests with the standard library test runner or `pytest`:

```bash
python -m unittest discover -s "AI Support Triage System/tests"
# or
pytest "AI Support Triage System/tests"
```

### Cleanup: remove generated outputs from version control

If `AI Support Triage System/support_tickets/output.csv` has been committed accidentally, remove it from tracking:

```bash
git rm --cached "AI Support Triage System/support_tickets/output.csv"
git commit -m "chore: remove generated output.csv from repo"
git push
```

### Notes

- `requirements.txt` has been added to pin the minimal dependencies used by the project.
- Prefer running `python run.py` from the repo root to ensure the nested package path is configured correctly.
- If you intend to use a remote LLM, ensure `OPENAI_API_KEY` (or equivalent) is set in the copied `.env` file.


---

## Limitations

1. **Keyword-Based Routing:** Classification relies on keyword matching; complex or novel tickets may be misrouted.
2. **No Live Context:** Responses are only grounded in the bundled corpus; real-time product changes are not reflected.
3. **Simple Retrieval:** Document ranking uses basic word overlap; semantic similarity would improve recall.
4. **LLM Dependency:** Response quality depends on the underlying LLM model and API availability.
5. **Language:** Currently optimized for English; multi-language support is not implemented.
6. **No Machine Learning:** No learning from feedback or historical patterns.
7. **Company Scope:** The system is trained on three companies (Claude, HackerRank, Visa); extending to new companies requires manual corpus updates.

---

## Future Improvements

1. **Semantic Retrieval:** Replace word overlap with embeddings-based retrieval (e.g., using FAISS or Pinecone).
2. **Fine-Tuned Model:** Train a custom LLM on historical ticket data to improve classification and response accuracy.
3. **Feedback Loop:** Integrate user feedback to continuously improve routing and escalation thresholds.
4. **Multi-Language Support:** Extend classification and retrieval to support multiple languages.
5. **Real-Time Corpus Updates:** Implement live corpus refresh from official support APIs.
6. **Interactive Dashboard:** Build a web UI for monitoring, logging, and manual review of escalated tickets.
7. **Advanced Security:** Expand threat detection using graph-based anomaly detection or deep learning models.
8. **Integration with Ticketing Systems:** Connect directly to Jira, Zendesk, Salesforce, or other support platforms.
9. **Performance Optimization:** Add caching, batch processing, and async APIs for high-throughput scenarios.
10. **Explainability:** Add detailed reasoning traces and confidence scores for each decision.
