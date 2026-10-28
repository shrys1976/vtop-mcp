"""Semester grades models."""

from __future__ import annotations

from pydantic import BaseModel


class GradeCourse(BaseModel):
    code: str | None = None
    title: str | None = None
    course_type: str | None = None
    credits_l: str | None = None
    credits_p: str | None = None
    credits_j: str | None = None
    credits_c: str | None = None
    grading_type: str | None = None
    grand_total: str | None = None
    grade: str | None = None
    counts_toward_gpa: bool = True


class GradeList(BaseModel):
    semester_id: str
    gpa: float | None = None
    courses: list[GradeCourse]
