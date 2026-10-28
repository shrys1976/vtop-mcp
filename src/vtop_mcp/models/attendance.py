"""Attendance models."""

from __future__ import annotations

from pydantic import BaseModel, Field


class AttendanceCourse(BaseModel):
    code: str | None = None
    title: str
    slot: str | None = None
    attended: int | None = None
    total: int | None = None
    percentage: float | None = Field(default=None, description="Attendance percentage.")


class AttendanceList(BaseModel):
    semester_id: str
    courses: list[AttendanceCourse]
