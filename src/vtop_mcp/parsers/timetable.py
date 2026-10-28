"""Parse timetable HTML."""

from __future__ import annotations

import re

from bs4 import BeautifulSoup, Tag

from vtop_mcp.models.timetable import Timetable, TimetableSlot
from vtop_mcp.parsers._common import cell_text, parse_timetable_cell
from vtop_mcp.parsers.course_list import course_metadata_map


def _time_ranges_from_header_rows(table: Tag) -> tuple[list[str], list[str]]:
    theory: list[str] = []
    lab: list[str] = []
    rows = table.find_all("tr")
    for tr in rows[:4]:
        cells = tr.find_all(["th", "td"])
        texts = [cell_text(c) for c in cells]
        joined = " ".join(texts).upper()
        if "THEORY" in joined:
            theory = texts[1:]
        elif "LAB" in joined and not lab:
            lab = texts[1:]
    return theory, lab


def _column_times(
    col_idx: int,
    theory: list[str],
    lab: list[str],
    *,
    is_lab_row: bool,
) -> tuple[str | None, str | None]:
    band = lab if is_lab_row and lab else theory
    if col_idx >= len(band):
        return None, None
    text = band[col_idx]
    if not text or text in ("-", "Lunch"):
        return None, None
    match = re.search(
        r"(\d{1,2}:\d{2}(?:\s*[AP]M)?)\s*[-–]\s*(\d{1,2}:\d{2}(?:\s*[AP]M)?)",
        text,
        re.I,
    )
    if match:
        return match.group(1).strip(), match.group(2).strip()
    return text, None


def parse_timetable(html: str, semester_id: str) -> Timetable:
    soup = BeautifulSoup(html, "html.parser")
    meta = course_metadata_map(html)
    table = soup.find("table", id="timeTableStyle")
    slots: list[TimetableSlot] = []
    if table is None:
        return Timetable(semester_id=semester_id, slots=slots)

    theory_times, lab_times = _time_ranges_from_header_rows(table)
    current_day: str | None = None

    days = ("MON", "TUE", "WED", "THU", "FRI", "SAT", "SUN")
    for tr in table.find_all("tr"):
        cells = tr.find_all(["td", "th"])
        if not cells:
            continue
        texts = [cell_text(c).upper() for c in cells]
        if texts[0] in days:
            current_day = texts[0]
        kind_idx = 0
        if texts[0] in days and len(texts) > 1:
            kind_idx = 1
        row_kind = texts[kind_idx] if kind_idx < len(texts) else ""
        if row_kind not in ("THEORY", "LAB"):
            continue
        is_lab = row_kind == "LAB"
        data_cells = cells[kind_idx + 1 :]
        for col_idx, cell in enumerate(data_cells):
            raw = cell_text(cell)
            if not raw or raw in ("-", "Lunch"):
                continue
            parsed = parse_timetable_cell(raw)
            if not parsed.get("course_code"):
                continue
            code = str(parsed["course_code"])
            info = meta.get(code)
            start, end = _column_times(
                col_idx,
                theory_times,
                lab_times,
                is_lab_row=is_lab,
            )
            slots.append(
                TimetableSlot(
                    day=current_day,
                    row_kind=row_kind,
                    start_time=start,
                    end_time=end,
                    course_code=code,
                    course_title=info.title if info else None,
                    course_type=parsed.get("course_type")
                    or (info.course_type if info else None),
                    venue=parsed.get("venue") or (info.venue if info else None),
                    faculty=info.faculty if info else None,
                    slot=parsed.get("slot") or (info.slot if info else None),
                )
            )

    return Timetable(semester_id=semester_id, slots=slots)
