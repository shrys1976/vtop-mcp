"""Shared parsing helpers."""

from __future__ import annotations

import re

from bs4 import BeautifulSoup, NavigableString, Tag

COURSE_CODE_RE = re.compile(r"^[A-Z]{2,5}[0-9]{3,4}[A-Z]?$")
COURSE_CODE_SEARCH = re.compile(r"\b([A-Z]{2,5}[0-9]{3,4}[A-Z]?)\b")


def cell_text(cell: Tag | None) -> str:
    if cell is None:
        return ""
    return cell.get_text(" ", strip=True)


def parse_int(text: str) -> int | None:
    text = text.strip()
    if not text or text == "-":
        return None
    match = re.search(r"^\d+$", text)
    return int(match.group(0)) if match else None


def parse_percent(text: str) -> float | None:
    match = re.search(r"(\d+(?:\.\d+)?)\s*%", text)
    return float(match.group(1)) if match else None


def null_if_dash(value: str | None) -> str | None:
    if value is None:
        return None
    stripped = value.strip()
    if not stripped or stripped == "-":
        return None
    return stripped


def paragraph_parts(cell: Tag) -> list[str]:
    parts: list[str] = []
    for p in cell.find_all("p"):
        text = p.get_text(" ", strip=True)
        if text:
            parts.append(text)
    if not parts:
        text = cell.get_text(" ", strip=True)
        if text:
            parts.append(text)
    return parts


def split_course_detail(text: str) -> tuple[str | None, str, str | None]:
    """BCSE302L - Database Systems - Theory Only."""
    text = text.strip()
    if not text:
        return None, "", None
    parts = [p.strip() for p in text.split(" - ") if p.strip()]
    if not parts:
        return None, "", None
    code = parts[0] if COURSE_CODE_RE.match(parts[0]) else None
    if code and len(parts) >= 2:
        title = parts[1]
        course_type = parts[2] if len(parts) > 2 else None
        return code, title, course_type
    return None, text, None


def split_class_detail(text: str) -> tuple[str | None, str | None, str | None]:
    """VL2026270102771 - D2+TD2 - SJT415."""
    parts = [p.strip() for p in text.split(" - ") if p.strip()]
    if len(parts) >= 3:
        return parts[0], parts[1], parts[2]
    if len(parts) == 2:
        return parts[0], parts[1], None
    if len(parts) == 1:
        return parts[0], None, None
    return None, None, None


def parse_timetable_cell(text: str) -> dict[str, str | None]:
    text = text.strip()
    if not text or text in ("-", "Lunch"):
        return {}
    segments = [s.strip() for s in text.split("-") if s.strip()]
    if len(segments) < 2:
        return {"slot": text}
    code_idx = next(
        (i for i, seg in enumerate(segments) if COURSE_CODE_RE.match(seg)),
        None,
    )
    if code_idx is None:
        return {"slot": text}
    slot = "-".join(segments[:code_idx]) if code_idx > 0 else segments[0]
    code = segments[code_idx]
    course_type = segments[code_idx + 1] if len(segments) > code_idx + 1 else None
    venue = segments[code_idx + 2] if len(segments) > code_idx + 2 else None
    if venue and venue.upper() == "ALL":
        venue = None
    return {
        "slot": slot or None,
        "course_code": code,
        "course_type": course_type,
        "venue": venue,
    }


def find_course_list_table(soup: BeautifulSoup) -> Tag | None:
    grid = soup.find("table", id="timeTableStyle")
    tables = soup.find_all("table")
    if not tables:
        return None
    if grid and tables[0] is not grid:
        return tables[0]
    for table in tables:
        header = " ".join(cell_text(th) for th in table.find_all("th")).lower()
        if "faculty" in header and "course" in header:
            return table
    return tables[0] if tables else None


def accordion_value(soup: BeautifulSoup, section_keyword: str, label: str) -> str | None:
    in_section = False
    label_lower = label.lower()
    for row in soup.find_all("tr"):
        cells = row.find_all(["td", "th"])
        if not cells:
            continue
        row_text = " ".join(cell_text(c) for c in cells).upper()
        if section_keyword.upper() in row_text and len(cells) == 1:
            in_section = True
            continue
        if not in_section:
            continue
        if len(cells) >= 2:
            key = cell_text(cells[0]).lower()
            if label_lower in key:
                return cell_text(cells[1]) or None
    return None
