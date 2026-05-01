from __future__ import annotations

import os
from functools import lru_cache

from openai import OpenAI


MODEL_NAME = os.getenv("OPENROUTER_MODEL", "meta-llama/llama-3-8b-instruct")


@lru_cache(maxsize=1)
def _client() -> OpenAI | None:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        return None

    return OpenAI(api_key=api_key, base_url="https://openrouter.ai/api/v1")


def build_prompt(company: str, issue: str, context: str) -> list[dict[str, str]]:
    system_message = (
        "You are a cybersecurity-aware support agent. "
        "Use only the supplied context. Do not hallucinate policies, links, or steps. "
        "If the context is insufficient, say so clearly and recommend contacting support. "
        "Keep the answer concise, factual, and actionable."
    )
    user_message = f"""Company: {company}

USER ISSUE:
{issue}

SUPPORT CONTEXT:
{context}

Write a concise grounded response."""

    return [
        {"role": "system", "content": system_message},
        {"role": "user", "content": user_message},
    ]


def generate_response(issue: str, retrieved_docs: list[str], company: str) -> str:
    """Generate a grounded support response using only retrieved context."""
    if not retrieved_docs:
        return (
            f"Thank you for contacting {company} support. "
            "We could not find specific documentation for this issue. "
            "Please contact our support team directly for personalised assistance."
        )

    client = _client()
    if client is None:
        return "Based on our documentation: " + retrieved_docs[0][:400]

    context = "\n\n---\n\n".join(retrieved_docs)
    messages = build_prompt(company, issue, context)

    try:
        response = client.chat.completions.create(
            model=MODEL_NAME,
            messages=messages,
            temperature=0.1,
            max_tokens=220,
        )
        return response.choices[0].message.content.strip()
    except Exception:
        return "Based on our documentation: " + retrieved_docs[0][:400]
