"""Session status model."""

from __future__ import annotations

from pydantic import BaseModel, Field


class SessionStatus(BaseModel):
    authenticated: bool
    regno: str | None = None
    session_age_seconds: float | None = Field(
        default=None,
        description="Seconds since encrypted session was last saved.",
    )
    otp_pending: bool = False
    captcha_pending: bool = False
    authorized_id_present: bool = False
