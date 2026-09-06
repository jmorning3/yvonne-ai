import time
from collections.abc import AsyncIterator

import openai
from openai import AsyncOpenAI

from backend.app.core.config import Settings
from backend.app.core.errors import ProviderConfigurationError, ProviderError
from backend.app.core.prompt import YVONNE_SYSTEM_PROMPT
from backend.app.models.internal import ProviderResult, TokenUsage, ValidatedChatRequest
from backend.app.providers.base_provider import BaseProvider


class OpenAIProvider(BaseProvider):
    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self._client: AsyncOpenAI | None = None

    @property
    def name(self) -> str:
        return "openai"

    def _get_client(self) -> AsyncOpenAI:
        if not self._settings.openai_api_key:
            raise ProviderConfigurationError(
                "OPENAI_API_KEY is not configured.", provider=self.name
            )
        if self._client is None:
            self._client = AsyncOpenAI(
                api_key=self._settings.openai_api_key,
                timeout=self._settings.request_timeout_seconds,
                max_retries=0,
            )
        return self._client

    async def generate(self, request: ValidatedChatRequest) -> ProviderResult:
        client = self._get_client()
        model = request.model or self._settings.openai_model
        started = time.perf_counter()
        try:
            response = await client.responses.create(
                model=model, instructions=YVONNE_SYSTEM_PROMPT, input=request.message
            )
        except (openai.APIConnectionError, openai.RateLimitError, openai.APITimeoutError) as exc:
            raise ProviderError(str(exc), provider=self.name, retryable=True) from exc
        except openai.APIStatusError as exc:
            raise ProviderError(
                str(exc),
                provider=self.name,
                retryable=exc.status_code >= 500 or exc.status_code == 429,
                details={"statusCode": exc.status_code, "requestId": exc.request_id},
            ) from exc
        except Exception as exc:
            raise ProviderError(str(exc), provider=self.name, retryable=False) from exc

        usage = response.usage
        input_tokens = int(getattr(usage, "input_tokens", 0) or 0)
        output_tokens = int(getattr(usage, "output_tokens", 0) or 0)
        total_tokens = int(getattr(usage, "total_tokens", input_tokens + output_tokens) or 0)
        return ProviderResult(
            content=response.output_text or "",
            provider=self.name,
            model=str(response.model or model),
            usage=TokenUsage(
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                total_tokens=total_tokens,
            ),
            finish_reason=str(response.status or "completed"),
            provider_request_id=getattr(response, "_request_id", None),
            latency_ms=(time.perf_counter() - started) * 1000,
            metadata={"responseId": response.id},
        )

    async def stream(self, request: ValidatedChatRequest) -> AsyncIterator[str]:
        client = self._get_client()
        model = request.model or self._settings.openai_model
        try:
            stream = await client.responses.create(
                model=model,
                instructions=YVONNE_SYSTEM_PROMPT,
                input=request.message,
                stream=True,
            )
            async for event in stream:
                if event.type == "response.output_text.delta":
                    yield event.delta
        except openai.APIError as exc:
            raise ProviderError(str(exc), provider=self.name, retryable=True) from exc

    async def healthcheck(self) -> bool:
        return bool(self._settings.openai_api_key)
