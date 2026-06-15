import json
from datetime import datetime, timezone

from docx import Document
from docx.shared import Pt

from app.core.config import get_settings
from app.services.llm.prompts import PROJECT_DOC_SECTIONS, SECTION_LABELS


def build_project_doc(
    *,
    title: str,
    section_data: dict,
    user_email: str,
    session_id: int,
    model_used: str,
) -> Document:
    settings = get_settings()
    doc = Document()

    doc.add_heading(title or "Health Data Science Project", level=0)
    doc.add_paragraph(f"Institution: {settings.institution_name}")
    doc.add_paragraph(f"Generated: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}")
    doc.add_paragraph(f"Author: {user_email}")
    doc.add_paragraph(f"Session ID: {session_id}")
    doc.add_paragraph("")
    doc.add_paragraph(
        "Purpose: Document the study's data, methods, expected artifacts, and analysis workflow."
    )
    doc.add_paragraph("")

    for section_key in PROJECT_DOC_SECTIONS:
        label = SECTION_LABELS.get(section_key, section_key.replace("_", " ").title())
        doc.add_heading(label, level=1)
        content = section_data.get(section_key, "")
        if isinstance(content, dict):
            content = content.get("content", json.dumps(content, indent=2))
        doc.add_paragraph(str(content) if content else "[Not provided]")

    footer = doc.sections[0].footer
    footer_para = footer.paragraphs[0] if footer.paragraphs else footer.add_paragraph()
    footer_para.text = (
        f"HRA Export | {user_email} | Session {session_id} | Model: {model_used} | "
        f"{datetime.now(timezone.utc).isoformat()}"
    )
    for run in footer_para.runs:
        run.font.size = Pt(8)

    return doc
