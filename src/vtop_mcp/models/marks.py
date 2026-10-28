"""Marks models."""

from __future__ import annotations

from pydantic import BaseModel


class MarkComponent(BaseModel):
    name: str
    score: str | None = None
    max_score: str | None = None


class CourseMarks(BaseModel):
    code: str | None = None
    title: str
    components: list[MarkComponent] = []


class MarksList(BaseModel):
    semester_id: str
    courses: list[CourseMarks]
