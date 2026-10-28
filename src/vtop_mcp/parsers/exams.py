"""Parse exam schedule HTML."""

from __future__ import annotations

from vtop_mcp.models.exams import ExamEntry, ExamSchedule
from vtop_mcp.parsers.tables import find_tables, iter_data_rows


def parse_exam_schedule(html: str, semester_id: str | None) -> ExamSchedule:
    exams: list[ExamEntry] = []
    for table in find_tables(html):
        rows = iter_data_rows(table)
        if len(rows) < 2:
            continue
        header = " ".join(rows[0]).lower()
        if not any(key in header for key in ("exam", "course", "date", "venue")):
            continue
        for row in rows[1:]:
            if len(row) < 2:
                continue
            exams.append(
                ExamEntry(
                    course_code=row[0] if len(row) > 0 else None,
                    course_title=row[1] if len(row) > 1 else None,
                    exam_name=row[2] if len(row) > 2 else None,
                    date=row[3] if len(row) > 3 else None,
                    session=row[4] if len(row) > 4 else None,
                    venue=row[5] if len(row) > 5 else None,
                    seat_no=row[6] if len(row) > 6 else None,
                )
            )
    return ExamSchedule(semester_id=semester_id, exams=exams)
