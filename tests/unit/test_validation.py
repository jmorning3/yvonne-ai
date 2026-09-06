import pytest

from backend.app.core.config import Settings
from backend.app.core.errors import RequestValidationError
from backend.app.core.validation import ValidationPipelineExecutor
from backend.app.models.requests import ChatRequest


def test_validation_normalizes_input():
    result = ValidationPipelineExecutor(Settings(), {"mock"}).execute(
        ChatRequest(userId=" user-1 ", message=" hello ", provider=" MOCK ")
    )
    assert (result.user_id, result.message, result.provider) == ("user-1", "hello", "mock")

def test_validation_rejects_unknown_provider():
    with pytest.raises(RequestValidationError):
        ValidationPipelineExecutor(Settings(), {"mock"}).execute(
            ChatRequest(userId="u", message="hello", provider="unknown")
        )
