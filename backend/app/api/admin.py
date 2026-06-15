from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.audit.service import log_audit
from app.core.config import get_settings
from app.core.database import get_db
from app.core.deps import get_current_admin, get_current_user
from app.models import AppSetting, AuditLog, CatalogColumn, CatalogTable, Dataset, TableRelationship, User
from app.schemas import (
    AppSettingOut,
    AppSettingUpdate,
    AuditLogOut,
    CatalogColumnCreate,
    CatalogColumnOut,
    CatalogTableCreate,
    CatalogTableOut,
    DatasetCreate,
    DatasetOut,
    DatasetUpdate,
    TableRelationshipCreate,
    TableRelationshipOut,
)

router = APIRouter(prefix="/admin", tags=["admin"])


@router.get("/settings", response_model=list[AppSettingOut])
async def list_settings(
    _: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(AppSetting))
    return result.scalars().all()


@router.put("/settings/{key}", response_model=AppSettingOut)
async def update_setting(
    key: str,
    body: AppSettingUpdate,
    request: Request,
    admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(AppSetting).where(AppSetting.key == key))
    setting = result.scalar_one_or_none()
    if setting:
        setting.value = body.value
    else:
        setting = AppSetting(key=key, value=body.value)
        db.add(setting)
    await log_audit(
        db,
        user_id=admin.id,
        action="update_setting",
        resource_type="setting",
        resource_id=key,
        details=body.value[:200],
        ip_address=request.client.host if request.client else "",
    )
    await db.commit()
    await db.refresh(setting)
    return setting


@router.get("/datasets", response_model=list[DatasetOut])
async def list_datasets_admin(
    _: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Dataset).order_by(Dataset.name))
    return result.scalars().all()


@router.post("/datasets", response_model=DatasetOut, status_code=status.HTTP_201_CREATED)
async def create_dataset(
    body: DatasetCreate,
    request: Request,
    admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    settings = get_settings()
    if body.enabled:
        enabled_count = await db.execute(select(Dataset).where(Dataset.enabled.is_(True)))
        if len(enabled_count.scalars().all()) >= settings.max_active_datasets:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Maximum active datasets ({settings.max_active_datasets}) reached",
            )
    dataset = Dataset(name=body.name, description=body.description, enabled=body.enabled)
    db.add(dataset)
    await log_audit(
        db,
        user_id=admin.id,
        action="create_dataset",
        resource_type="dataset",
        resource_id=body.name,
        ip_address=request.client.host if request.client else "",
    )
    await db.commit()
    await db.refresh(dataset)
    return dataset


@router.put("/datasets/{dataset_id}", response_model=DatasetOut)
async def update_dataset(
    dataset_id: int,
    body: DatasetUpdate,
    admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Dataset).where(Dataset.id == dataset_id))
    dataset = result.scalar_one_or_none()
    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found")
    if body.name is not None:
        dataset.name = body.name
    if body.description is not None:
        dataset.description = body.description
    if body.enabled is not None:
        dataset.enabled = body.enabled
    await db.commit()
    await db.refresh(dataset)
    return dataset


@router.delete("/datasets/{dataset_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_dataset(
    dataset_id: int,
    admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Dataset).where(Dataset.id == dataset_id))
    dataset = result.scalar_one_or_none()
    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found")
    await db.delete(dataset)
    await db.commit()


@router.get("/datasets/{dataset_id}/tables", response_model=list[CatalogTableOut])
async def list_tables(
    dataset_id: int,
    _: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(CatalogTable)
        .where(CatalogTable.dataset_id == dataset_id)
        .options(selectinload(CatalogTable.columns))
        .order_by(CatalogTable.name)
    )
    return result.scalars().all()


@router.post("/datasets/{dataset_id}/tables", response_model=CatalogTableOut, status_code=201)
async def create_table(
    dataset_id: int,
    body: CatalogTableCreate,
    admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    table = CatalogTable(dataset_id=dataset_id, name=body.name, description=body.description)
    db.add(table)
    await db.commit()
    await db.refresh(table)
    return table


@router.post("/tables/{table_id}/columns", response_model=CatalogColumnOut, status_code=201)
async def create_column(
    table_id: int,
    body: CatalogColumnCreate,
    admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    column = CatalogColumn(table_id=table_id, **body.model_dump())
    db.add(column)
    await db.commit()
    await db.refresh(column)
    return column


@router.delete("/columns/{column_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_column(
    column_id: int,
    admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(CatalogColumn).where(CatalogColumn.id == column_id))
    column = result.scalar_one_or_none()
    if not column:
        raise HTTPException(status_code=404, detail="Column not found")
    await db.delete(column)
    await db.commit()


@router.post("/relationships", response_model=TableRelationshipOut, status_code=201)
async def create_relationship(
    body: TableRelationshipCreate,
    admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    rel = TableRelationship(**body.model_dump())
    db.add(rel)
    await db.commit()
    await db.refresh(rel)
    return rel


@router.get("/audit", response_model=list[AuditLogOut])
async def list_audit_logs(
    _: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(AuditLog).order_by(AuditLog.created_at.desc()).limit(200))
    logs = result.scalars().all()
    return [
        AuditLogOut(
            id=log.id,
            user_id=log.user_id,
            action=log.action,
            resource_type=log.resource_type,
            resource_id=log.resource_id,
            details=log.details,
            created_at=log.created_at.isoformat(),
        )
        for log in logs
    ]


@router.get("/users", response_model=list[dict])
async def list_users(
    _: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(User).order_by(User.email))
    users = result.scalars().all()
    return [
        {"id": u.id, "email": u.email, "full_name": u.full_name, "role": u.role.value, "is_active": u.is_active}
        for u in users
    ]


@router.post("/maintenance/cleanup-sessions")
async def cleanup_sessions(
    admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    from app.services.retention import cleanup_expired_sessions

    count = await cleanup_expired_sessions(db)
    await log_audit(
        db,
        user_id=admin.id,
        action="cleanup_sessions",
        resource_type="maintenance",
        details=f"Removed {count} expired sessions",
    )
    return {"removed": count}
