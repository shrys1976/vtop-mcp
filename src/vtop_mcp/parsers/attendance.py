"""Parse attendance HTML tables."""

from __future__ import annotations

from vtop_mcp.models.attendance import AttendanceCourse, AttendanceList
from vtop_mcp.parsers._common import (
    cell_text,
    parse_int,
    parse_percent,
    split_class_detail,
    split_course_detail,
)
from bs4 import BeautifulSoup


def _faculty_and_school(text: str) -> tuple[str | None, str | None]:
    text = text.strip()
    if " - " not in text:
        return text or None, None
    name, school = text.split(" - ", 1)
    return name.strip() or None, school.strip() or None


def _parse_row(cells: list[str]) -> AttendanceCourse | None:
    if len(cells) < 8:
        return None
    code, title, course_type = split_course_detail(cells[2] if len(cells) > 2 else "")
    if not title:
        return None
    class_id, slot, venue = split_class_detail(cells[3] if len(cells) > 3 else "")
    faculty, school = _faculty_and_school(cells[4] if len(cells) > 4 else "")
    attended = parse_int(cells[5] if len(cells) > 5 else "")
    total = parse_int(cells[6] if len(cells) > 6 else "")
    percentage = parse_percent(cells[7] if len(cells) > 7 else "")
    debar = cells[8].strip() if len(cells) > 8 else None
    if debar == "-":
        debar = None
    return AttendanceCourse(
        code=code,
        title=title,
        course_type=course_type,
        class_group=cells[1] if len(cells) > 1 else None,
        class_id=class_id,
        slot=slot,
        venue=venue,
        faculty=faculty,
        school=school,
        attended=attended,
        total=total,
        percentage=percentage,
        debar_status=debar,
    )


def parse_attendance(html: str, semester_id: str) -> AttendanceList:
    soup = BeautifulSoup(html, "html.parser")
    courses: list[AttendanceCourse] = []
    for tr in soup.find_all("tr"):
        tds = tr.find_all("td")
        if len(tds) < 8:
            continue
        cells = [cell_text(td) for td in tds]
        if cells[0].lower().startswith("sl"):
            continue
        item = _parse_row(cells)
        if item:
            courses.append(item)
    return AttendanceList(semester_id=semester_id, courses=courses)
