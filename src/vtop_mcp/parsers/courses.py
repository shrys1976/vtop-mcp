"""Parse registered courses HTML."""

from __future__ import annotations

import re

from vtop_mcp.models.courses import Course, CourseList
from vtop_mcp.parsers.tables import find_tables, iter_data_rows


def parse_courses(html: str, semester_id: str) -> CourseList:
    courses: list[Course] = []
    for table in find_tables(html):
        rows = iter_data_rows(table)
        if len(rows) < 2:
            continue
        for row in rows[1:]:
            if len(row) < 2:
                continue
            code = row[0]
            if not re.match(r"^[A-Z]{2,4}[0-9]{4}", code or ""):
                continue
            courses.append(
                Course(
                    code=code,
                    title=row[1],
                    slot=row[2] if len(row) > 2 else None,
                    faculty=row[3] if len(row) > 3 else None,
                    course_type=row[4] if len(row) > 4 else None,
                )
            )
    return CourseList(semester_id=semester_id, courses=courses)
