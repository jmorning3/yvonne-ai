import asyncio
import time
from dataclasses import dataclass
from enum import StrEnum

from backend.app.core.config import Settings
from backend.app.core.errors import (
    AttemptFailure,
    CircuitOpenError,
    ExecutionExhaustedError,
    ProviderError,
)
from backend.app.core.provider_factory import ProviderFactory
from backend.app.models.internal import ExecutionResult, ValidatedChatRequest


class CircuitState(StrEnum):
    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"


@dataclass(slots=True)
class CircuitSnapshot:
    state: CircuitState = CircuitState.CLOSED
    failures: int = 0
    opened_at: float | None = None
    probe_in_flight: bool = False


class CircuitBreaker:
    def __init__(self, failure_threshold: int, recovery_seconds: float) -> None:
        self._failure_threshold = max(1, failure_threshold)
        self._recovery_seconds = max(0.1, recovery_seconds)
        self._snapshot = CircuitSnapshot()
        self._lock = asyncio.Lock()

    async def before_call(self, provider: str) -> None:
        async with self._lock:
            now = time.monotonic()
            if self._snapshot.state == CircuitState.OPEN:
                opened_at = self._snapshot.opened_at or now
                if now - opened_at < self._recovery_seconds:
                    raise CircuitOpenError(provider=provider)
                self._snapshot.state = CircuitState.HALF_OPEN
                self._snapshot.probe_in_flight = False
            if self._snapshot.state == CircuitState.HALF_OPEN:
                if self._snapshot.probe_in_flight:
                    raise CircuitOpenError(provider=provider)
                self._snapshot.probe_in_flight = True

    async def record_success(self) -> None:
        async with self._lock:
            self._snapshot = CircuitSnapshot()

    async def record_failure(self) -> None:
        async with self._lock:
            self._snapshot.probe_in_flight = False
            self._snapshot.failures += 1
            if (
                self._snapshot.state == CircuitState.HALF_OPEN
                or self._snapshot.failures >= self._failure_threshold
            ):
                self._snapshot.state = CircuitState.OPEN
                self._snapshot.opened_at = time.monotonic()

    async def state(self) -> CircuitState:
        async with self._lock:
            return self._snapshot.state


class ExecutionEngine:
    def __init__(self, factory: ProviderFactory, settings: Settings) -> None:
        self._factory = factory
        self._settings = settings
        self._circuits = {
            name: CircuitBreaker(
                settings.circuit_failure_threshold, settings.circuit_recovery_seconds
            )
            for name in factory.names()
        }

    def _provider_order(self, request: ValidatedChatRequest) -> list[str]:
        if request.provider:
            return [request.provider]
        candidates = [self._settings.ai_provider, *self._settings.failover_order]
        supported = set(self._factory.names())
        return list(dict.fromkeys(name for name in candidates if name in supported))

    async def execute(self, request: ValidatedChatRequest) -> ExecutionResult:
        provider_order = self._provider_order(request)
        failures: list[AttemptFailure] = []
        attempted: list[str] = []
        for provider_name in provider_order:
            provider = self._factory.get(provider_name)
            circuit = self._circuits[provider_name]
            for attempt in range(1, self._settings.retries_per_provider + 1):
                attempted.append(provider_name)
                try:
                    await circuit.before_call(provider_name)
                    async with asyncio.timeout(self._settings.request_timeout_seconds):
                        result = await provider.generate(request)
                    await circuit.record_success()
                    return ExecutionResult(
                        request_id=request.request_id,
                        user_id=request.user_id,
                        provider_result=result,
                        attempted_providers=tuple(attempted),
                    )
                except CircuitOpenError as exc:
                    failures.append(
                        AttemptFailure(provider_name, attempt, exc.code, exc.message, False)
                    )
                    break
                except ProviderError as exc:
                    await circuit.record_failure()
                    failures.append(
                        AttemptFailure(provider_name, attempt, exc.code, exc.message, exc.retryable)
                    )
                    if not exc.retryable:
                        break
                except TimeoutError:
                    await circuit.record_failure()
                    failures.append(
                        AttemptFailure(
                            provider_name,
                            attempt,
                            "PROVIDER_TIMEOUT",
                            f"Provider '{provider_name}' exceeded "
                            f"{self._settings.request_timeout_seconds} seconds.",
                            True,
                        )
                    )
                except Exception as exc:
                    await circuit.record_failure()
                    failures.append(
                        AttemptFailure(
                            provider_name, attempt, "UNEXPECTED_PROVIDER_ERROR", str(exc), False
                        )
                    )
                    break
                if attempt < self._settings.retries_per_provider:
                    delay = self._settings.retry_base_delay_seconds * (2 ** (attempt - 1))
                    await asyncio.sleep(delay)
        raise ExecutionExhaustedError(failures)
