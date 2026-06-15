import enum
from datetime import datetime, timezone

from sqlalchemy import (
    Boolean,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class UserRole(str, enum.Enum):
    researcher = "researcher"
    admin = "admin"


class WizardType(str, enum.Enum):
    project_doc = "project_doc"
    data_clean = "data_clean"


class WizardStep(str, enum.Enum):
    basics = "basics"
    intake = "intake"
    review = "review"
    quality = "quality"
    export = "export"
    select_dataset = "select_dataset"
    link_project = "link_project"
    schema_explore = "schema_explore"
    discussion = "discussion"
    script_draft = "script_draft"
    validation = "validation"


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    full_name: Mapped[str] = mapped_column(String(255))
    hashed_password: Mapped[str] = mapped_column(String(255))
    role: Mapped[UserRole] = mapped_column(Enum(UserRole), default=UserRole.researcher)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    wizard_sessions: Mapped[list["WizardSession"]] = relationship(back_populates="user")


class AppSetting(Base):
    __tablename__ = "app_settings"

    key: Mapped[str] = mapped_column(String(100), primary_key=True)
    value: Mapped[str] = mapped_column(Text)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )


class Dataset(Base):
    __tablename__ = "datasets"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(255), unique=True)
    description: Mapped[str] = mapped_column(Text, default="")
    enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    tables: Mapped[list["CatalogTable"]] = relationship(
        back_populates="dataset", cascade="all, delete-orphan"
    )


class CatalogTable(Base):
    __tablename__ = "catalog_tables"
    __table_args__ = (UniqueConstraint("dataset_id", "name", name="uq_table_dataset_name"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    dataset_id: Mapped[int] = mapped_column(ForeignKey("datasets.id", ondelete="CASCADE"))
    name: Mapped[str] = mapped_column(String(255))
    description: Mapped[str] = mapped_column(Text, default="")
    sample_rows: Mapped[str] = mapped_column(Text, default="[]")

    dataset: Mapped["Dataset"] = relationship(back_populates="tables")
    columns: Mapped[list["CatalogColumn"]] = relationship(
        back_populates="table", cascade="all, delete-orphan"
    )
    relationships_from: Mapped[list["TableRelationship"]] = relationship(
        back_populates="from_table",
        foreign_keys="TableRelationship.from_table_id",
        cascade="all, delete-orphan",
    )


class CatalogColumn(Base):
    __tablename__ = "catalog_columns"
    __table_args__ = (UniqueConstraint("table_id", "name", name="uq_column_table_name"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    table_id: Mapped[int] = mapped_column(ForeignKey("catalog_tables.id", ondelete="CASCADE"))
    name: Mapped[str] = mapped_column(String(255))
    data_type: Mapped[str] = mapped_column(String(100))
    nullable: Mapped[bool] = mapped_column(Boolean, default=True)
    is_primary_key: Mapped[bool] = mapped_column(Boolean, default=False)
    is_foreign_key: Mapped[bool] = mapped_column(Boolean, default=False)
    description: Mapped[str] = mapped_column(Text, default="")
    valid_values: Mapped[str] = mapped_column(Text, default="")
    coding_notes: Mapped[str] = mapped_column(Text, default="")
    is_phi: Mapped[bool] = mapped_column(Boolean, default=False)
    notes: Mapped[str] = mapped_column(Text, default="")

    table: Mapped["CatalogTable"] = relationship(back_populates="columns")


class TableRelationship(Base):
    __tablename__ = "table_relationships"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    from_table_id: Mapped[int] = mapped_column(ForeignKey("catalog_tables.id", ondelete="CASCADE"))
    to_table_id: Mapped[int] = mapped_column(ForeignKey("catalog_tables.id", ondelete="CASCADE"))
    from_column: Mapped[str] = mapped_column(String(255))
    to_column: Mapped[str] = mapped_column(String(255))
    relationship_type: Mapped[str] = mapped_column(String(50), default="many_to_one")
    description: Mapped[str] = mapped_column(Text, default="")

    from_table: Mapped["CatalogTable"] = relationship(
        back_populates="relationships_from", foreign_keys=[from_table_id]
    )


class WizardSession(Base):
    __tablename__ = "wizard_sessions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    wizard_type: Mapped[WizardType] = mapped_column(Enum(WizardType))
    current_step: Mapped[str] = mapped_column(String(50))
    title: Mapped[str] = mapped_column(String(255), default="Untitled")
    dataset_id: Mapped[int | None] = mapped_column(ForeignKey("datasets.id"), nullable=True)
    linked_project_id: Mapped[int | None] = mapped_column(
        ForeignKey("wizard_sessions.id"), nullable=True
    )
    section_data: Mapped[str] = mapped_column(Text, default="{}")
    script_content: Mapped[str] = mapped_column(Text, default="")
    validation_result: Mapped[str] = mapped_column(Text, default="{}")
    quality_checklist: Mapped[str] = mapped_column(Text, default="{}")
    llm_model_used: Mapped[str] = mapped_column(String(100), default="")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    user: Mapped["User"] = relationship(back_populates="wizard_sessions")
    messages: Mapped[list["ChatMessage"]] = relationship(
        back_populates="session", cascade="all, delete-orphan"
    )
    exports: Mapped[list["ExportArtifact"]] = relationship(
        back_populates="session", cascade="all, delete-orphan"
    )


class ChatMessage(Base):
    __tablename__ = "chat_messages"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    session_id: Mapped[int] = mapped_column(ForeignKey("wizard_sessions.id", ondelete="CASCADE"))
    role: Mapped[str] = mapped_column(String(20))
    content: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    session: Mapped["WizardSession"] = relationship(back_populates="messages")


class ExportArtifact(Base):
    __tablename__ = "export_artifacts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    session_id: Mapped[int] = mapped_column(ForeignKey("wizard_sessions.id", ondelete="CASCADE"))
    filename: Mapped[str] = mapped_column(String(255))
    file_path: Mapped[str] = mapped_column(String(500))
    artifact_type: Mapped[str] = mapped_column(String(50))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    session: Mapped["WizardSession"] = relationship(back_populates="exports")


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    action: Mapped[str] = mapped_column(String(100))
    resource_type: Mapped[str] = mapped_column(String(100), default="")
    resource_id: Mapped[str] = mapped_column(String(100), default="")
    details: Mapped[str] = mapped_column(Text, default="")
    ip_address: Mapped[str] = mapped_column(String(50), default="")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
