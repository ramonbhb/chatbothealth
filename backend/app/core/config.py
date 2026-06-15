from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_name: str = "Health Research Assistant"
    secret_key: str = "change-me-in-production-use-openssl-rand"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 480

    database_url: str = "postgresql+asyncpg://hra:hra_secret@db:5432/hra"
    exports_dir: str = "/app/exports"

    llm_model: str = "gemini/gemini-2.0-flash"
    llm_model_local: str = "ollama/llama3"
    gemini_api_key: str = ""
    ollama_api_base: str = "http://host.docker.internal:11434"
    local_model_enabled: bool = False
    audit_log_prompts: bool = False
    session_retention_days: int = 90

    max_active_datasets: int = 1
    institution_name: str = "Research Institution"
    allow_registration: bool = False

    cors_origins: str = "http://localhost:5173,http://localhost:3000"


@lru_cache
def get_settings() -> Settings:
    return Settings()
