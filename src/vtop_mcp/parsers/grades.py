"""Parse semester grade view HTML."""

from __future__ import annotations

import re

from bs4 import BeautifulSoup

from vtop_mcp.models.grades import GradeCourse, GradeList
from vtop_mcp.parsers._common import COURSE_CODE_RE, cell_text


def parse_grades(html: str, semester_id: str) -> GradeList:
    if "no records found" in html.lower():
        return GradeList(semester_id=semester_id, gpa=None, courses=[])

    soup = BeautifulSoup(html, "html.parser")
    gpa: float | None = None
    gpa_match = re.search(r"GPA\s*:\s*(\d+(?:\.\d+)?)", html, re.I)
    if gpa_match:
        gpa = float(gpa_match.group(1))

    exclude_gpa = "not included in gpa" in html.lower()
    courses: list[GradeCourse] = []
    for tr in soup.find_all("tr"):
        cells = tr.find_all("td")
        if len(cells) < 11:
            continue
        values = [cell_text(c) for c in cells]
        code = values[1]
        if not COURSE_CODE_RE.match(code or ""):
            continue
        row_style = tr.get("style") or ""
        counts = not exclude_gpa and "background-color: green" not in row_style.lower()
        courses.append(
            GradeCourse(
                code=code,
                title=values[2],
                course_type=values[3],
                credits_l=values[4],
                credits_p=values[5],
                credits_j=values[6],
                credits_c=values[7],
                grading_type=values[8],
                grand_total=values[9],
                grade=values[10],
                counts_toward_gpa=counts,
            )
        )
    return GradeList(semester_id=semester_id, gpa=gpa, courses=courses)
