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
from app.models import CatalogTable, ChatMessage, Dataset, ExportArtifact, User, WizardSession, WizardType
from app.schemas import ChatMessageCreate, ChatMessageOut, WizardSessionCreate, WizardSessionOut, WizardSessionUpdate
from app.services.scriptgen.validator import build_readme_snippet, validate_script
from app.services.wizards.orchestrator import (
    generate_clean_script,
    get_schema_context,
    parse_sample_rows,
    run_clean_discussion,
    run_clean_kickoff,
)

router = APIRouter(prefix="/cleaning", tags=["cleaning"])


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


@router.get("/datasets", response_model=list[dict])
async def list_enabled_datasets(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Dataset).where(Dataset.enabled.is_(True)).order_by(Dataset.name))
    datasets = result.scalars().all()
    return [{"id": d.id, "name": d.name, "description": d.description} for d in datasets]


@router.get("/datasets/{dataset_id}/schema")
async def get_dataset_schema(
    dataset_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Dataset)
        .where(Dataset.id == dataset_id, Dataset.enabled.is_(True))
        .options(
            selectinload(Dataset.tables).selectinload(CatalogTable.columns),
            selectinload(Dataset.tables).selectinload(CatalogTable.relationships_from),
        )
    )
    dataset = result.scalar_one_or_none()
    if not dataset:
        raise HTTPException(status_code=404, detail="Conjunto de dados não encontrado")
    return {
        "id": dataset.id,
        "name": dataset.name,
        "description": dataset.description,
        "schema_text": await get_schema_context(db, dataset_id),
        "tables": [
            {
                "id": t.id,
                "name": t.name,
                "description": t.description,
                "sample_rows": parse_sample_rows(t.sample_rows),
                "columns": [
                    {
                        "id": c.id,
                        "name": c.name,
                        "data_type": c.data_type,
                        "nullable": c.nullable,
                        "is_primary_key": c.is_primary_key,
                        "is_foreign_key": c.is_foreign_key,
                        "description": c.description,
                        "valid_values": c.valid_values,
                        "is_phi": c.is_phi,
                    }
                    for c in t.columns
                ],
            }
            for t in dataset.tables
        ],
    }


@router.get("", response_model=list[WizardSessionOut])
async def list_cleaning_sessions(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(WizardSession)
        .where(
            WizardSession.user_id == current_user.id,
            WizardSession.wizard_type == WizardType.data_clean,
        )
        .options(selectinload(WizardSession.messages))
        .order_by(WizardSession.updated_at.desc())
    )
    return [_session_out(s) for s in result.scalars().all()]


@router.post("", response_model=WizardSessionOut, status_code=201)
async def create_cleaning_session(
    body: WizardSessionCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    session = WizardSession(
        user_id=current_user.id,
        wizard_type=WizardType.data_clean,
        current_step="select_dataset",
        title=body.title,
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
async def get_cleaning_session(
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
        raise HTTPException(status_code=404, detail="Sessão não encontrada")
    return _session_out(session)


@router.patch("/{session_id}", response_model=WizardSessionOut)
async def update_cleaning_session(
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
        raise HTTPException(status_code=404, detail="Sessão não encontrada")
    if body.title is not None:
        session.title = body.title
    if body.current_step is not None:
        session.current_step = body.current_step
    if body.dataset_id is not None:
        session.dataset_id = body.dataset_id
    if body.linked_project_id is not None:
        session.linked_project_id = body.linked_project_id
    if body.script_content is not None:
        session.script_content = body.script_content
        validation = validate_script(body.script_content)
        session.validation_result = json.dumps(validation)
    session.updated_at = datetime.now(timezone.utc)
    await db.commit()
    await db.refresh(session)
    return _session_out(session)


@router.post("/{session_id}/chat", response_model=ChatMessageOut)
async def cleaning_chat(
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
        raise HTTPException(status_code=404, detail="Sessão não encontrada")

    user_msg = ChatMessage(session_id=session.id, role="user", content=body.content)
    db.add(user_msg)
    await db.flush()

    reply = await run_clean_discussion(db, session, body.content)
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


@router.post("/{session_id}/kickoff", response_model=ChatMessageOut)
async def cleaning_kickoff(
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
        raise HTTPException(status_code=404, detail="Sessão não encontrada")
    if session.messages:
        last = session.messages[-1]
        return ChatMessageOut(
            id=last.id,
            role=last.role,
            content=last.content,
            created_at=last.created_at.isoformat(),
        )

    reply = await run_clean_kickoff(db, session)
    assistant_msg = ChatMessage(session_id=session.id, role="assistant", content=reply)
    db.add(assistant_msg)
    session.current_step = "discussion"
    session.updated_at = datetime.now(timezone.utc)
    await db.commit()
    await db.refresh(assistant_msg)
    return ChatMessageOut(
        id=assistant_msg.id,
        role=assistant_msg.role,
        content=assistant_msg.content,
        created_at=assistant_msg.created_at.isoformat(),
    )


@router.post("/{session_id}/generate-script")
async def generate_script(
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
        raise HTTPException(status_code=404, detail="Sessão não encontrada")
    script = await generate_clean_script(db, session)
    session.current_step = "script_draft"
    await db.commit()
    return {
        "script_content": script,
        "validation_result": json.loads(session.validation_result or "{}"),
    }


@router.post("/{session_id}/validate")
async def validate_cleaning_script(
    session_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(WizardSession)
        .where(WizardSession.id == session_id, WizardSession.user_id == current_user.id)
    )
    session = result.scalar_one_or_none()
    if not session:
        raise HTTPException(status_code=404, detail="Sessão não encontrada")
    validation = validate_script(session.script_content)
    session.validation_result = json.dumps(validation)
    session.current_step = "validation"
    await db.commit()
    return validation


@router.post("/{session_id}/export")
async def export_cleaning(
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
        raise HTTPException(status_code=404, detail="Sessão não encontrada")

    script_path = os.path.join(settings.exports_dir, f"data_clean_{session.id}.py")
    readme_path = os.path.join(settings.exports_dir, f"data_clean_{session.id}_README.md")

    with open(script_path, "w") as f:
        f.write(session.script_content)

    readme = build_readme_snippet(
        session_id=session.id,
        user_email=current_user.email,
        model_used=session.llm_model_used or settings.llm_model,
    )
    with open(readme_path, "w") as f:
        f.write(readme)

    artifact = ExportArtifact(
        session_id=session.id,
        filename="data_clean.py",
        file_path=script_path,
        artifact_type="data_clean_py",
    )
    db.add(artifact)
    session.current_step = "export"
    await log_audit(
        db,
        user_id=current_user.id,
        action="export_data_clean",
        resource_type="wizard_session",
        resource_id=str(session.id),
        ip_address=request.client.host if request.client else "",
    )
    await db.commit()
    return FileResponse(script_path, filename="data_clean.py", media_type="text/x-python")
