"""Parse marks / internals HTML."""

from __future__ import annotations

import re

from vtop_mcp.models.marks import CourseMarks, MarkComponent, MarksList
from vtop_mcp.parsers.tables import find_tables, iter_data_rows


def parse_marks(html: str, semester_id: str) -> MarksList:
    courses: list[CourseMarks] = []
    current: CourseMarks | None = None
    for table in find_tables(html):
        rows = iter_data_rows(table)
        for row in rows:
            if len(row) >= 2 and re.match(r"^[A-Z]{2,4}[0-9]{4}", row[0] or ""):
                current = CourseMarks(code=row[0], title=row[1], components=[])
                courses.append(current)
                continue
            if current and len(row) >= 2 and not row[0].lower().startswith("total"):
                current.components.append(
                    MarkComponent(
                        name=row[0],
                        score=row[1] if len(row) > 1 else None,
                        max_score=row[2] if len(row) > 2 else None,
                    )
                )
    return MarksList(semester_id=semester_id, courses=courses)
