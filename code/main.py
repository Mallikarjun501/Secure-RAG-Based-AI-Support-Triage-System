from __future__ import annotations

from datetime import datetime, timedelta
from pathlib import Path

import pandas as pd

from classification import classify_product_area, classify_request_type
from llm import generate_response
from retrieval import load_documents, retrieve_docs
from security import MODE, decision_engine


ROOT_DIR = Path(__file__).resolve().parent.parent
INPUT_PATH = ROOT_DIR / "support_tickets" / "support_tickets.csv"
OUTPUT_PATH = ROOT_DIR / "support_tickets" / "output.csv"
LOG_PATH = ROOT_DIR / "log.txt"

ESCALATION_RESPONSE = (
    "This issue requires attention from our specialist team. "
    "Please contact official support directly for secure, personalised assistance. "
    "We apologise for any inconvenience."
)


def _now() -> datetime:
    return datetime.now().astimezone()


def _format_bool(value: bool) -> str:
    return "true" if value else "false"


def _normalize_field(value: object) -> str:
    if value is None or pd.isna(value):
        return ""
    return str(value).strip()


def _summarize_docs(domain_docs: dict[str, list[str]]) -> str:
    return (
        f"HackerRank={len(domain_docs['hackerrank'])}, "
        f"Claude={len(domain_docs['claude'])}, "
        f"Visa={len(domain_docs['visa'])}, "
        f"Global={len(domain_docs['all'])}"
    )


def _write_soc_log(records: list[dict], domain_docs: dict[str, list[str]], started_at: datetime) -> None:
    lines: list[str] = []
    lines.append("[SUPPORT TRIAGE SYSTEM]")
    lines.append(f"[Session started: {started_at.isoformat(timespec='seconds')}]")
    lines.append("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    lines.append("")
    lines.append(f"[{started_at.isoformat(timespec='seconds')}] [SYSTEM]")
    lines.append("Batch run started. Processing support tickets from support_tickets/support_tickets.csv")
    lines.append(f"Mode: {MODE}")
    lines.append("Architecture: domain-scoped RAG + LLM (OpenRouter Llama)")
    lines.append(f"Domain corpus: {_summarize_docs(domain_docs)}")
    lines.append("")
    lines.append("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    lines.append("")

    for offset, record in enumerate(records, start=1):
        ts = (started_at + timedelta(seconds=offset)).isoformat(timespec='seconds')
        lines.append(f"[{ts}] [{record['module']}]")
        lines.append(f"Ticket {record['ticket_id']} | Company: {record['company']}")
        lines.append(f"Decision: {record['status'].upper()}")
        lines.append(f"Security Flag: {record['security_flag']}")
        lines.append(f"Attack Type: {record['attack_type']}")
        lines.append(f"Risk Score: {record['risk_score']}")
        lines.append(f"Security Reason: {record['security_reason']}")
        lines.append(f"Request Type: {record['request_type']} | Product Area: {record['product_area']}")
        lines.append("")

    summary_ts = (started_at + timedelta(seconds=len(records) + 1)).isoformat(timespec='seconds')
    replied = sum(1 for record in records if record["status"] == "replied")
    escalated = sum(1 for record in records if record["status"] == "escalated")
    lines.append(f"[{summary_ts}] [SYSTEM]")
    lines.append("Batch run complete. All tickets processed successfully")
    lines.append(f"Output written to: {OUTPUT_PATH.relative_to(ROOT_DIR)}")
    lines.append(f"Total tickets: {len(records)} | Replied: {replied} | Escalated: {escalated}")
    lines.append("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")

    LOG_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")


def process_tickets(domain_docs: dict[str, list[str]] | None = None) -> list[dict]:
    df = pd.read_csv(INPUT_PATH)
    if domain_docs is None:
        domain_docs = load_documents(ROOT_DIR / "data")

    output_rows: list[dict] = []

    print(f"Loaded {len(df)} tickets from {INPUT_PATH.relative_to(ROOT_DIR)}", flush=True)
    print(f"Domain corpus: {_summarize_docs(domain_docs)}", flush=True)

    for idx, row in df.iterrows():
        ticket_id = idx + 1
        issue = _normalize_field(row.get("Issue", ""))
        subject = _normalize_field(row.get("Subject", ""))
        company = _normalize_field(row.get("Company", ""))

        print(f"[{ticket_id:02d}/{len(df):02d}] {company} | {subject}", flush=True)

        request_type = classify_request_type(issue)
        product_area = classify_product_area(issue, company)
        escalate, attack_type, risk_score = decision_engine(issue, request_type, company)
        security_flag = _format_bool(attack_type != "benign" or risk_score >= 70)

        if escalate:
            status = "escalated"
            response = ESCALATION_RESPONSE
            justification = f"Security threat='{attack_type}', risk_score={risk_score}, mode={MODE}, escalated=True"
            security_reason = f"Escalation triggered for {attack_type}"
            module = "SECURITY"
            print(f"    -> ESCALATED | attack={attack_type} | risk={risk_score}", flush=True)
        else:
            retrieved_docs = retrieve_docs(issue, domain_docs, company)
            response = generate_response(issue, retrieved_docs, company)
            status = "replied"
            justification = (
                f"Type='{request_type}', Area='{product_area}', Retrieved={len(retrieved_docs)}, "
                f"Security='{attack_type}', Risk={risk_score}, mode={MODE}"
            )
            security_reason = "No active security threat detected"
            module = "TRIAGE"
            print(f"    -> REPLIED | area={product_area} | risk={risk_score} | docs={len(retrieved_docs)}", flush=True)

        output_rows.append(
            {
                "ticket_id": ticket_id,
                "issue": issue,
                "subject": subject,
                "company": company,
                "status": status,
                "product_area": product_area,
                "request_type": request_type,
                "response": response,
                "justification": justification,
                "security_flag": security_flag,
                "attack_type": attack_type,
                "risk_score": risk_score,
                "security_reason": security_reason,
                "module": module,
            }
        )

    return output_rows


def main() -> None:
    started_at = _now()
    print("Starting support triage pipeline...", flush=True)
    domain_docs = load_documents(ROOT_DIR / "data")
    rows = process_tickets(domain_docs)

    out_df = pd.DataFrame(
        rows,
        columns=[
            "ticket_id",
            "status",
            "product_area",
            "request_type",
            "response",
            "justification",
            "security_flag",
            "attack_type",
            "risk_score",
            "issue",
            "subject",
            "company",
        ],
    )

    out_df[[
        "ticket_id",
        "status",
        "product_area",
        "request_type",
        "response",
        "justification",
        "security_flag",
        "attack_type",
        "risk_score",
    ]].to_csv(OUTPUT_PATH, index=False)

    _write_soc_log(rows, domain_docs, started_at)

    replied = sum(1 for row in rows if row["status"] == "replied")
    escalated = sum(1 for row in rows if row["status"] == "escalated")
    print(f"Done. Output written to {OUTPUT_PATH.relative_to(ROOT_DIR)}", flush=True)
    print(f"Replied: {replied} | Escalated: {escalated}", flush=True)


if __name__ == "__main__":
    main()