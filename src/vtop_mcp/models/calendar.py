"""Academic calendar models."""

from __future__ import annotations

from pydantic import BaseModel


class CalendarEvent(BaseModel):
    date: str | None = None
    title: str
    category: str | None = None
    class_group: str | None = None
    remark: str | None = None


class AcademicCalendar(BaseModel):
    semester_id: str | None = None
    class_group_id: str | None = None
    events: list[CalendarEvent]
