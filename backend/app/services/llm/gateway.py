import logging
import os
from collections.abc import AsyncGenerator

from litellm import acompletion
from litellm.exceptions import RateLimitError

from app.core.config import get_settings
from app.services.llm.json_utils import parse_json_object

logger = logging.getLogger(__name__)

# Gemini 2.5+ e 3.x usam tokens de "pensamento" que podem esgotar max_tokens e devolver conteúdo vazio.
_GEMINI_REASONING_PREFIXES = ("gemini/gemini-2", "gemini/gemini-3", "gemini-2", "gemini-3")


def _is_gemini_reasoning_model(model: str) -> bool:
    normalized = model.lower().replace("models/", "")
    return any(normalized.startswith(prefix) for prefix in _GEMINI_REASONING_PREFIXES)


def _gemini_kwargs(model: str) -> dict:
    if _is_gemini_reasoning_model(model):
        return {"reasoning_effort": "none"}
    return {}


def _finish_reason(response) -> str | None:
    try:
        return response.choices[0].finish_reason
    except (AttributeError, IndexError, KeyError):
        return None


def _extract_content(response) -> str:
    try:
        return response.choices[0].message.content or ""
    except (AttributeError, IndexError, KeyError):
        return ""


class LLMGateway:
    def _apply_api_keys(self) -> None:
        settings = get_settings()
        if settings.gemini_api_key:
            os.environ["GEMINI_API_KEY"] = settings.gemini_api_key
            os.environ["GOOGLE_API_KEY"] = settings.gemini_api_key
        if settings.local_model_enabled:
            os.environ["OLLAMA_API_BASE"] = settings.ollama_api_base

    @property
    def model(self) -> str:
        settings = get_settings()
        if settings.local_model_enabled:
            return settings.llm_model_local
        return settings.llm_model

    async def complete(
        self,
        messages: list[dict[str, str]],
        *,
        temperature: float = 0.3,
        max_tokens: int = 4096,
        json_mode: bool = False,
    ) -> tuple[str, int, int]:
        self._apply_api_keys()
        settings = get_settings()
        if not settings.gemini_api_key and not settings.local_model_enabled:
            raise RuntimeError(
                "GEMINI_API_KEY não está configurada. Defina no arquivo .env do projeto e reinicie o backend."
            )

        effective_max_tokens = max(max_tokens, 256)
        base_kwargs: dict = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": effective_max_tokens,
            **_gemini_kwargs(self.model),
        }
        if json_mode:
            base_kwargs["response_format"] = {"type": "json_object"}

        last_finish_reason: str | None = None
        for attempt in range(2):
            kwargs = dict(base_kwargs)
            if attempt == 1:
                kwargs["reasoning_effort"] = "none"
                kwargs["max_tokens"] = max(effective_max_tokens, 4096)
                logger.warning(
                    "LLM resposta vazia (finish_reason=%s); tentando novamente com reasoning desativado",
                    last_finish_reason,
                )

            try:
                response = await acompletion(**kwargs)
            except RateLimitError as exc:
                logger.warning("LLM rate limit: %s", exc)
                raise RuntimeError(
                    "Limite de taxa da API Gemini excedido (plano gratuito ~20 requisições/dia). "
                    "Aguarde cerca de um minuto e tente novamente, ou verifique o uso em https://ai.dev/rate-limit. "
                    f"Detalhes: {exc}"
                ) from exc
            except Exception as exc:
                logger.exception("LLM call failed")
                raise RuntimeError(f"Falha na chamada ao LLM: {exc}") from exc

            content = _extract_content(response)
            last_finish_reason = _finish_reason(response)
            if content.strip():
                usage = getattr(response, "usage", None)
                prompt_tokens = getattr(usage, "prompt_tokens", 0) if usage else 0
                completion_tokens = getattr(usage, "completion_tokens", 0) if usage else 0
                return content, prompt_tokens, completion_tokens

        raise RuntimeError(
            "O LLM retornou uma resposta vazia. "
            f"Modelo: {self.model}, finish_reason={last_finish_reason}. "
            "Isso costuma ocorrer quando o modelo usa tokens de 'pensamento' e esgota o limite. "
            "O backend já tenta desativar o reasoning automaticamente; se persistir, "
            "verifique GET /api/llm/status ou ajuste LLM_MODEL no .env."
        )

    async def stream(
        self,
        messages: list[dict[str, str]],
        *,
        temperature: float = 0.3,
        max_tokens: int = 4096,
    ) -> AsyncGenerator[str, None]:
        self._apply_api_keys()
        response = await acompletion(
            model=self.model,
            messages=messages,
            temperature=temperature,
            max_tokens=max(max_tokens, 256),
            stream=True,
            **_gemini_kwargs(self.model),
        )
        async for chunk in response:
            delta = chunk.choices[0].delta
            if delta and delta.content:
                yield delta.content

    async def complete_json(
        self,
        messages: list[dict[str, str]],
        *,
        temperature: float = 0.2,
        max_tokens: int = 4096,
    ) -> tuple[dict, str, int, int]:
        try:
            content, prompt_tokens, completion_tokens = await self.complete(
                messages,
                temperature=temperature,
                max_tokens=max_tokens,
                json_mode=True,
            )
        except RuntimeError:
            content, prompt_tokens, completion_tokens = await self.complete(
                messages,
                temperature=temperature,
                max_tokens=max_tokens,
                json_mode=False,
            )
        return parse_json_object(content), content, prompt_tokens, completion_tokens


llm_gateway = LLMGateway()
