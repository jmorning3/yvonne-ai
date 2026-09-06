import pytest

from backend.app.core.provider_factory import ProviderFactory
from backend.app.providers.mock_provider import MockProvider


def test_factory_registers_and_caches():
    factory = ProviderFactory()
    factory.register("mock", MockProvider)
    assert factory.get("mock") is factory.get("mock")

def test_factory_rejects_blank_name():
    with pytest.raises(ValueError):
        ProviderFactory().register("  ", MockProvider)
