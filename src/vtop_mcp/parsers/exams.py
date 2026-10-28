"""Parse exam schedule HTML."""

from __future__ import annotations

from bs4 import BeautifulSoup

from vtop_mcp.models.exams import ExamEntry, ExamSchedule
from vtop_mcp.parsers._common import COURSE_CODE_RE, cell_text, null_if_dash


def parse_exam_schedule(html: str, semester_id: str | None) -> ExamSchedule:
    soup = BeautifulSoup(html, "html.parser")
    exams: list[ExamEntry] = []
    current_group: str | None = None
    for tr in soup.find_all("tr"):
        cells = tr.find_all("td")
        if not cells:
            continue
        if len(cells) == 1:
            text = cell_text(cells[0]).strip()
            classes = tr.get("class") or []
            if "panelHead" in " ".join(classes) or text.upper() in (
                "FAT",
                "CAT2",
                "CAT1",
            ):
                current_group = text
            continue
        values = [cell_text(c) for c in cells]
        if "course code" in " ".join(values).lower():
            continue
        if len(values) >= 13 and COURSE_CODE_RE.match(values[1] or ""):
            exams.append(
                ExamEntry(
                    course_code=values[1],
                    course_title=values[2],
                    course_type=values[3],
                    class_id=values[4],
                    slot=values[5],
                    exam_name=current_group,
                    date=values[6],
                    session=values[7],
                    reporting_time=values[8],
                    exam_time=values[9],
                    venue=null_if_dash(values[10]),
                    seat_location=null_if_dash(values[11]),
                    seat_no=null_if_dash(values[12]),
                )
            )
    return ExamSchedule(semester_id=semester_id, exams=exams)
