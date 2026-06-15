import json
import os
from collections.abc import AsyncGenerator

from litellm import acompletion

from app.core.config import get_settings


class LLMGateway:
    def __init__(self) -> None:
        self.settings = get_settings()
        if self.settings.gemini_api_key:
            os.environ["GEMINI_API_KEY"] = self.settings.gemini_api_key
        if self.settings.local_model_enabled:
            os.environ["OLLAMA_API_BASE"] = self.settings.ollama_api_base

    @property
    def model(self) -> str:
        if self.settings.local_model_enabled:
            return self.settings.llm_model_local
        return self.settings.llm_model
    async def complete(
        self,
        messages: list[dict[str, str]],
        *,
        temperature: float = 0.3,
        max_tokens: int = 4096,
    ) -> tuple[str, int, int]:
        response = await acompletion(
            model=self.model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
        )
        content = response.choices[0].message.content or ""
        usage = getattr(response, "usage", None)
        prompt_tokens = getattr(usage, "prompt_tokens", 0) if usage else 0
        completion_tokens = getattr(usage, "completion_tokens", 0) if usage else 0
        return content, prompt_tokens, completion_tokens

    async def stream(
        self,
        messages: list[dict[str, str]],
        *,
        temperature: float = 0.3,
        max_tokens: int = 4096,
    ) -> AsyncGenerator[str, None]:
        response = await acompletion(
            model=self.model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            stream=True,
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
    ) -> tuple[dict, int, int]:
        content, prompt_tokens, completion_tokens = await self.complete(
            messages, temperature=temperature
        )
        cleaned = content.strip()
        if cleaned.startswith("```"):
            cleaned = cleaned.split("\n", 1)[-1]
            if cleaned.endswith("```"):
                cleaned = cleaned[:-3]
        try:
            return json.loads(cleaned), prompt_tokens, completion_tokens
        except json.JSONDecodeError:
            return {"raw": content}, prompt_tokens, completion_tokens


llm_gateway = LLMGateway()
