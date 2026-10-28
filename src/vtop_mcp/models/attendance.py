"""Attendance models."""

from __future__ import annotations

from pydantic import BaseModel, Field


class AttendanceCourse(BaseModel):
    code: str | None = None
    title: str
    course_type: str | None = None
    class_group: str | None = None
    class_id: str | None = None
    slot: str | None = None
    venue: str | None = None
    faculty: str | None = None
    school: str | None = None
    attended: int | None = None
    total: int | None = None
    percentage: float | None = Field(default=None, description="Attendance percentage.")
    debar_status: str | None = None


class AttendanceList(BaseModel):
    semester_id: str
    courses: list[AttendanceCourse]
