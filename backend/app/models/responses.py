from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

from backend.app.models.internal import TokenUsage


class FrozenResponseModel(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, populate_by_name=True)


class ChatData(FrozenResponseModel):
    role: Literal["assistant"] = "assistant"
    content: str
    provider: str
    model: str
    finish_reason: str | None = Field(default=None, alias="finishReason")


class ResponseMetadata(FrozenResponseModel):
    request_id: str = Field(alias="requestId")
    user_id: str | None = Field(default=None, alias="userId")
    provider_request_id: str | None = Field(default=None, alias="providerRequestId")
    latency_ms: float | None = Field(default=None, alias="latencyMs")
    attempted_providers: tuple[str, ...] = Field(default=(), alias="attemptedProviders")
    extra: dict[str, Any] = Field(default_factory=dict)


class ErrorPayload(FrozenResponseModel):
    code: str
    message: str
    details: dict[str, Any] = Field(default_factory=dict)


class ChatResponse(FrozenResponseModel):
    status: Literal["success", "error"]
    message: str
    data: ChatData | None = None
    usage: TokenUsage | None = None
    metadata: ResponseMetadata
    error: ErrorPayload | None = None


class HealthResponse(FrozenResponseModel):
    status: Literal["ok"]
    service: str
    version: str
    providers: tuple[str, ...]
