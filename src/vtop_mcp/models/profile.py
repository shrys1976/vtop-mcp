"""Student profile model."""

from __future__ import annotations

from pydantic import BaseModel, Field


class Profile(BaseModel):
    regno: str | None = None
    name: str | None = None
    programme: str | None = None
    branch: str | None = None
    school: str | None = None
    email: str | None = Field(default=None, description="May be partially masked.")
    mobile: str | None = None
