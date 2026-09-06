import time
from collections.abc import AsyncIterator
from typing import Any, cast

from google import genai

from backend.app.core.config import Settings
from backend.app.core.errors import ProviderConfigurationError, ProviderError
from backend.app.core.prompt import YVONNE_SYSTEM_PROMPT
from backend.app.models.internal import ProviderResult, TokenUsage, ValidatedChatRequest
from backend.app.providers.base_provider import BaseProvider


class GeminiProvider(BaseProvider):
    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self._client: genai.Client | None = None

    @property
    def name(self) -> str:
        return "gemini"

    def _get_client(self) -> genai.Client:
        if not self._settings.gemini_api_key:
            raise ProviderConfigurationError(
                "GEMINI_API_KEY is not configured.", provider=self.name
            )
        if self._client is None:
            self._client = genai.Client(api_key=self._settings.gemini_api_key)
        return self._client

    @staticmethod
    def _status_code(exc: Exception) -> int | None:
        value = getattr(exc, "status_code", None) or getattr(exc, "code", None)
        return value if isinstance(value, int) else None

    async def generate(self, request: ValidatedChatRequest) -> ProviderResult:
        client = self._get_client()
        model = request.model or self._settings.gemini_model
        started = time.perf_counter()
        try:
            interaction = cast(
                Any,
                await client.aio.interactions.create(
                    model=model,
                    system_instruction=YVONNE_SYSTEM_PROMPT,
                    input=request.message,
                    store=False,
                ),
            )
        except Exception as exc:
            status_code = self._status_code(exc)
            raise ProviderError(
                str(exc),
                provider=self.name,
                retryable=status_code in {408, 429, 500, 502, 503, 504} or status_code is None,
                details={"statusCode": status_code} if status_code is not None else None,
            ) from exc

        usage = getattr(interaction, "usage", None)
        input_tokens = int(getattr(usage, "input_tokens", 0) or 0)
        output_tokens = int(getattr(usage, "output_tokens", 0) or 0)
        total_tokens = int(getattr(usage, "total_tokens", input_tokens + output_tokens) or 0)
        return ProviderResult(
            content=interaction.output_text or "",
            provider=self.name,
            model=model,
            usage=TokenUsage(
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                total_tokens=total_tokens,
            ),
            finish_reason="completed",
            provider_request_id=str(getattr(interaction, "id", "") or "") or None,
            latency_ms=(time.perf_counter() - started) * 1000,
        )

    async def stream(self, request: ValidatedChatRequest) -> AsyncIterator[str]:
        client = self._get_client()
        model = request.model or self._settings.gemini_model
        try:
            stream = cast(
                Any,
                await client.aio.interactions.create(
                    model=model,
                    system_instruction=YVONNE_SYSTEM_PROMPT,
                    input=request.message,
                    store=False,
                    stream=True,
                ),
            )
            async for event in stream:
                if getattr(event, "event_type", None) == "step.delta":
                    delta = getattr(event, "delta", None)
                    text = getattr(delta, "text", None)
                    if getattr(delta, "type", None) == "text" and text:
                        yield str(text)
        except Exception as exc:
            raise ProviderError(str(exc), provider=self.name, retryable=True) from exc

    async def healthcheck(self) -> bool:
        return bool(self._settings.gemini_api_key)
