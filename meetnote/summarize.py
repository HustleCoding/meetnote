"""Local summarization of transcripts using Ollama.

Talks to a locally running Ollama daemon over HTTP. Produces a markdown summary
with an overview, key points, decisions and action items.
"""

from __future__ import annotations

from .config import Config

SUMMARY_SYSTEM_PROMPT = (
    "You are a meeting assistant. You are given a raw transcript of a meeting. "
    "Write a concise, well-structured summary in Markdown. Be faithful to the "
    "transcript and do not invent details."
)

SUMMARY_INSTRUCTIONS = """\
Summarize the meeting transcript below. Use exactly these Markdown sections:

## Overview
A 2-3 sentence high-level summary.

## Key Points
Bulleted list of the most important points discussed.

## Decisions
Bulleted list of decisions made (or "None recorded.").

## Action Items
Bulleted list of action items. Format each as "- [ ] <owner if known>: <task>".

Transcript:
---
{transcript}
---
"""


def build_summary_prompt(transcript_text: str) -> str:
    return SUMMARY_INSTRUCTIONS.format(transcript=transcript_text.strip())


class SummarizeError(RuntimeError):
    pass


def summarize(transcript_text: str, config: Config, timeout: float = 600.0) -> str:
    """Summarize a transcript via the local Ollama API and return Markdown text."""
    import requests  # lazy import keeps the dependency optional for tests

    url = f"{config.ollama_host.rstrip('/')}/api/chat"
    payload = {
        "model": config.ollama_model,
        "stream": False,
        "messages": [
            {"role": "system", "content": SUMMARY_SYSTEM_PROMPT},
            {"role": "user", "content": build_summary_prompt(transcript_text)},
        ],
    }
    try:
        resp = requests.post(url, json=payload, timeout=timeout)
        resp.raise_for_status()
    except requests.RequestException as exc:  # pragma: no cover - network error path
        raise SummarizeError(
            f"Could not reach Ollama at {config.ollama_host}. Is it running "
            f"('ollama serve') and is the model '{config.ollama_model}' pulled? ({exc})"
        ) from exc

    data = resp.json()
    message = data.get("message") or {}
    content = message.get("content", "").strip()
    if not content:
        raise SummarizeError("Ollama returned an empty summary.")
    return content
