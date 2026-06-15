import asyncio
import json
import os

from sqlalchemy import select, text

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

PATIENT_SAMPLES = [
    {"patient_id": 1001, "birth_year": 1965, "sex": "F"},
    {"patient_id": 1002, "birth_year": 1978, "sex": "M"},
    {"patient_id": 1003, "birth_year": 1982, "sex": "F"},
    {"patient_id": 1004, "birth_year": 1954, "sex": "M"},
    {"patient_id": 1005, "birth_year": 1990, "sex": "F"},
    {"patient_id": 1006, "birth_year": 1968, "sex": "M"},
    {"patient_id": 1007, "birth_year": 1975, "sex": "F"},
    {"patient_id": 1008, "birth_year": 1988, "sex": "Other"},
    {"patient_id": 1009, "birth_year": 1960, "sex": "M"},
    {"patient_id": 1010, "birth_year": 1995, "sex": "F"},
]

ENCOUNTER_SAMPLES = [
    {"encounter_id": 5001, "patient_id": 1001, "encounter_date": "2023-01-15", "diagnosis_code": "E11.9"},
    {"encounter_id": 5002, "patient_id": 1001, "encounter_date": "2023-06-20", "diagnosis_code": "I10"},
    {"encounter_id": 5003, "patient_id": 1002, "encounter_date": "2023-02-10", "diagnosis_code": "E11.65"},
    {"encounter_id": 5004, "patient_id": 1003, "encounter_date": "2023-03-05", "diagnosis_code": "J45.909"},
    {"encounter_id": 5005, "patient_id": 1004, "encounter_date": "2023-04-12", "diagnosis_code": "E11.9"},
    {"encounter_id": 5006, "patient_id": 1005, "encounter_date": "2023-05-18", "diagnosis_code": None},
    {"encounter_id": 5007, "patient_id": 1006, "encounter_date": "2023-07-01", "diagnosis_code": "I25.10"},
    {"encounter_id": 5008, "patient_id": 1007, "encounter_date": "2023-08-22", "diagnosis_code": "E11.9"},
    {"encounter_id": 5009, "patient_id": 1008, "encounter_date": "2023-09-30", "diagnosis_code": "M54.5"},
    {"encounter_id": 5010, "patient_id": 1009, "encounter_date": "2023-10-15", "diagnosis_code": "E11.9"},
]


async def _ensure_sample_rows_column() -> None:
    async with engine.begin() as conn:
        await conn.execute(
            text("ALTER TABLE catalog_tables ADD COLUMN IF NOT EXISTS sample_rows TEXT DEFAULT '[]'")
        )


async def _apply_demo_samples(db) -> None:
    for table_name, samples in [("patients", PATIENT_SAMPLES), ("encounters", ENCOUNTER_SAMPLES)]:
        result = await db.execute(select(CatalogTable).where(CatalogTable.name == table_name))
        table = result.scalar_one_or_none()
        if table and (not table.sample_rows or table.sample_rows == "[]"):
            table.sample_rows = json.dumps(samples)


async def seed() -> None:
    settings = get_settings()
    os.makedirs(settings.exports_dir, exist_ok=True)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    await _ensure_sample_rows_column()

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
                sample_rows=json.dumps(PATIENT_SAMPLES),
            )
            encounters = CatalogTable(
                dataset_id=dataset.id,
                name="encounters",
                description="Clinical encounter records",
                sample_rows=json.dumps(ENCOUNTER_SAMPLES),
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
        else:
            await _apply_demo_samples(db)

        await db.commit()


if __name__ == "__main__":
    asyncio.run(seed())
