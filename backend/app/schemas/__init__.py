from pydantic import BaseModel, EmailStr, Field


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserCreate(BaseModel):
    email: EmailStr
    full_name: str
    password: str = Field(min_length=8)
    role: str = "researcher"


class UserOut(BaseModel):
    id: int
    email: str
    full_name: str
    role: str
    is_active: bool

    model_config = {"from_attributes": True}


class LoginRequest(BaseModel):
    email: str
    password: str


class AppSettingOut(BaseModel):
    key: str
    value: str

    model_config = {"from_attributes": True}


class AppSettingUpdate(BaseModel):
    value: str


class DatasetCreate(BaseModel):
    name: str
    description: str = ""
    enabled: bool = True


class DatasetUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    enabled: bool | None = None


class DatasetOut(BaseModel):
    id: int
    name: str
    description: str
    enabled: bool

    model_config = {"from_attributes": True}


class CatalogColumnCreate(BaseModel):
    name: str
    data_type: str
    nullable: bool = True
    is_primary_key: bool = False
    is_foreign_key: bool = False
    description: str = ""
    valid_values: str = ""
    coding_notes: str = ""
    is_phi: bool = False
    notes: str = ""


class CatalogColumnOut(CatalogColumnCreate):
    id: int
    table_id: int

    model_config = {"from_attributes": True}


class CatalogTableCreate(BaseModel):
    name: str
    description: str = ""


class CatalogTableOut(BaseModel):
    id: int
    dataset_id: int
    name: str
    description: str
    columns: list[CatalogColumnOut] = []

    model_config = {"from_attributes": True}


class TableRelationshipCreate(BaseModel):
    from_table_id: int
    to_table_id: int
    from_column: str
    to_column: str
    relationship_type: str = "many_to_one"
    description: str = ""


class TableRelationshipOut(TableRelationshipCreate):
    id: int

    model_config = {"from_attributes": True}


class WizardSessionCreate(BaseModel):
    wizard_type: str
    title: str = "Untitled"


class WizardSessionUpdate(BaseModel):
    title: str | None = None
    current_step: str | None = None
    dataset_id: int | None = None
    linked_project_id: int | None = None
    section_data: dict | None = None
    script_content: str | None = None


class ChatMessageCreate(BaseModel):
    content: str


class ImportTextRequest(BaseModel):
    full_text: str = Field(min_length=20)


class ChatMessageOut(BaseModel):
    id: int
    role: str
    content: str
    created_at: str

    model_config = {"from_attributes": True}


class WizardSessionOut(BaseModel):
    id: int
    wizard_type: str
    current_step: str
    title: str
    dataset_id: int | None
    linked_project_id: int | None
    section_data: dict
    script_content: str
    validation_result: dict
    quality_checklist: dict
    llm_model_used: str
    created_at: str
    updated_at: str
    messages: list[ChatMessageOut] = []


class QualityCheckItem(BaseModel):
    item: str
    passed: bool
    note: str = ""


class ValidationResult(BaseModel):
    valid: bool
    syntax_ok: bool
    lint_ok: bool
    safety_ok: bool
    issues: list[str] = []


class AuditLogOut(BaseModel):
    id: int
    user_id: int | None
    action: str
    resource_type: str
    resource_id: str
    details: str
    created_at: str

    model_config = {"from_attributes": True}
