import json

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models import CatalogTable, Dataset, WizardSession, WizardType
from app.services.llm.gateway import llm_gateway
from app.services.llm.prompts import (
    CLEAN_KICKOFF_PROMPT,
    CLEAN_SYSTEM_PROMPT,
    DOC_SYSTEM_PROMPT,
    PROJECT_DOC_SECTIONS,
    QUALITY_CHECKLIST_ITEMS,
    SCRIPT_TEMPLATE_HEADER,
    SECTION_GUIDANCE,
    SECTION_LABELS,
)
from app.services.llm.json_utils import coerce_section_value, parse_json_object
from app.services.scriptgen.validator import validate_script

MAX_SAMPLE_ROWS = 10


def parse_sample_rows(raw: str) -> list[dict]:
    try:
        rows = json.loads(raw or "[]")
        if isinstance(rows, list):
            return [r for r in rows if isinstance(r, dict)][:MAX_SAMPLE_ROWS]
    except json.JSONDecodeError:
        pass
    return []


async def get_schema_context(db: AsyncSession, dataset_id: int, *, include_samples: bool = True) -> str:
    result = await db.execute(
        select(Dataset)
        .where(Dataset.id == dataset_id)
        .options(
            selectinload(Dataset.tables).selectinload(CatalogTable.columns),
            selectinload(Dataset.tables).selectinload(CatalogTable.relationships_from),
        )
    )
    dataset = result.scalar_one_or_none()
    if not dataset:
        return "No dataset found."

    lines = [f"Dataset: {dataset.name}", f"Description: {dataset.description}", ""]
    for table in dataset.tables:
        lines.append(f"Table: {table.name} — {table.description}")
        for col in table.columns:
            phi = " [PHI]" if col.is_phi else ""
            lines.append(
                f"  - {col.name} ({col.data_type}, nullable={col.nullable}){phi}: {col.description}"
            )
            if col.valid_values:
                lines.append(f"    Valid values: {col.valid_values}")
        for rel in table.relationships_from:
            lines.append(
                f"  -> Join {rel.from_column} to {rel.to_table_id}.{rel.to_column} ({rel.relationship_type})"
            )
        if include_samples:
            samples = parse_sample_rows(table.sample_rows)
            if samples:
                lines.append(f"  Sample rows (up to {MAX_SAMPLE_ROWS}, de-identified examples):")
                for i, row in enumerate(samples, 1):
                    lines.append(f"    {i}. {json.dumps(row)}")
            else:
                lines.append("  Sample rows: (none provided)")
        lines.append("")
    return "\n".join(lines)


async def run_doc_intake(
    db: AsyncSession,
    session: WizardSession,
    user_message: str,
) -> str:
    section_data = json.loads(session.section_data or "{}")
    current_section = section_data.get("_current_section", PROJECT_DOC_SECTIONS[0])
    guidance = SECTION_GUIDANCE.get(current_section, "")

    messages = [
        {"role": "system", "content": DOC_SYSTEM_PROMPT},
        {
            "role": "system",
            "content": (
                f"Current section: {current_section} ({SECTION_LABELS.get(current_section, current_section)}). "
                f"Section goal: {guidance} "
                f"Existing sections so far: {json.dumps({k: v for k, v in section_data.items() if not k.startswith('_')})}"
            ),
        },
    ]
    for msg in session.messages[-20:]:
        messages.append({"role": msg.role, "content": msg.content})
    messages.append({"role": "user", "content": user_message})

    reply, _, _ = await llm_gateway.complete(messages)
    session.llm_model_used = llm_gateway.model
    return reply


async def extract_section_content(
    db: AsyncSession,
    session: WizardSession,
    section_key: str,
) -> dict:
    label = SECTION_LABELS.get(section_key, section_key)
    messages = [
        {"role": "system", "content": DOC_SYSTEM_PROMPT},
        {
            "role": "system",
            "content": (
                f"Extract and summarize content for the section '{section_key}' ({label}) from the conversation. "
                "Use only information discussed — do not invent content. "
                "Return JSON: {\"content\": \"...\", \"complete\": true/false, \"missing\": [\"...\"]}"
            ),
        },
    ]
    for msg in session.messages:
        messages.append({"role": msg.role, "content": msg.content})

    result, _, _, _ = await llm_gateway.complete_json(messages)
    if "content" not in result and "raw" in result:
        result["content"] = str(result.get("raw", ""))
    return result


async def split_full_text_into_sections(full_text: str) -> tuple[dict[str, str], str, dict]:
    section_spec = {
        key: SECTION_LABELS.get(key, key.replace("_", " ").title())
        for key in PROJECT_DOC_SECTIONS
    }
    keys_list = ", ".join(PROJECT_DOC_SECTIONS)
    system_content = (
        f"{DOC_SYSTEM_PROMPT}\n\n"
        "Split the user's full project document text into predefined sections. "
        "Use ONLY the provided text — do not invent content. "
        f"Section labels: {json.dumps(section_spec, indent=2)}. "
        f"You MUST return a single JSON object using EXACTLY these snake_case keys: {keys_list}. "
        "Each value must be a string with the extracted text for that section. "
        "Use an empty string if the section is not present in the source text."
    )
    messages = [
        {"role": "system", "content": system_content},
        {"role": "user", "content": full_text},
    ]
    result, raw_content, _, _ = await llm_gateway.complete_json(messages, max_tokens=8192)

    if "raw" in result and len(result) == 1:
        result = parse_json_object(str(result["raw"]))

    if "sections" in result and isinstance(result["sections"], dict):
        result = {**result, **result["sections"]}

    label_to_key = {
        key.lower(): key for key in PROJECT_DOC_SECTIONS
    }
    for key, label in SECTION_LABELS.items():
        label_to_key[label.lower()] = key
        label_to_key[label.lower().replace(" / ", "_").replace(" ", "_")] = key

    sections: dict[str, str] = {}
    for key in PROJECT_DOC_SECTIONS:
        value = result.get(key, "")
        if not value:
            for result_key, result_value in result.items():
                if str(result_key).startswith("_"):
                    continue
                normalized = str(result_key).lower().replace(" ", "_").replace("/", "_")
                if normalized == key or label_to_key.get(str(result_key).lower()) == key:
                    value = result_value
                    break
        sections[key] = coerce_section_value(value)

    debug = {
        "model": llm_gateway.model,
        "raw_length": len(raw_content),
        "raw_preview": raw_content[:800],
        "parsed_keys": [k for k in result.keys() if not str(k).startswith("_")],
        "filled_sections": sum(1 for v in sections.values() if v.strip()),
        "input_length": len(full_text),
    }
    return sections, llm_gateway.model, debug


async def run_quality_check(session: WizardSession) -> dict:
    section_data = json.loads(session.section_data or "{}")
    messages = [
        {"role": "system", "content": DOC_SYSTEM_PROMPT},
        {
            "role": "system",
            "content": (
                "Evaluate the project document sections against this checklist. "
                f"Checklist: {QUALITY_CHECKLIST_ITEMS}. "
                "Return JSON: {\"items\": [{\"item\": \"...\", \"passed\": bool, \"note\": \"...\"}]}"
            ),
        },
        {"role": "user", "content": json.dumps(section_data)},
    ]
    result, _, _, _ = await llm_gateway.complete_json(messages)
    if "items" not in result:
        result = {
            "items": [
                {
                    "item": item,
                    "passed": bool(section_data),
                    "note": "Automated fallback check",
                }
                for item in QUALITY_CHECKLIST_ITEMS
            ]
        }
    return result


async def run_clean_discussion(
    db: AsyncSession,
    session: WizardSession,
    user_message: str,
) -> str:
    schema_context = ""
    if session.dataset_id:
        schema_context = await get_schema_context(db, session.dataset_id, include_samples=True)

    messages = [
        {"role": "system", "content": CLEAN_SYSTEM_PROMPT},
        {"role": "system", "content": f"Dataset structure and samples:\n{schema_context}"},
    ]
    for msg in session.messages[-20:]:
        messages.append({"role": msg.role, "content": msg.content})
    messages.append({"role": "user", "content": user_message})

    reply, _, _ = await llm_gateway.complete(messages)
    session.llm_model_used = llm_gateway.model
    return reply


async def run_clean_kickoff(db: AsyncSession, session: WizardSession) -> str:
    if not session.dataset_id:
        return "Please select a dataset first to explore structure and samples."

    schema_context = await get_schema_context(db, session.dataset_id, include_samples=True)
    messages = [
        {"role": "system", "content": CLEAN_SYSTEM_PROMPT},
        {"role": "system", "content": CLEAN_KICKOFF_PROMPT},
        {"role": "system", "content": f"Dataset structure and samples:\n{schema_context}"},
        {"role": "user", "content": "Please open our cleaning and modeling planning session."},
    ]
    reply, _, _ = await llm_gateway.complete(messages)
    session.llm_model_used = llm_gateway.model
    return reply


async def generate_clean_script(
    db: AsyncSession,
    session: WizardSession,
) -> str:
    schema_context = ""
    if session.dataset_id:
        schema_context = await get_schema_context(db, session.dataset_id, include_samples=True)

    messages = [
        {"role": "system", "content": CLEAN_SYSTEM_PROMPT},
        {"role": "system", "content": f"Schema context:\n{schema_context}"},
        {
            "role": "system",
            "content": (
                "Generate a complete data_clean.py script based on the conversation. "
                "Use pandas and SQLAlchemy. Include a main() function. "
                "Return ONLY Python code, no markdown fences."
            ),
        },
    ]
    for msg in session.messages:
        messages.append({"role": msg.role, "content": msg.content})

    script, _, _ = await llm_gateway.complete(messages, temperature=0.1)
    script = script.strip()
    if script.startswith("```"):
        lines = script.split("\n")
        script = "\n".join(lines[1:])
        if script.endswith("```"):
            script = script[:-3]

    if SCRIPT_TEMPLATE_HEADER.strip() not in script:
        script = SCRIPT_TEMPLATE_HEADER + script

    session.script_content = script
    session.llm_model_used = llm_gateway.model
    validation = validate_script(script)
    session.validation_result = json.dumps(validation)
    return script
