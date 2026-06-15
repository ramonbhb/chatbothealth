import os

from app.services.llm.gateway import LLMGateway


def test_model_uses_gemini_by_default(monkeypatch):
    monkeypatch.setenv("LOCAL_MODEL_ENABLED", "false")
    from app.core.config import get_settings
    get_settings.cache_clear()
    gateway = LLMGateway()
    assert "gemini" in gateway.model or gateway.settings.llm_model == gateway.model


def test_model_switches_to_local_when_enabled(monkeypatch):
    monkeypatch.setenv("LOCAL_MODEL_ENABLED", "true")
    monkeypatch.setenv("LLM_MODEL_LOCAL", "ollama/llama3")
    from app.core.config import get_settings
    get_settings.cache_clear()
    gateway = LLMGateway()
    assert gateway.model == gateway.settings.llm_model_local
