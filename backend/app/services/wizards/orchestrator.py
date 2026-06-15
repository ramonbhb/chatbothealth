import json

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models import CatalogTable, Dataset, WizardSession, WizardType
from app.services.llm.gateway import llm_gateway
from app.services.llm.prompts import (
    CLEAN_SYSTEM_PROMPT,
    DOC_SYSTEM_PROMPT,
    PROJECT_DOC_SECTIONS,
    QUALITY_CHECKLIST_ITEMS,
    SCRIPT_TEMPLATE_HEADER,
)
from app.services.scriptgen.validator import validate_script


async def get_schema_context(db: AsyncSession, dataset_id: int) -> str:
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
        lines.append("")
    return "\n".join(lines)


async def run_doc_intake(
    db: AsyncSession,
    session: WizardSession,
    user_message: str,
) -> str:
    section_data = json.loads(session.section_data or "{}")
    current_section = section_data.get("_current_section", PROJECT_DOC_SECTIONS[0])

    messages = [
        {"role": "system", "content": DOC_SYSTEM_PROMPT},
        {
            "role": "system",
            "content": (
                f"Current section: {current_section}. "
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
    messages = [
        {"role": "system", "content": DOC_SYSTEM_PROMPT},
        {
            "role": "system",
            "content": (
                f"Extract and summarize content for section '{section_key}' from the conversation. "
                "Return JSON: {\"content\": \"...\", \"complete\": true/false, \"missing\": [\"...\"]}"
            ),
        },
    ]
    for msg in session.messages:
        messages.append({"role": msg.role, "content": msg.content})

    result, _, _ = await llm_gateway.complete_json(messages)
    return result


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
    result, _, _ = await llm_gateway.complete_json(messages)
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
        schema_context = await get_schema_context(db, session.dataset_id)

    messages = [
        {"role": "system", "content": CLEAN_SYSTEM_PROMPT},
        {"role": "system", "content": f"Schema context:\n{schema_context}"},
    ]
    for msg in session.messages[-20:]:
        messages.append({"role": msg.role, "content": msg.content})
    messages.append({"role": "user", "content": user_message})

    reply, _, _ = await llm_gateway.complete(messages)
    session.llm_model_used = llm_gateway.model
    return reply


async def generate_clean_script(
    db: AsyncSession,
    session: WizardSession,
) -> str:
    schema_context = ""
    if session.dataset_id:
        schema_context = await get_schema_context(db, session.dataset_id)

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
