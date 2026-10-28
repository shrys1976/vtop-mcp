"""HOD and Dean contact models."""

from __future__ import annotations

from pydantic import BaseModel


class OfficialContact(BaseModel):
    role: str
    name: str | None = None
    designation: str | None = None
    cabin: str | None = None
    email: str | None = None


class HodDeanInfo(BaseModel):
    dean: OfficialContact | None = None
    hod: OfficialContact | None = None
