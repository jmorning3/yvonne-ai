from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class ChatRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True, extra="forbid", frozen=True)

    user_id: str = Field(alias="userId", min_length=1, max_length=128)
    message: str = Field(min_length=1)
    provider: str | None = Field(default=None, max_length=64)
    model: str | None = Field(default=None, max_length=128)
    request_id: str | None = Field(default=None, alias="requestId", max_length=128)
    metadata: dict[str, Any] = Field(default_factory=dict)
