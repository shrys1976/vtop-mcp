"""Parse academic calendar HTML."""

from __future__ import annotations

from vtop_mcp.models.calendar import AcademicCalendar, CalendarEvent
from vtop_mcp.parsers.tables import find_tables, iter_data_rows


def parse_academic_calendar(html: str, semester_id: str | None) -> AcademicCalendar:
    events: list[CalendarEvent] = []
    for table in find_tables(html):
        rows = iter_data_rows(table)
        if len(rows) < 2:
            continue
        header = " ".join(rows[0]).lower()
        if not any(key in header for key in ("date", "event", "calendar", "day")):
            continue
        for row in rows[1:]:
            if len(row) < 2:
                continue
            events.append(
                CalendarEvent(
                    date=row[0],
                    title=row[1],
                    category=row[2] if len(row) > 2 else None,
                )
            )
    return AcademicCalendar(semester_id=semester_id, events=events)
