"""Marks models."""

from __future__ import annotations

from pydantic import BaseModel


class MarkComponent(BaseModel):
    name: str
    max_score: str | None = None
    weightage_percent: str | None = None
    status: str | None = None
    score: str | None = None
    weightage_mark: str | None = None
    remark: str | None = None


class CourseMarks(BaseModel):
    code: str | None = None
    title: str
    class_number: str | None = None
    course_type: str | None = None
    course_system: str | None = None
    faculty: str | None = None
    slot: str | None = None
    course_mode: str | None = None
    components: list[MarkComponent] = []


class MarksList(BaseModel):
    semester_id: str
    courses: list[CourseMarks]
