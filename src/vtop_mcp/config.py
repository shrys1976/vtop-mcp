"""Application configuration from environment."""

from __future__ import annotations

from pathlib import Path

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

from vtop_mcp.vtop.constants import (
    ALLOWED_HOSTNAME,
    BASE_URL,
    DEFAULT_MAX_CAPTCHA_RETRIES,
)


def default_session_path() -> Path:
    return Path.home() / ".config" / "vtop-mcp" / "session.enc"


class Settings(BaseSettings):
    """VTOP MCP settings (env prefix ``VTOP_`` where noted)."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        populate_by_name=True,
    )

    base_url: str = Field(default=BASE_URL, validation_alias="VTOP_BASE_URL")
    regno: str | None = Field(default=None, validation_alias="VTOP_REGNO")
    password: str | None = Field(default=None, validation_alias="VTOP_PASSWORD")
    max_captcha_retries: int = Field(
        default=DEFAULT_MAX_CAPTCHA_RETRIES,
        validation_alias="VTOP_MAX_CAPTCHA_RETRIES",
    )
    session_file: Path = Field(
        default_factory=default_session_path,
        validation_alias="VTOP_SESSION_FILE",
    )
    session_key_env: str | None = Field(
        default=None,
        validation_alias="VTOP_SESSION_KEY",
        description="Fernet key (testing only); production uses OS keyring.",
    )
    request_timeout_sec: float = Field(default=30.0, validation_alias="VTOP_TIMEOUT_SEC")
    max_redirects: int = Field(default=10, validation_alias="VTOP_MAX_REDIRECTS")

    @field_validator("base_url")
    @classmethod
    def base_url_must_match_allowlist(cls, value: str) -> str:
        normalized = value.rstrip("/")
        if ALLOWED_HOSTNAME not in normalized:
            msg = f"VTOP_BASE_URL must use host {ALLOWED_HOSTNAME!r}"
            raise ValueError(msg)
        return normalized

    @field_validator("session_file", mode="before")
    @classmethod
    def expand_session_path(cls, value: str | Path) -> Path:
        return Path(value).expanduser()
