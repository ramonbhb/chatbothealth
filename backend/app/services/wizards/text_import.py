"""Split long project documents into wizard sections without echoing the full text in one LLM response."""

from __future__ import annotations

import json
import re
from typing import TYPE_CHECKING

from app.services.llm.json_utils import coerce_section_value
from app.services.llm.prompts import PROJECT_DOC_SECTIONS, SECTION_LABELS

if TYPE_CHECKING:
    from app.services.llm.gateway import LLMGateway

# Above this size, a single JSON response cannot reliably hold all section text.
LONG_TEXT_CHAR_THRESHOLD = 6_000
CHUNK_TARGET_CHARS = 3_500
CHUNK_BATCH_SIZE = 10

_HEADING_ALIASES: dict[str, list[str]] = {
    "background": ["contexto", "background", "introdução", "introducao", "antecedentes", "visão geral"],
    "research_questions": [
        "perguntas de pesquisa",
        "perguntas de pesquisa / hipóteses",
        "hipóteses",
        "hipoteses",
        "research questions",
        "questões de pesquisa",
    ],
    "objectives": ["objetivos", "objectives", "objetivo"],
    "data_sources": ["fontes de dados", "data sources", "dados", "data"],
    "study_population": ["população do estudo", "populacao do estudo", "study population", "coorte", "população"],
    "variables_endpoints": [
        "variáveis e desfechos",
        "variaveis e desfechos",
        "variables",
        "endpoints",
        "desfechos",
    ],
    "methods_analysis": [
        "métodos / plano de análise",
        "metodos / plano de analise",
        "métodos",
        "metodos",
        "methods",
        "plano de análise",
        "plano de analise",
    ],
    "expected_artifacts": [
        "artefatos e entregáveis esperados",
        "artefatos",
        "entregáveis",
        "entregaveis",
        "expected artifacts",
        "deliverables",
    ],
    "analysis_application": ["fluxo de análise", "fluxo de analise", "analysis flow", "aplicação", "aplicacao"],
    "data_governance_ethics": [
        "governança de dados e ética",
        "governanca de dados e etica",
        "ética",
        "etica",
        "ethics",
        "governança",
    ],
    "timeline": ["cronograma", "timeline", "prazos"],
    "risks_limitations": ["riscos e limitações", "riscos e limitacoes", "risks", "limitações", "limitacoes"],
    "references": ["referências", "referencias", "references", "bibliografia"],
}


def _normalize_heading(line: str) -> str:
    text = line.strip()
    text = re.sub(r"^#+\s*", "", text)
    text = re.sub(r"^\d+[\.)]\s*", "", text)
    text = re.sub(r"^[-*]\s+", "", text)
    return re.sub(r"\s+", " ", text).strip().lower()


def match_section_heading(line: str) -> str | None:
    normalized = _normalize_heading(line)
    if not normalized or len(normalized) > 120:
        return None

    for key, label in SECTION_LABELS.items():
        label_norm = label.lower()
        if normalized == label_norm or normalized == key.replace("_", " "):
            return key

    for key, aliases in _HEADING_ALIASES.items():
        for alias in aliases:
            if normalized == alias or normalized.startswith(f"{alias}:"):
                return key
    return None


def split_by_headings(full_text: str) -> dict[str, str]:
    sections: dict[str, list[str]] = {key: [] for key in PROJECT_DOC_SECTIONS}
    current_key: str | None = None
    preamble: list[str] = []

    for line in full_text.splitlines():
        heading_key = match_section_heading(line)
        if heading_key:
            current_key = heading_key
            continue
        if current_key:
            sections[current_key].append(line)
        else:
            preamble.append(line)

    if preamble and not any(sections.values()):
        sections["background"] = preamble

    return {key: "\n".join(lines).strip() for key, lines in sections.items()}


def paragraph_chunks(full_text: str, *, max_chars: int = CHUNK_TARGET_CHARS) -> list[str]:
    paragraphs = [p.strip() for p in re.split(r"\n\s*\n", full_text.strip()) if p.strip()]
    if not paragraphs:
        return [full_text.strip()] if full_text.strip() else []

    chunks: list[str] = []
    current: list[str] = []
    current_len = 0

    for paragraph in paragraphs:
        extra = len(paragraph) + (2 if current else 0)
        if current and current_len + extra > max_chars:
            chunks.append("\n\n".join(current))
            current = [paragraph]
            current_len = len(paragraph)
        else:
            current.append(paragraph)
            current_len += extra

    if current:
        chunks.append("\n\n".join(current))
    return chunks


def assemble_sections_from_assignments(
    chunks: list[str],
    assignments: dict[int, str],
) -> dict[str, str]:
    grouped: dict[str, list[str]] = {key: [] for key in PROJECT_DOC_SECTIONS}
    for index, chunk in enumerate(chunks):
        section_key = assignments.get(index)
        if section_key in grouped:
            grouped[section_key].append(chunk)
    return {key: "\n\n".join(parts).strip() for key, parts in grouped.items()}


def count_filled_sections(sections: dict[str, str]) -> int:
    return sum(1 for value in sections.values() if value.strip())


def should_use_chunked_import(full_text: str) -> bool:
    return len(full_text) >= LONG_TEXT_CHAR_THRESHOLD


async def assign_chunks_via_llm(
    gateway: LLMGateway,
    chunks: list[str],
) -> dict[int, str]:
    section_desc = json.dumps(
        {key: SECTION_LABELS[key] for key in PROJECT_DOC_SECTIONS},
        ensure_ascii=False,
    )
    assignments: dict[int, str] = {}

    for batch_start in range(0, len(chunks), CHUNK_BATCH_SIZE):
        batch = chunks[batch_start : batch_start + CHUNK_BATCH_SIZE]
        numbered_parts = []
        for offset, chunk in enumerate(batch):
            index = batch_start + offset
            preview = chunk if len(chunk) <= 4000 else chunk[:4000] + "\n[...]"
            numbered_parts.append(f"--- FRAGMENTO {index} ---\n{preview}")

        messages = [
            {
                "role": "system",
                "content": (
                    "Você classifica fragmentos de um documento de projeto de pesquisa em saúde.\n"
                    f"Chaves válidas: {', '.join(PROJECT_DOC_SECTIONS)}\n"
                    f"Rótulos: {section_desc}\n"
                    "Atribua cada fragmento a exatamente uma chave. "
                    "Use string vazia \"\" apenas se o fragmento for claramente irrelevante.\n"
                    'Retorne JSON: {"assignments": {"0": "background", "1": "methods_analysis"}}'
                ),
            },
            {"role": "user", "content": "\n\n".join(numbered_parts)},
        ]
        result, _, _, _ = await gateway.complete_json(messages, max_tokens=2048)
        batch_assignments = result.get("assignments", {})
        if not isinstance(batch_assignments, dict):
            continue

        for index_str, section_key in batch_assignments.items():
            try:
                index = int(index_str)
            except (TypeError, ValueError):
                continue
            if section_key in PROJECT_DOC_SECTIONS:
                assignments[index] = section_key

    return assignments


async def split_long_text_into_sections(
    gateway: LLMGateway,
    full_text: str,
) -> tuple[dict[str, str], dict]:
    heuristic_sections = split_by_headings(full_text)
    heuristic_filled = count_filled_sections(heuristic_sections)
    if heuristic_filled >= 3:
        sections = {
            key: coerce_section_value(heuristic_sections.get(key, ""))
            for key in PROJECT_DOC_SECTIONS
        }
        debug = {
            "strategy": "headings",
            "filled_sections": count_filled_sections(sections),
            "input_length": len(full_text),
        }
        return sections, debug

    chunks = paragraph_chunks(full_text)
    assignments = await assign_chunks_via_llm(gateway, chunks)
    sections = assemble_sections_from_assignments(chunks, assignments)
    sections = {key: coerce_section_value(sections.get(key, "")) for key in PROJECT_DOC_SECTIONS}
    debug = {
        "strategy": "chunk_assignment",
        "chunk_count": len(chunks),
        "assigned_chunks": len(assignments),
        "filled_sections": count_filled_sections(sections),
        "input_length": len(full_text),
    }
    return sections, debug
