import pytest

from backend.app.core.config import Settings
from backend.app.core.errors import ProviderError
from backend.app.core.execution import ExecutionEngine
from backend.app.core.provider_factory import ProviderFactory
from backend.app.models.internal import ProviderResult, ValidatedChatRequest
from backend.app.providers.mock_provider import MockProvider


class FailingProvider(MockProvider):
    @property
    def name(self): return "failing"
    async def generate(self, request: ValidatedChatRequest) -> ProviderResult:
        raise ProviderError("temporary", provider=self.name, retryable=True)

@pytest.mark.asyncio
async def test_failover():
    settings = Settings(ai_provider="failing", provider_failover="mock", retries_per_provider=1)
    factory = ProviderFactory()
    factory.register("failing", FailingProvider)
    factory.register("mock", MockProvider)
    result = await ExecutionEngine(factory, settings).execute(
        ValidatedChatRequest(user_id="u", message="hello", request_id="r")
    )
    assert result.attempted_providers == ("failing", "mock")
