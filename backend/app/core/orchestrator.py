from uuid import uuid4

from backend.app.core.errors import YvonneError
from backend.app.core.execution import ExecutionEngine
from backend.app.core.response_mapper import MappedResponse, ResponseMapper
from backend.app.core.validation import ValidationPipelineExecutor
from backend.app.models.requests import ChatRequest


class Orchestrator:
    def __init__(
        self,
        *,
        validator: ValidationPipelineExecutor,
        engine: ExecutionEngine,
        response_mapper: ResponseMapper,
    ) -> None:
        self._validator = validator
        self._engine = engine
        self._response_mapper = response_mapper

    async def process(self, request: ChatRequest) -> MappedResponse:
        fallback_request_id = request.request_id or str(uuid4())
        try:
            validated = self._validator.execute(request)
            return self._response_mapper.success(await self._engine.execute(validated))
        except YvonneError as exc:
            return self._response_mapper.error(
                exc, request_id=fallback_request_id, user_id=request.user_id.strip() or None
            )
