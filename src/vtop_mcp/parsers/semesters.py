"""Parse semester dropdown from VTOP HTML."""

from __future__ import annotations

import re

from bs4 import BeautifulSoup

from vtop_mcp.models.semesters import Semester, SemesterList
from vtop_mcp.vtop.constants import FIELD_SEMESTER_SUB_ID


def parse_semesters(html: str) -> SemesterList:
    soup = BeautifulSoup(html, "html.parser")
    select = soup.find("select", attrs={"name": FIELD_SEMESTER_SUB_ID})
    if select is None:
        select = soup.find("select", id=re.compile(r"sem", re.I))
    semesters: list[Semester] = []
    if select is None:
        return SemesterList(semesters=semesters)

    for option in select.find_all("option"):
        value = (option.get("value") or "").strip()
        label = option.get_text(strip=True)
        if not value or value in ("-1", "0", ""):
            continue
        active = bool(option.get("selected")) or "current" in label.lower()
        semesters.append(Semester(id=value, label=label, active=active))

    if semesters and not any(item.active for item in semesters):
        semesters[0].active = True

    return SemesterList(semesters=semesters)
