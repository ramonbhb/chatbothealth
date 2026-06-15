import asyncio
import os

from sqlalchemy import select

from app.core.config import get_settings
from app.core.database import AsyncSessionLocal, Base, engine
from app.core.security import get_password_hash
from app.models import (
    AppSetting,
    CatalogColumn,
    CatalogTable,
    Dataset,
    User,
    UserRole,
)


async def seed() -> None:
    settings = get_settings()
    os.makedirs(settings.exports_dir, exist_ok=True)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with AsyncSessionLocal() as db:
        admin = await db.execute(select(User).where(User.email == "admin@hra.local"))
        if not admin.scalar_one_or_none():
            db.add(
                User(
                    email="admin@hra.local",
                    full_name="System Admin",
                    hashed_password=get_password_hash("admin12345"),
                    role=UserRole.admin,
                )
            )
            db.add(
                User(
                    email="researcher@hra.local",
                    full_name="Demo Researcher",
                    hashed_password=get_password_hash("research12345"),
                    role=UserRole.researcher,
                )
            )

        defaults = {
            "max_active_datasets": str(settings.max_active_datasets),
            "institution_name": settings.institution_name,
            "llm_model": settings.llm_model,
            "session_retention_days": str(settings.session_retention_days),
        }
        for key, value in defaults.items():
            existing = await db.execute(select(AppSetting).where(AppSetting.key == key))
            if not existing.scalar_one_or_none():
                db.add(AppSetting(key=key, value=value))

        dataset_result = await db.execute(select(Dataset).where(Dataset.name == "Sample Health Dataset"))
        if not dataset_result.scalar_one_or_none():
            dataset = Dataset(
                name="Sample Health Dataset",
                description="Demo dataset for development and testing",
                enabled=True,
            )
            db.add(dataset)
            await db.flush()

            patients = CatalogTable(
                dataset_id=dataset.id,
                name="patients",
                description="Patient demographic and enrollment records",
            )
            encounters = CatalogTable(
                dataset_id=dataset.id,
                name="encounters",
                description="Clinical encounter records",
            )
            db.add_all([patients, encounters])
            await db.flush()

            db.add_all(
                [
                    CatalogColumn(
                        table_id=patients.id,
                        name="patient_id",
                        data_type="INTEGER",
                        nullable=False,
                        is_primary_key=True,
                        description="Unique patient identifier",
                    ),
                    CatalogColumn(
                        table_id=patients.id,
                        name="birth_year",
                        data_type="INTEGER",
                        nullable=True,
                        description="Year of birth",
                    ),
                    CatalogColumn(
                        table_id=patients.id,
                        name="sex",
                        data_type="VARCHAR(10)",
                        nullable=True,
                        valid_values="M, F, Other, Unknown",
                        description="Biological sex at birth",
                    ),
                    CatalogColumn(
                        table_id=encounters.id,
                        name="encounter_id",
                        data_type="INTEGER",
                        nullable=False,
                        is_primary_key=True,
                        description="Unique encounter identifier",
                    ),
                    CatalogColumn(
                        table_id=encounters.id,
                        name="patient_id",
                        data_type="INTEGER",
                        nullable=False,
                        is_foreign_key=True,
                        description="Foreign key to patients.patient_id",
                    ),
                    CatalogColumn(
                        table_id=encounters.id,
                        name="encounter_date",
                        data_type="DATE",
                        nullable=False,
                        description="Date of clinical encounter",
                    ),
                    CatalogColumn(
                        table_id=encounters.id,
                        name="diagnosis_code",
                        data_type="VARCHAR(20)",
                        nullable=True,
                        description="Primary ICD-10 diagnosis code",
                    ),
                ]
            )

        await db.commit()


if __name__ == "__main__":
    asyncio.run(seed())
