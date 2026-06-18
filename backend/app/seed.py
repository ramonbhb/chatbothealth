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
    {"patient_id": 1008, "birth_year": 1988, "sex": "Outro"},
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


async def _demo_dataset(db):
    for name in ("Conjunto de Saúde de Exemplo", "Sample Health Dataset"):
        result = await db.execute(select(Dataset).where(Dataset.name == name))
        dataset = result.scalar_one_or_none()
        if dataset:
            return dataset
    return None


async def _migrate_demo_dataset_labels(db) -> None:
    dataset = await _demo_dataset(db)
    if not dataset:
        return
    dataset.name = "Conjunto de Saúde de Exemplo"
    dataset.description = "Conjunto de dados de demonstração para desenvolvimento e testes"

    for table_name, description in [
        ("patients", "Registros demográficos e de inclusão de pacientes"),
        ("encounters", "Registros de encontros clínicos"),
    ]:
        table_result = await db.execute(
            select(CatalogTable).where(
                CatalogTable.dataset_id == dataset.id,
                CatalogTable.name == table_name,
            )
        )
        table = table_result.scalar_one_or_none()
        if table:
            table.description = description


async def _apply_demo_samples(db) -> None:
    dataset = await _demo_dataset(db)
    if not dataset:
        return
    for table_name, samples in [("patients", PATIENT_SAMPLES), ("encounters", ENCOUNTER_SAMPLES)]:
        result = await db.execute(
            select(CatalogTable).where(
                CatalogTable.dataset_id == dataset.id,
                CatalogTable.name == table_name,
            )
        )
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
                    full_name="Administrador do Sistema",
                    hashed_password=get_password_hash("admin12345"),
                    role=UserRole.admin,
                )
            )
            db.add(
                User(
                    email="researcher@hra.local",
                    full_name="Pesquisador Demo",
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

        dataset_result = await db.execute(select(Dataset).where(Dataset.name == "Conjunto de Saúde de Exemplo"))
        if not dataset_result.scalar_one_or_none():
            dataset = Dataset(
                name="Conjunto de Saúde de Exemplo",
                description="Conjunto de dados de demonstração para desenvolvimento e testes",
                enabled=True,
            )
            db.add(dataset)
            await db.flush()

            patients = CatalogTable(
                dataset_id=dataset.id,
                name="patients",
                description="Registros demográficos e de inclusão de pacientes",
                sample_rows=json.dumps(PATIENT_SAMPLES),
            )
            encounters = CatalogTable(
                dataset_id=dataset.id,
                name="encounters",
                description="Registros de encontros clínicos",
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
                        description="Identificador único do paciente",
                    ),
                    CatalogColumn(
                        table_id=patients.id,
                        name="birth_year",
                        data_type="INTEGER",
                        nullable=True,
                        description="Ano de nascimento",
                    ),
                    CatalogColumn(
                        table_id=patients.id,
                        name="sex",
                        data_type="VARCHAR(10)",
                        nullable=True,
                        valid_values="M, F, Outro, Desconhecido",
                        description="Sexo biológico ao nascer",
                    ),
                    CatalogColumn(
                        table_id=encounters.id,
                        name="encounter_id",
                        data_type="INTEGER",
                        nullable=False,
                        is_primary_key=True,
                        description="Identificador único do encontro",
                    ),
                    CatalogColumn(
                        table_id=encounters.id,
                        name="patient_id",
                        data_type="INTEGER",
                        nullable=False,
                        is_foreign_key=True,
                        description="Chave estrangeira para patients.patient_id",
                    ),
                    CatalogColumn(
                        table_id=encounters.id,
                        name="encounter_date",
                        data_type="DATE",
                        nullable=False,
                        description="Data do encontro clínico",
                    ),
                    CatalogColumn(
                        table_id=encounters.id,
                        name="diagnosis_code",
                        data_type="VARCHAR(20)",
                        nullable=True,
                        description="Código principal de diagnóstico CID 10",
                    ),
                ]
            )
        else:
            await _apply_demo_samples(db)

        await _migrate_demo_dataset_labels(db)

        await db.commit()


if __name__ == "__main__":
    asyncio.run(seed())
