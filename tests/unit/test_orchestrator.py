import pytest

from backend.app.core.config import Settings
from backend.app.core.execution import ExecutionEngine
from backend.app.core.orchestrator import Orchestrator
from backend.app.core.provider_factory import ProviderFactory
from backend.app.core.response_mapper import ResponseMapper
from backend.app.core.validation import ValidationPipelineExecutor
from backend.app.models.requests import ChatRequest
from backend.app.providers.mock_provider import MockProvider


@pytest.mark.asyncio
async def test_orchestrator_happy_path():
    settings = Settings(ai_provider="mock", provider_failover="mock")
    factory = ProviderFactory()
    factory.register("mock", MockProvider)
    orchestrator = Orchestrator(
        validator=ValidationPipelineExecutor(settings, {"mock"}),
        engine=ExecutionEngine(factory, settings),
        response_mapper=ResponseMapper(),
    )
    mapped = await orchestrator.process(ChatRequest(userId="u", message="Hello Yvonne"))
    assert mapped.status_code == 200
    assert mapped.body.data and mapped.body.data.provider == "mock"
