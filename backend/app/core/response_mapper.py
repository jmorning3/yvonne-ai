from dataclasses import dataclass

from backend.app.core.errors import YvonneError
from backend.app.models.internal import ExecutionResult
from backend.app.models.responses import (
    ChatData,
    ChatResponse,
    ErrorPayload,
    ResponseMetadata,
)


@dataclass(frozen=True, slots=True)
class MappedResponse:
    body: ChatResponse
    status_code: int


class ResponseMapper:
    def success(self, result: ExecutionResult) -> MappedResponse:
        provider_result = result.provider_result
        return MappedResponse(
            body=ChatResponse(
                status="success",
                message="Request completed successfully.",
                data=ChatData(
                    content=provider_result.content,
                    provider=provider_result.provider,
                    model=provider_result.model,
                    finishReason=provider_result.finish_reason,
                ),
                usage=provider_result.usage,
                metadata=ResponseMetadata(
                    requestId=result.request_id,
                    userId=result.user_id,
                    providerRequestId=provider_result.provider_request_id,
                    latencyMs=provider_result.latency_ms,
                    attemptedProviders=result.attempted_providers,
                    extra=provider_result.metadata,
                ),
            ),
            status_code=200,
        )

    def error(
        self, error: YvonneError, *, request_id: str, user_id: str | None = None
    ) -> MappedResponse:
        return MappedResponse(
            body=ChatResponse(
                status="error",
                message=error.message,
                metadata=ResponseMetadata(requestId=request_id, userId=user_id),
                error=ErrorPayload(
                    code=error.code, message=error.message, details=error.details
                ),
            ),
            status_code=error.http_status,
        )
