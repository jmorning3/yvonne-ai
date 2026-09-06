from collections.abc import Callable

from backend.app.providers.base_provider import BaseProvider

ProviderBuilder = Callable[[], BaseProvider]


class ProviderFactory:
    def __init__(self) -> None:
        self._builders: dict[str, ProviderBuilder] = {}
        self._instances: dict[str, BaseProvider] = {}

    def register(self, name: str, builder: ProviderBuilder) -> None:
        key = name.strip().lower()
        if not key:
            raise ValueError("Provider name cannot be blank.")
        self._builders[key] = builder
        self._instances.pop(key, None)

    def get(self, name: str) -> BaseProvider:
        key = name.strip().lower()
        if key not in self._builders:
            raise KeyError(f"Provider '{key}' is not registered.")
        if key not in self._instances:
            self._instances[key] = self._builders[key]()
        return self._instances[key]

    def names(self) -> tuple[str, ...]:
        return tuple(self._builders)
