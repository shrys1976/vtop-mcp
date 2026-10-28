"""Parse faculty search HTML."""

from __future__ import annotations

import re

from bs4 import BeautifulSoup, Tag

from vtop_mcp.models.faculty import (
    FacultyDetail,
    FacultyOpenHour,
    FacultySearchMatch,
    FacultySearchResult,
)
from vtop_mcp.parsers._common import cell_text


def parse_faculty_search_results(html: str, query: str) -> FacultySearchResult:
    soup = BeautifulSoup(html, "html.parser")
    matches: list[FacultySearchMatch] = []
    for tr in soup.find_all("tr"):
        cells = tr.find_all("td")
        if len(cells) < 4:
            continue
        if "name of the faculty" in cell_text(cells[0]).lower():
            continue
        button = tr.find("button", id=True)
        if button is None:
            continue
        emp_id = str(button.get("id") or "").strip()
        if not emp_id.isdigit():
            match = re.search(r'getEmployeeIdNo\s*\(\s*"(\d+)"', tr.get("onclick") or "")
            if match:
                emp_id = match.group(1)
        if not emp_id:
            continue
        matches.append(
            FacultySearchMatch(
                employee_id=emp_id,
                name=cell_text(cells[0]) or None,
                designation=cell_text(cells[1]) or None,
                school=cell_text(cells[2]) or None,
            )
        )
    return FacultySearchResult(query=query, matches=matches)


def _label_table_pairs(root: Tag) -> dict[str, str]:
    pairs: dict[str, str] = {}
    for tr in root.find_all("tr"):
        cells = [c for c in tr.find_all("td") if not c.find("img")]
        if len(cells) < 2:
            continue
        key = cell_text(cells[0]).lower()
        val = cell_text(cells[1])
        if key and val:
            pairs[key] = val
    return pairs


def parse_faculty_detail(html: str, employee_id: str) -> FacultyDetail:
    soup = BeautifulSoup(html, "html.parser")
    pairs = _label_table_pairs(soup)
    open_hours: list[FacultyOpenHour] = []
    for tr in soup.find_all("tr"):
        cells = tr.find_all("td")
        if len(cells) < 2:
            continue
        day = cell_text(cells[0])
        if day.upper() in (
            "MONDAY",
            "TUESDAY",
            "WEDNESDAY",
            "THURSDAY",
            "FRIDAY",
            "SATURDAY",
            "SUNDAY",
        ):
            timings = cell_text(cells[1])
            open_hours.append(FacultyOpenHour(day=day, timings=timings or None))

    return FacultyDetail(
        employee_id=employee_id,
        name=pairs.get("name of the faculty"),
        designation=pairs.get("designation"),
        department=pairs.get("name of department"),
        school=pairs.get("school / centre name"),
        email=pairs.get("e-mail id"),
        cabin=pairs.get("cabin number"),
        open_hours=open_hours,
    )
