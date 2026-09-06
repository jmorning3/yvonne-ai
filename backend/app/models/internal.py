from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field


class ImmutableModel(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


class ValidatedChatRequest(ImmutableModel):
    user_id: str
    message: str
    provider: str | None = None
    model: str | None = None
    request_id: str
    metadata: dict[str, Any] = Field(default_factory=dict)


class TokenUsage(ImmutableModel):
    input_tokens: int = 0
    output_tokens: int = 0
    total_tokens: int = 0


class ProviderResult(ImmutableModel):
    content: str
    provider: str
    model: str
    usage: TokenUsage = Field(default_factory=TokenUsage)
    finish_reason: str | None = None
    provider_request_id: str | None = None
    latency_ms: float = 0.0
    metadata: dict[str, Any] = Field(default_factory=dict)


class ExecutionResult(ImmutableModel):
    status: Literal["success"] = "success"
    request_id: str
    user_id: str
    provider_result: ProviderResult
    attempted_providers: tuple[str, ...] = ()
