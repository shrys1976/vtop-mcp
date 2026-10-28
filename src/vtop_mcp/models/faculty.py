"""Faculty search models."""

from __future__ import annotations

from pydantic import BaseModel


class FacultySearchMatch(BaseModel):
    employee_id: str
    name: str | None = None
    designation: str | None = None
    school: str | None = None


class FacultyOpenHour(BaseModel):
    day: str
    timings: str | None = None


class FacultyDetail(BaseModel):
    employee_id: str
    name: str | None = None
    designation: str | None = None
    department: str | None = None
    school: str | None = None
    email: str | None = None
    cabin: str | None = None
    open_hours: list[FacultyOpenHour] = []


class FacultySearchResult(BaseModel):
    query: str
    matches: list[FacultySearchMatch] = []
    detail: FacultyDetail | None = None
