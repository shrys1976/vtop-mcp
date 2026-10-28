"""Proctor details model."""

from __future__ import annotations

from pydantic import BaseModel


class ProctorDetails(BaseModel):
    faculty_id: str | None = None
    name: str | None = None
    designation: str | None = None
    school: str | None = None
    cabin: str | None = None
    department: str | None = None
    email: str | None = None
    intercom: str | None = None
    mobile: str | None = None
