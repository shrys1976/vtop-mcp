"""Timetable models."""

from __future__ import annotations

from pydantic import BaseModel


class TimetableSlot(BaseModel):
    day: str | None = None
    row_kind: str | None = None
    start_time: str | None = None
    end_time: str | None = None
    course_code: str | None = None
    course_title: str | None = None
    course_type: str | None = None
    venue: str | None = None
    faculty: str | None = None
    slot: str | None = None


class Timetable(BaseModel):
    semester_id: str
    slots: list[TimetableSlot]
