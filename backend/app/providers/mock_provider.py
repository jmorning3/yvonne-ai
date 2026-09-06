from collections.abc import AsyncIterator

from backend.app.models.internal import ProviderResult, TokenUsage, ValidatedChatRequest
from backend.app.providers.base_provider import BaseProvider


class MockProvider(BaseProvider):
    @property
    def name(self) -> str:
        return "mock"

    async def generate(self, request: ValidatedChatRequest) -> ProviderResult:
        content = f"Mock response: {request.message}"
        input_tokens = len(request.message.split())
        output_tokens = len(content.split())
        return ProviderResult(
            content=content,
            provider=self.name,
            model=request.model or "mock-v1",
            usage=TokenUsage(
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                total_tokens=input_tokens + output_tokens,
            ),
            finish_reason="completed",
            provider_request_id=f"mock-{request.request_id}",
        )

    async def stream(self, request: ValidatedChatRequest) -> AsyncIterator[str]:
        result = await self.generate(request)
        for index, token in enumerate(result.content.split(" ")):
            yield token if index == 0 else f" {token}"
