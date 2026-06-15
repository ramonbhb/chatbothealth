import json
import os
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import FileResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.audit.service import log_audit
from app.core.config import get_settings
from app.core.database import get_db
from app.core.deps import get_current_user
from app.models import ChatMessage, ExportArtifact, User, WizardSession, WizardType
from app.schemas import (
    ChatMessageCreate,
    ChatMessageOut,
    ImportTextRequest,
    WizardSessionCreate,
    WizardSessionOut,
    WizardSessionUpdate,
)
from app.services.docgen.builder import build_project_doc
from app.services.llm.json_utils import coerce_section_value
from app.services.llm.prompts import PROJECT_DOC_SECTIONS
from app.services.wizards.orchestrator import (
    extract_section_content,
    run_doc_intake,
    run_quality_check,
    split_full_text_into_sections,
)

router = APIRouter(prefix="/projects", tags=["projects"])


def _session_out(session: WizardSession) -> WizardSessionOut:
    return WizardSessionOut(
        id=session.id,
        wizard_type=session.wizard_type.value,
        current_step=session.current_step,
        title=session.title,
        dataset_id=session.dataset_id,
        linked_project_id=session.linked_project_id,
        section_data=json.loads(session.section_data or "{}"),
        script_content=session.script_content,
        validation_result=json.loads(session.validation_result or "{}"),
        quality_checklist=json.loads(session.quality_checklist or "{}"),
        llm_model_used=session.llm_model_used,
        created_at=session.created_at.isoformat(),
        updated_at=session.updated_at.isoformat(),
        messages=[
            ChatMessageOut(
                id=m.id,
                role=m.role,
                content=m.content,
                created_at=m.created_at.isoformat(),
            )
            for m in session.messages
        ],
    )


@router.get("", response_model=list[WizardSessionOut])
async def list_projects(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(WizardSession)
        .where(
            WizardSession.user_id == current_user.id,
            WizardSession.wizard_type == WizardType.project_doc,
        )
        .options(selectinload(WizardSession.messages))
        .order_by(WizardSession.updated_at.desc())
    )
    return [_session_out(s) for s in result.scalars().all()]


@router.post("", response_model=WizardSessionOut, status_code=201)
async def create_project(
    body: WizardSessionCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    section_data = {"_current_section": PROJECT_DOC_SECTIONS[0]}
    session = WizardSession(
        user_id=current_user.id,
        wizard_type=WizardType.project_doc,
        current_step="basics",
        title=body.title,
        section_data=json.dumps(section_data),
    )
    db.add(session)
    await db.commit()
    result = await db.execute(
        select(WizardSession)
        .where(WizardSession.id == session.id)
        .options(selectinload(WizardSession.messages))
    )
    return _session_out(result.scalar_one())


@router.get("/{session_id}", response_model=WizardSessionOut)
async def get_project(
    session_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(WizardSession)
        .where(WizardSession.id == session_id, WizardSession.user_id == current_user.id)
        .options(selectinload(WizardSession.messages))
    )
    session = result.scalar_one_or_none()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return _session_out(session)


@router.patch("/{session_id}", response_model=WizardSessionOut)
async def update_project(
    session_id: int,
    body: WizardSessionUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(WizardSession)
        .where(WizardSession.id == session_id, WizardSession.user_id == current_user.id)
        .options(selectinload(WizardSession.messages))
    )
    session = result.scalar_one_or_none()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    if body.title is not None:
        session.title = body.title
    if body.current_step is not None:
        session.current_step = body.current_step
    if body.section_data is not None:
        session.section_data = json.dumps(body.section_data)
    session.updated_at = datetime.now(timezone.utc)
    await db.commit()
    result = await db.execute(
        select(WizardSession)
        .where(WizardSession.id == session_id)
        .options(selectinload(WizardSession.messages))
    )
    return _session_out(result.scalar_one())


@router.post("/{session_id}/save-draft", response_model=WizardSessionOut)
async def save_draft(
    session_id: int,
    body: WizardSessionUpdate,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(WizardSession)
        .where(WizardSession.id == session_id, WizardSession.user_id == current_user.id)
        .options(selectinload(WizardSession.messages))
    )
    session = result.scalar_one_or_none()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    if body.title is not None:
        session.title = body.title
    if body.current_step is not None:
        session.current_step = body.current_step
    if body.section_data is not None:
        session.section_data = json.dumps(body.section_data)
    session.updated_at = datetime.now(timezone.utc)
    await log_audit(
        db,
        user_id=current_user.id,
        action="save_project_draft",
        resource_type="wizard_session",
        resource_id=str(session.id),
        ip_address=request.client.host if request.client else "",
    )
    await db.commit()
    result = await db.execute(
        select(WizardSession)
        .where(WizardSession.id == session_id)
        .options(selectinload(WizardSession.messages))
    )
    return _session_out(result.scalar_one())


@router.post("/{session_id}/import-text", response_model=WizardSessionOut)
async def import_full_text(
    session_id: int,
    body: ImportTextRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(WizardSession)
        .where(WizardSession.id == session_id, WizardSession.user_id == current_user.id)
        .options(selectinload(WizardSession.messages))
    )
    session = result.scalar_one_or_none()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    try:
        sections, model, debug = await split_full_text_into_sections(body.full_text)
    except RuntimeError as exc:
        raise HTTPException(
            status_code=502,
            detail={"message": str(exc), "debug": {"stage": "llm_call", "hint": "Run backend/scripts/debug_import.py or GET /api/llm/status"}},
        ) from exc

    filled = sum(1 for v in sections.values() if v.strip())
    if filled == 0:
        raise HTTPException(
            status_code=502,
            detail={
                "message": "Could not extract sections from the text. The AI response was empty or invalid.",
                "debug": debug,
            },
        )

    section_data = json.loads(session.section_data or "{}")
    section_data.update(sections)
    section_data["_current_section"] = PROJECT_DOC_SECTIONS[0]
    section_data["_imported"] = True
    session.section_data = json.dumps(section_data)
    session.current_step = "review"
    session.llm_model_used = model
    session.updated_at = datetime.now(timezone.utc)

    note = ChatMessage(
        session_id=session.id,
        role="assistant",
        content="Imported full project text and split it into predefined sections. Review and edit each section below.",
    )
    db.add(note)
    await db.commit()
    result = await db.execute(
        select(WizardSession)
        .where(WizardSession.id == session_id)
        .options(selectinload(WizardSession.messages))
    )
    return _session_out(result.scalar_one())


@router.post("/{session_id}/chat", response_model=ChatMessageOut)
async def project_chat(
    session_id: int,
    body: ChatMessageCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(WizardSession)
        .where(WizardSession.id == session_id, WizardSession.user_id == current_user.id)
        .options(selectinload(WizardSession.messages))
    )
    session = result.scalar_one_or_none()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    user_msg = ChatMessage(session_id=session.id, role="user", content=body.content)
    db.add(user_msg)
    await db.flush()

    reply = await run_doc_intake(db, session, body.content)
    assistant_msg = ChatMessage(session_id=session.id, role="assistant", content=reply)
    db.add(assistant_msg)
    session.updated_at = datetime.now(timezone.utc)
    await db.commit()
    await db.refresh(assistant_msg)
    return ChatMessageOut(
        id=assistant_msg.id,
        role=assistant_msg.role,
        content=assistant_msg.content,
        created_at=assistant_msg.created_at.isoformat(),
    )


@router.post("/{session_id}/extract/{section_key}")
async def extract_section(
    session_id: int,
    section_key: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(WizardSession)
        .where(WizardSession.id == session_id, WizardSession.user_id == current_user.id)
        .options(selectinload(WizardSession.messages))
    )
    session = result.scalar_one_or_none()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    extracted = await extract_section_content(db, session, section_key)
    section_data = json.loads(session.section_data or "{}")
    section_data[section_key] = coerce_section_value(extracted.get("content", extracted))
    section_data["_current_section"] = section_key
    session.section_data = json.dumps(section_data)
    await db.commit()
    return extracted


@router.post("/{session_id}/quality-check")
async def quality_check(
    session_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(WizardSession)
        .where(WizardSession.id == session_id, WizardSession.user_id == current_user.id)
        .options(selectinload(WizardSession.messages))
    )
    session = result.scalar_one_or_none()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    checklist = await run_quality_check(session)
    session.quality_checklist = json.dumps(checklist)
    session.current_step = "quality"
    await db.commit()
    return checklist


@router.post("/{session_id}/export")
async def export_project(
    session_id: int,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    settings = get_settings()
    os.makedirs(settings.exports_dir, exist_ok=True)

    result = await db.execute(
        select(WizardSession)
        .where(WizardSession.id == session_id, WizardSession.user_id == current_user.id)
    )
    session = result.scalar_one_or_none()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    section_data = json.loads(session.section_data or "{}")
    doc = build_project_doc(
        title=session.title,
        section_data=section_data,
        user_email=current_user.email,
        session_id=session.id,
        model_used=session.llm_model_used or settings.llm_model,
    )
    filename = f"project_{session.id}.docx"
    filepath = os.path.join(settings.exports_dir, filename)
    doc.save(filepath)

    artifact = ExportArtifact(
        session_id=session.id,
        filename=filename,
        file_path=filepath,
        artifact_type="project_docx",
    )
    db.add(artifact)
    session.current_step = "export"
    await log_audit(
        db,
        user_id=current_user.id,
        action="export_project_doc",
        resource_type="wizard_session",
        resource_id=str(session.id),
        ip_address=request.client.host if request.client else "",
    )
    await db.commit()
    return FileResponse(
        filepath,
        filename="project.docx",
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    )
