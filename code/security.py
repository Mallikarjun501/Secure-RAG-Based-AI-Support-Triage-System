from __future__ import annotations

import os
import re


MODE = os.getenv("MODE", "secure").strip().lower()
if MODE not in {"secure", "normal"}:
    MODE = "secure"

SECURE_THRESHOLD = 60
NORMAL_THRESHOLD = 70


def _contains_any(text: str, patterns: list[str]) -> bool:
    return any(pattern in text for pattern in patterns)


def detect_prompt_injection(issue: str) -> bool:
    """Detect instruction override, prompt leakage, and malicious command attempts."""
    text = issue.lower()

    patterns = [
        r"ignore (?:all|the)? previous instructions",
        r"disregard (?:all|the)? previous instructions",
        r"override (?:the )?(?:system|developer|assistant)?(?: instructions| prompt)?",
        r"show (?:me )?(?:the )?(?:system prompt|internal rules|developer message|instructions)",
        r"reveal (?:the )?(?:instructions|logic|policy)",
        r"internal logic",
        r"prompt injection",
        r"system prompt",
        r"developer message",
        r"delete all files",
        r"rm\s+-rf",
        r"drop table",
        r"format c:",
        r"bypass security",
        r"exfiltrat",
    ]

    return any(re.search(pattern, text) for pattern in patterns)


def classify_security_threat(issue: str) -> str:
    """Return a cybersecurity threat label for the ticket content."""
    text = issue.lower()

    if detect_prompt_injection(issue):
        if _contains_any(text, ["delete all files", "rm -rf", "drop table", "format c:"]):
            return "policy_violation"
        if _contains_any(text, ["show internal rules", "show system prompt", "internal logic", "reveal the instructions"]):
            return "prompt_injection"
        if _contains_any(text, ["all documents", "all data", "export all", "dump data", "customer list", "download database"]):
            return "data_exfiltration"
        return "prompt_injection"

    fraud_patterns = [
        "fraud",
        "identity theft",
        "identity stolen",
        "stolen card",
        "stolen",
        "blocked card",
        "chargeback",
        "unauthorised charge",
        "unauthorized charge",
    ]
    if _contains_any(text, fraud_patterns):
        return "fraud_risk"

    exfiltration_patterns = [
        "export all",
        "download all",
        "dump data",
        "customer list",
        "all records",
        "all documents",
        "send me the database",
        "give me the logs",
        "extract data",
    ]
    if _contains_any(text, exfiltration_patterns):
        return "data_exfiltration"

    policy_patterns = [
        "delete all files",
        "hack ",
        "exploit",
        "bypass",
        "jailbreak",
        "override",
        "move me to the next round",
        "increase my score",
        "change my result",
    ]
    if _contains_any(text, policy_patterns):
        return "policy_violation"

    return "benign"


def compute_risk_score(issue: str, request_type: str) -> int:
    """Compute a 0-100 risk score for the ticket."""
    threat = classify_security_threat(issue)

    threat_scores = {
        "prompt_injection": 95,
        "data_exfiltration": 90,
        "fraud_risk": 85,
        "policy_violation": 75,
        "benign": 20,
    }
    request_scores = {
        "invalid": 75,
        "bug": 35,
        "feature_request": 25,
        "product_issue": 20,
    }

    score = threat_scores[threat]
    if threat == "benign":
        score = request_scores.get(request_type, 25)

    if MODE == "secure" and score < 90:
        score += 5

    return min(score, 100)


def decision_engine(issue: str, request_type: str, company: str | None = None) -> tuple[bool, str, int]:
    """Return escalation decision, attack type, and risk score."""
    attack_type = classify_security_threat(issue)
    risk_score = compute_risk_score(issue, request_type)
    threshold = SECURE_THRESHOLD if MODE == "secure" else NORMAL_THRESHOLD

    if request_type == "invalid":
        attack_type = attack_type if attack_type != "benign" else "policy_violation"
        risk_score = max(risk_score, 75)

    if company and str(company).lower() == "visa" and attack_type == "benign":
        if _contains_any(issue.lower(), ["blocked", "fraud", "identity", "stolen", "cash"]):
            attack_type = "fraud_risk"
            risk_score = max(risk_score, 85)

    escalate = risk_score > threshold
    return escalate, attack_type, risk_score
