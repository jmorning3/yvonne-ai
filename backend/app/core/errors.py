from dataclasses import asdict, dataclass
from typing import Any


class YvonneError(Exception):
    code = "YVONNE_ERROR"
    http_status = 500

    def __init__(self, message: str, *, details: dict[str, Any] | None = None) -> None:
        super().__init__(message)
        self.message = message
        self.details = details or {}


class RequestValidationError(YvonneError):
    code = "VALIDATION_ERROR"
    http_status = 422


class ProviderError(YvonneError):
    code = "PROVIDER_ERROR"
    http_status = 502

    def __init__(
        self,
        message: str,
        *,
        provider: str,
        retryable: bool = True,
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message, details={"provider": provider, **(details or {})})
        self.provider = provider
        self.retryable = retryable


class ProviderConfigurationError(ProviderError):
    code = "PROVIDER_CONFIGURATION_ERROR"
    http_status = 503

    def __init__(self, message: str, *, provider: str) -> None:
        super().__init__(message, provider=provider, retryable=False)


class CircuitOpenError(ProviderError):
    code = "CIRCUIT_OPEN"
    http_status = 503

    def __init__(self, *, provider: str) -> None:
        super().__init__(
            f"Circuit breaker is open for provider '{provider}'.",
            provider=provider,
            retryable=False,
        )


@dataclass(frozen=True, slots=True)
class AttemptFailure:
    provider: str
    attempt: int
    code: str
    message: str
    retryable: bool


class ExecutionExhaustedError(YvonneError):
    code = "ALL_PROVIDERS_FAILED"
    http_status = 503

    def __init__(self, failures: list[AttemptFailure]) -> None:
        super().__init__(
            "All configured AI providers failed.",
            details={"attempts": [asdict(item) for item in failures]},
        )
        self.failures = failures
