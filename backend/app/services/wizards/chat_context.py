"""Keep conversational LLM prompts small for faster responses."""

from __future__ import annotations

from app.models import ChatMessage
from app.services.llm.prompts import PROJECT_DOC_SECTIONS, SECTION_LABELS

CHAT_MAX_HISTORY = 12
CHAT_MAX_MESSAGE_CHARS = 2_000
CHAT_MAX_OUTPUT_TOKENS = 1_024
SECTION_PREVIEW_CHARS = 500


def truncate_text(text: str, limit: int) -> str:
    cleaned = text.strip()
    if len(cleaned) <= limit:
        return cleaned
    return cleaned[: limit - 1].rstrip() + "…"


def section_context_summary(section_data: dict[str, str]) -> str:
    lines: list[str] = []
    for key in PROJECT_DOC_SECTIONS:
        raw = str(section_data.get(key, "") or "").strip()
        if not raw:
            continue
        label = SECTION_LABELS.get(key, key)
        preview = truncate_text(raw, SECTION_PREVIEW_CHARS)
        lines.append(f"- {key} ({label}): {preview}")
    return "\n".join(lines) if lines else "(nenhuma seção preenchida ainda)"


def trim_chat_history(
    messages: list[ChatMessage],
    *,
    max_messages: int = CHAT_MAX_HISTORY,
    max_chars: int = CHAT_MAX_MESSAGE_CHARS,
) -> list[dict[str, str]]:
    recent = messages[-max_messages:]
    return [
        {"role": msg.role, "content": truncate_text(msg.content, max_chars)}
        for msg in recent
    ]
