"""Runtime settings (env-driven, ``SCHEMA_FORGE_`` prefix)."""

from __future__ import annotations

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Process configuration, overridable via env vars or a ``.env`` file."""

    model_config = SettingsConfigDict(
        env_prefix="SCHEMA_FORGE_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    host: str = "127.0.0.1"
    port: int = 8000
    log_level: str = "info"
    log_format: str = "pretty"  # "pretty" | "json"

    # ngspice executable name / path. Resolved from PATH by default.
    ngspice_bin: str = "ngspice"
    # Hard ceiling on a single simulation (seconds).
    sim_timeout_s: float = 120.0


@lru_cache
def get_settings() -> Settings:
    """Return the process-wide cached settings instance."""
    return Settings()
