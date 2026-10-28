"""Semester list models."""

from __future__ import annotations

from pydantic import BaseModel, Field


class Semester(BaseModel):
    id: str = Field(description="semesterSubId for semester-scoped tools")
    label: str
    active: bool = False


class SemesterList(BaseModel):
    semesters: list[Semester]
