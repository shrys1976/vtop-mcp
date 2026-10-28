"""Exam schedule models."""

from __future__ import annotations

from pydantic import BaseModel


class ExamEntry(BaseModel):
    course_code: str | None = None
    course_title: str | None = None
    exam_name: str | None = None
    date: str | None = None
    session: str | None = None
    venue: str | None = None
    seat_no: str | None = None


class ExamSchedule(BaseModel):
    semester_id: str | None = None
    exams: list[ExamEntry]
