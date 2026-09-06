from abc import ABC, abstractmethod
from collections.abc import AsyncIterator

from backend.app.models.internal import ProviderResult, ValidatedChatRequest


class BaseProvider(ABC):
    @property
    @abstractmethod
    def name(self) -> str: ...

    @abstractmethod
    async def generate(self, request: ValidatedChatRequest) -> ProviderResult: ...

    @abstractmethod
    def stream(self, request: ValidatedChatRequest) -> AsyncIterator[str]: ...

    async def healthcheck(self) -> bool:
        return True
