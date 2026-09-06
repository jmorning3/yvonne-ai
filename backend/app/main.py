from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from backend.app.api.chat import router as chat_router
from backend.app.api.health import router as health_router
from backend.app.core.config import get_settings
from backend.app.core.execution import ExecutionEngine
from backend.app.core.orchestrator import Orchestrator
from backend.app.core.provider_factory import ProviderFactory
from backend.app.core.response_mapper import ResponseMapper
from backend.app.core.validation import ValidationPipelineExecutor
from backend.app.providers.mock_provider import MockProvider


def build_provider_factory() -> ProviderFactory:
    settings = get_settings()
    factory = ProviderFactory()
    factory.register("mock", MockProvider)

    def build_openai_provider():
        from backend.app.providers.openai_provider import OpenAIProvider
        return OpenAIProvider(settings)

    def build_gemini_provider():
        from backend.app.providers.gemini_provider import GeminiProvider
        return GeminiProvider(settings)

    factory.register("openai", build_openai_provider)
    factory.register("gemini", build_gemini_provider)
    return factory


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    settings = get_settings()
    factory = build_provider_factory()
    app.state.provider_factory = factory
    app.state.orchestrator = Orchestrator(
        validator=ValidationPipelineExecutor(settings, set(factory.names())),
        engine=ExecutionEngine(factory, settings),
        response_mapper=ResponseMapper(),
    )
    yield


settings = get_settings()
app = FastAPI(title=settings.app_name, version="0.1.0", lifespan=lifespan)
app.include_router(health_router, prefix=settings.api_prefix)
app.include_router(chat_router, prefix=settings.api_prefix)
