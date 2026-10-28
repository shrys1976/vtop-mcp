"""Parse timetable HTML."""

from __future__ import annotations

from vtop_mcp.models.timetable import Timetable, TimetableSlot
from vtop_mcp.parsers.tables import find_tables, iter_data_rows


def parse_timetable(html: str, semester_id: str) -> Timetable:
    slots: list[TimetableSlot] = []
    for table in find_tables(html):
        rows = iter_data_rows(table)
        if len(rows) < 2:
            continue
        header = " ".join(rows[0]).lower()
        if not any(key in header for key in ("time", "day", "course", "slot")):
            continue
        for row in rows[1:]:
            if len(row) < 3:
                continue
            slots.append(
                TimetableSlot(
                    day=row[0] if len(row) > 0 else None,
                    start_time=row[1] if len(row) > 1 else None,
                    end_time=row[2] if len(row) > 2 else None,
                    course_code=row[3] if len(row) > 3 else None,
                    course_title=row[4] if len(row) > 4 else None,
                    venue=row[5] if len(row) > 5 else None,
                    faculty=row[6] if len(row) > 6 else None,
                    slot=row[7] if len(row) > 7 else None,
                )
            )
    return Timetable(semester_id=semester_id, slots=slots)
