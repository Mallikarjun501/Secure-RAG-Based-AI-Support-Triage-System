from __future__ import annotations

import re


def _contains_any(text: str, patterns: list[str]) -> bool:
    return any(pattern in text for pattern in patterns)


def classify_request_type(issue: str) -> str:
    """Classify a ticket into the requested support workflow buckets."""
    text = issue.lower()

    invalid_signals = [
        "delete all files",
        "hack ",
        "exploit",
        "bypass",
        "jailbreak",
        "show internal rules",
        "show system prompt",
        "internal logic",
        "show me your instructions",
        "what is the capital",
        "who won",
    ]
    if _contains_any(text, invalid_signals):
        return "invalid"

    bug_signals = [
        "not working",
        "isn't working",
        "doesn't work",
        "stopped working",
        "stopped in between",
        "error",
        "failed",
        "failing",
        "down",
        "crashed",
        "broken",
        "unable to",
        "can not",
        "cannot",
        "blocker",
        "submission",
        "submissions not",
        "site is down",
    ]
    if _contains_any(text, bug_signals):
        return "bug"

    feature_signals = [
        "feature request",
        "can you add",
        "would love to see",
        "extend inactivity",
        "inactivity time",
        "reschedule",
        "can we extend",
        "it would be great if",
    ]
    if _contains_any(text, feature_signals):
        return "feature_request"

    return "product_issue"


def classify_product_area(issue: str, company: str) -> str:
    """Map a ticket to the most relevant support area."""
    text = issue.lower()
    company_name = str(company).lower()

    if company_name == "visa":
        if _contains_any(text, ["travel", "cheque", "abroad", "lisbon", "trip", "foreign"]):
            return "travel_support"
        if _contains_any(text, ["dispute", "chargeback", "wrong product", "merchant"]):
            return "dispute_resolution"
        if _contains_any(text, ["stolen", "lost card", "identity", "fraud"]):
            return "fraud_security"
        if _contains_any(text, ["cash", "atm", "withdraw", "emergency"]):
            return "cash_access"
        if _contains_any(text, ["minimum spend", "surcharge", "fee", "limit"]):
            return "card_policy"
        if _contains_any(text, ["blocked", "declined", "cannot use"]):
            return "card_access"
        return "general_support"

    if company_name == "hackerrank":
        if _contains_any(
            text,
            [
                "test",
                "assessment",
                "score",
                "result",
                "graded",
                "evaluate",
                "invite",
                "reinvite",
                "candidate",
                "recruiter",
                "variant",
                "active",
                "expir",
                "duration",
            ],
        ):
            return "screen"
        if _contains_any(
            text,
            ["payment", "refund", "billing", "subscription", "invoice", "charge", "paid", "money", "order id"],
        ):
            return "billing"
        if _contains_any(text, ["interview", "mock interview", "inactivity", "interviewer", "candidate kicked", "room", "video"]):
            return "interview"
        if _contains_any(text, ["zoom", "proctoring", "compatible", "compatibility", "camera", "screen share", "record"]):
            return "proctoring"
        if _contains_any(text, ["account", "login", "delete account", "remove user", "employee", "seat", "admin", "access", "permission"]):
            return "account_management"
        if _contains_any(text, ["resume", "apply", "job", "practice", "challenge", "submission", "code editor"]):
            return "community"
        if _contains_any(text, ["infosec", "security form", "vendor", "enterprise", "hiring"]):
            return "enterprise_sales"
        if _contains_any(text, ["certificate", "name on cert", "credential"]):
            return "certification"
        return "general_support"

    if company_name == "claude":
        if _contains_any(text, ["privacy", "data", "delete conversation", "personal info", "crawl", "training", "opt out", "gdpr"]):
            return "privacy"
        if _contains_any(text, ["security", "vulnerability", "bug bounty", "exploit"]):
            return "security"
        if _contains_any(text, ["workspace", "team", "seat", "admin", "access", "permission", "lti", "sso", "students", "education"]):
            return "account_management"
        if _contains_any(text, ["api", "bedrock", "vertex", "azure", "integration", "failing requests", "all requests"]):
            return "api_integration"
        if _contains_any(text, ["conversation", "chat", "message", "history"]):
            return "conversation_management"
        if _contains_any(text, ["not working", "stopped", "down", "failing", "broken"]):
            return "platform_reliability"
        return "general_support"

    return "general_support"
