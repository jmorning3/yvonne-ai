from uuid import uuid4

from backend.app.core.config import Settings
from backend.app.core.errors import RequestValidationError
from backend.app.models.internal import ValidatedChatRequest
from backend.app.models.requests import ChatRequest


class ValidationPipelineExecutor:
    def __init__(self, settings: Settings, supported_providers: set[str]) -> None:
        self._settings = settings
        self._supported_providers = {name.lower() for name in supported_providers}

    def execute(self, request: ChatRequest) -> ValidatedChatRequest:
        user_id = request.user_id.strip()
        message = request.message.strip()
        if not user_id:
            raise RequestValidationError("userId must not be blank.")
        if not message:
            raise RequestValidationError("message must not be blank.")
        if len(message) > self._settings.max_message_chars:
            raise RequestValidationError(
                f"message exceeds maximum length of {self._settings.max_message_chars} characters."
            )
        provider = request.provider.lower().strip() if request.provider else None
        if provider and provider not in self._supported_providers:
            raise RequestValidationError(
                f"Unsupported provider '{provider}'.",
                details={"supportedProviders": sorted(self._supported_providers)},
            )
        model = request.model.strip() if request.model else None
        if request.model is not None and not model:
            raise RequestValidationError("model must not be blank when provided.")
        return ValidatedChatRequest(
            user_id=user_id,
            message=message,
            provider=provider,
            model=model,
            request_id=request.request_id or str(uuid4()),
            metadata=dict(request.metadata),
        )
