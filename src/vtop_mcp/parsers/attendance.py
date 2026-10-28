"""Parse attendance HTML tables."""

from __future__ import annotations

import re

from vtop_mcp.models.attendance import AttendanceCourse, AttendanceList
from vtop_mcp.parsers.tables import find_tables, iter_data_rows


def _parse_fraction(text: str) -> tuple[int | None, int | None]:
    match = re.search(r"(\d+)\s*/\s*(\d+)", text)
    if not match:
        return None, None
    return int(match.group(1)), int(match.group(2))


def _parse_percent(text: str) -> float | None:
    match = re.search(r"(\d+(?:\.\d+)?)\s*%", text)
    return float(match.group(1)) if match else None


def parse_attendance(html: str, semester_id: str) -> AttendanceList:
    courses: list[AttendanceCourse] = []
    for table in find_tables(html):
        rows = iter_data_rows(table)
        if len(rows) < 2:
            continue
        header = " ".join(rows[0]).lower()
        if "attendance" not in header and "course" not in header:
            continue
        for row in rows[1:]:
            if len(row) < 2:
                continue
            title = row[1] if len(row) > 1 else row[0]
            code = row[0] if len(row) > 2 else None
            slot = row[2] if len(row) > 3 else None
            joined = " ".join(row)
            attended, total = _parse_fraction(joined)
            percentage = _parse_percent(joined)
            courses.append(
                AttendanceCourse(
                    code=code,
                    title=title,
                    slot=slot,
                    attended=attended,
                    total=total,
                    percentage=percentage,
                )
            )
    return AttendanceList(semester_id=semester_id, courses=courses)
