"""Registered courses models."""

from __future__ import annotations

from pydantic import BaseModel


class Course(BaseModel):
    code: str | None = None
    title: str
    slot: str | None = None
    venue: str | None = None
    faculty: str | None = None
    school: str | None = None
    course_type: str | None = None
    class_id: str | None = None


class CourseList(BaseModel):
    semester_id: str
    courses: list[Course]
