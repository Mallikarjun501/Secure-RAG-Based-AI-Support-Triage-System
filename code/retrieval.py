from __future__ import annotations

import re
from pathlib import Path


def load_documents(base_path: str | Path = "data") -> dict[str, list[str]]:
    """Load local markdown support content and bucket it by domain."""
    base_dir = Path(base_path)
    domain_docs = {"hackerrank": [], "claude": [], "visa": [], "all": []}

    for path in base_dir.rglob("*.md"):
        try:
            content = path.read_text(encoding="utf-8")
        except Exception:
            continue

        if len(content.split()) < 1:
            continue

        path_lower = path.relative_to(base_dir).as_posix().lower()
        if "hackerrank" in path_lower or "support.hackerrank" in path_lower:
            domain_docs["hackerrank"].append(content)
        elif "claude" in path_lower or "support.claude" in path_lower:
            domain_docs["claude"].append(content)
        elif "visa" in path_lower:
            domain_docs["visa"].append(content)
        else:
            domain_docs["all"].append(content)

    return domain_docs


def clean_text(text: str) -> str:
    text = re.sub(r"http\S+", "[URL]", text)
    text = re.sub(r"#", "", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def _company_key(company: str) -> str:
    company_name = str(company).strip().lower()
    aliases = {
        "hackerrank": "hackerrank",
        "hacker rank": "hackerrank",
        "claude": "claude",
        "visa": "visa",
    }
    return aliases.get(company_name, "")


def retrieve_docs(issue: str, domain_docs: dict[str, list[str]], company: str, top_k: int = 3) -> list[str]:
    """Retrieve company-scoped documents with a global fallback."""
    company_name = _company_key(company)

    if company_name and company_name in domain_docs and domain_docs[company_name]:
        pool = domain_docs[company_name]
    else:
        pool = domain_docs["all"]
        if not pool:
            pool = [doc for key, docs in domain_docs.items() if key != "all" for doc in docs]

    issue_words = set(re.findall(r"\b\w{4,}\b", issue.lower()))
    scored: list[tuple[int, str]] = []

    for doc in pool:
        doc_clean = clean_text(doc).lower()
        doc_words = set(re.findall(r"\b\w{4,}\b", doc_clean))
        score = len(issue_words & doc_words)
        if score >= 3:
            scored.append((score, doc_clean))

    scored.sort(reverse=True, key=lambda item: item[0])
    return [doc[:600] for _, doc in scored[:top_k]]
