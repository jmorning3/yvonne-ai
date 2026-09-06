from functools import lru_cache

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", case_sensitive=False, extra="ignore"
    )

    app_name: str = "Yvonne AI"
    app_env: str = "development"
    api_prefix: str = "/api"
    ai_provider: str = "mock"
    provider_failover: str = "openai,gemini,mock"
    openai_api_key: str | None = None
    openai_model: str = "gpt-5.5"
    gemini_api_key: str | None = None
    gemini_model: str = "gemini-3.8-flash"
    request_timeout_seconds: float = Field(default=45.0, gt=0)
    retries_per_provider: int = Field(default=2, ge=1)
    retry_base_delay_seconds: float = Field(default=0.25, ge=0)
    circuit_failure_threshold: int = Field(default=3, ge=1)
    circuit_recovery_seconds: float = Field(default=30.0, gt=0)
    max_message_chars: int = Field(default=20_000, ge=1)

    @field_validator("ai_provider", mode="before")
    @classmethod
    def normalize_provider(cls, value: object) -> str:
        return str(value).strip().lower()

    @property
    def failover_order(self) -> list[str]:
        return [part.strip().lower() for part in self.provider_failover.split(",") if part.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
