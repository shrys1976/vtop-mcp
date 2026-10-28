"""Parse the timetable page course list table."""

from __future__ import annotations

import re

from bs4 import BeautifulSoup, Tag

from vtop_mcp.models.courses import Course
from vtop_mcp.parsers._common import (
    COURSE_CODE_RE,
    cell_text,
    find_course_list_table,
    paragraph_parts,
    split_course_detail,
)


def _parse_course_cell(cell: Tag) -> tuple[str | None, str, str | None]:
    parts = paragraph_parts(cell)
    if not parts:
        return None, "", None
    code, title, _ = split_course_detail(parts[0])
    course_type = None
    for extra in parts[1:]:
        cleaned = extra.strip("() ")
        if cleaned:
            course_type = cleaned
    if not title and parts[0]:
        code, title, course_type = split_course_detail(parts[0])
    return code, title or parts[0], course_type


def _parse_slot_venue(cell: Tag) -> tuple[str | None, str | None]:
    parts = paragraph_parts(cell)
    if not parts:
        return None, None
    slot_part = parts[0].rstrip(" -").strip()
    venue = parts[1].strip() if len(parts) > 1 else None
    if not venue and len(parts) == 1 and " - " in parts[0]:
        left, right = parts[0].split(" - ", 1)
        slot_part = left.strip()
        venue = right.strip() or None
    return slot_part or None, venue


def _parse_faculty_cell(cell: Tag) -> tuple[str | None, str | None]:
    parts = paragraph_parts(cell)
    if not parts:
        return None, None
    name = parts[0].rstrip(" -").strip() or None
    school = parts[1].strip() if len(parts) > 1 else None
    return name, school


def parse_course_list(html: str) -> list[Course]:
    soup = BeautifulSoup(html, "html.parser")
    table = find_course_list_table(soup)
    if table is None:
        return []

    header_cells = [
        cell_text(th).lower() for th in table.find_all("th")
    ]
    if not header_cells:
        first_row = table.find("tr")
        if first_row:
            header_cells = [cell_text(td).lower() for td in first_row.find_all("td")]

    def col_index(*names: str) -> int | None:
        for name in names:
            for i, header in enumerate(header_cells):
                if name in header:
                    return i
        return None

    idx_course = col_index("course")
    idx_class = col_index("class id")
    idx_slot = col_index("slot", "venue")
    idx_faculty = col_index("faculty")

    courses: list[Course] = []
    for tr in table.find_all("tr"):
        tds = tr.find_all("td")
        if len(tds) < 3:
            continue
        if idx_course is not None and idx_course < len(tds):
            code, title, course_type = _parse_course_cell(tds[idx_course])
        else:
            code, title, course_type = _parse_course_cell(tds[2])
        if not code or not COURSE_CODE_RE.match(code):
            continue
        class_id = (
            cell_text(tds[idx_class])
            if idx_class is not None and idx_class < len(tds)
            else None
        )
        slot_cell = tds[idx_slot] if idx_slot is not None and idx_slot < len(tds) else None
        faculty_cell = (
            tds[idx_faculty]
            if idx_faculty is not None and idx_faculty < len(tds)
            else None
        )
        slot, venue = _parse_slot_venue(slot_cell) if slot_cell else (None, None)
        faculty, school = (
            _parse_faculty_cell(faculty_cell) if faculty_cell else (None, None)
        )
        courses.append(
            Course(
                code=code,
                title=title,
                slot=slot,
                venue=venue,
                faculty=faculty,
                school=school,
                course_type=course_type,
                class_id=class_id or None,
            )
        )
    return courses


def course_metadata_map(html: str) -> dict[str, Course]:
    return {c.code: c for c in parse_course_list(html) if c.code}
