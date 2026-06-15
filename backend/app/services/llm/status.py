import asyncio

from app.core.config import _ENV_FILE, get_settings
from app.services.llm.gateway import llm_gateway


async def check_llm_status() -> dict:
    settings = get_settings()
    status = {
        "model": llm_gateway.model,
        "gemini_api_key_set": bool(settings.gemini_api_key),
        "env_file": str(_ENV_FILE),
        "env_file_exists": _ENV_FILE.exists(),
        "ok": False,
        "error": None,
        "test_response": None,
    }
    try:
        content, _, _ = await llm_gateway.complete(
            [{"role": "user", "content": "Reply with exactly: OK"}],
            max_tokens=16,
        )
        status["ok"] = content.strip().upper().startswith("OK")
        status["test_response"] = content[:100]
    except Exception as exc:
        status["error"] = str(exc)
    return status


if __name__ == "__main__":
    print(asyncio.run(check_llm_status()))
