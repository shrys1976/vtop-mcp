"""Parse marks / internals HTML."""

from __future__ import annotations

import re

from bs4 import BeautifulSoup, Tag

from vtop_mcp.models.marks import CourseMarks, MarkComponent, MarksList
from vtop_mcp.parsers._common import COURSE_CODE_RE, cell_text


def _output_text(cell: Tag) -> str:
    out = cell.find("output")
    if out:
        return cell_text(out)
    return cell_text(cell)


def _parse_components(nested: Tag) -> list[MarkComponent]:
    components: list[MarkComponent] = []
    inner = nested.find("table", class_=re.compile(r"customTable-level1"))
    if inner is None:
        return components
    rows = inner.find_all("tr", class_=re.compile(r"tableContent-level1"))
    for row in rows:
        cells = row.find_all("td")
        if len(cells) < 2:
            continue
        values = [_output_text(c) for c in cells]
        if values[1].lower().startswith("mark title"):
            continue
        components.append(
            MarkComponent(
                name=values[1] if len(values) > 1 else "",
                max_score=values[2] if len(values) > 2 else None,
                weightage_percent=values[3] if len(values) > 3 else None,
                status=values[4] if len(values) > 4 else None,
                score=values[5] if len(values) > 5 else None,
                weightage_mark=values[6] if len(values) > 6 else None,
                remark=values[7] if len(values) > 7 else None,
            )
        )
    return components


def parse_marks(html: str, semester_id: str) -> MarksList:
    soup = BeautifulSoup(html, "html.parser")
    courses: list[CourseMarks] = []
    for tr in soup.find_all("tr"):
        row_class = " ".join(tr.get("class") or [])
        if "tableContent" not in row_class:
            continue
        cells = tr.find_all("td", recursive=False)
        if not cells:
            continue
        nested = cells[0].find("table", class_=re.compile(r"customTable"))
        if len(cells) == 1 and nested is not None:
            if courses:
                courses[-1].components = _parse_components(cells[0])
            continue
        values = [cell_text(c) for c in cells]
        if len(values) < 3:
            continue
        code = values[2] if len(values) > 2 else values[0]
        if not COURSE_CODE_RE.match(code or ""):
            continue
        courses.append(
            CourseMarks(
                code=code,
                title=values[3] if len(values) > 3 else "",
                class_number=values[1] if len(values) > 1 else None,
                course_type=values[4] if len(values) > 4 else None,
                course_system=values[5] if len(values) > 5 else None,
                faculty=values[6] if len(values) > 6 else None,
                slot=values[7] if len(values) > 7 else None,
                course_mode=values[8] if len(values) > 8 else None,
                components=[],
            )
        )
    return MarksList(semester_id=semester_id, courses=courses)
