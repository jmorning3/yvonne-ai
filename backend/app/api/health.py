from fastapi import APIRouter, Request

from backend.app import __version__
from backend.app.core.provider_factory import ProviderFactory
from backend.app.models.responses import HealthResponse

router = APIRouter(tags=["health"])


@router.get("/health", response_model=HealthResponse)
async def health(request: Request) -> HealthResponse:
    factory: ProviderFactory = request.app.state.provider_factory
    return HealthResponse(
        status="ok",
        service="Yvonne AI",
        version=__version__,
        providers=factory.names(),
    )
