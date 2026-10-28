"""Parse academic calendar HTML."""

from __future__ import annotations

import re
from datetime import datetime

from bs4 import BeautifulSoup, Tag

from vtop_mcp.models.calendar import CalendarEvent
from vtop_mcp.parsers._common import cell_text


def extract_calendar_month_dates(html: str) -> list[str]:
    return list(
        dict.fromkeys(
            re.findall(
                r"processViewCalendar\s*\(\s*['\"](\d{2}-[A-Z]{3}-\d{4})['\"]",
                html,
                re.I,
            )
        )
    )


def _parse_cal_date(cal_date: str) -> tuple[int, int]:
    dt = datetime.strptime(cal_date, "%d-%b-%Y")
    return dt.year, dt.month


def _event_spans(td: Tag) -> list[tuple[str, str | None]]:
    spans = [s for s in td.find_all("span") if cell_text(s)]
    events: list[tuple[str, str | None]] = []
    i = 0
    while i < len(spans):
        text = cell_text(spans[i])
        if re.fullmatch(r"\d{1,2}", text):
            i += 1
            continue
        category = text
        subtitle = None
        if i + 1 < len(spans):
            next_text = cell_text(spans[i + 1])
            if next_text.startswith("("):
                subtitle = next_text.strip("() ")
                i += 2
                events.append((category, subtitle))
                continue
        events.append((category, subtitle))
        i += 1
    return events


def parse_calendar_month(html: str, cal_date: str) -> list[CalendarEvent]:
    year, month = _parse_cal_date(cal_date)
    soup = BeautifulSoup(html, "html.parser")
    events: list[CalendarEvent] = []
    seen: set[tuple[str, str, str | None]] = set()
    for td in soup.find_all("td"):
        spans = td.find_all("span")
        day_num: int | None = None
        for span in spans:
            text = cell_text(span)
            if re.fullmatch(r"\d{1,2}", text):
                day_num = int(text)
                break
        if day_num is None:
            continue
        date_str = (
            f"{day_num:02d}-"
            f"{datetime(year, month, day_num).strftime('%b').upper()}-"
            f"{year}"
        )
        for category, subtitle in _event_spans(td):
            key = (date_str, category, subtitle)
            if key in seen:
                continue
            seen.add(key)
            cat = category.split(" - ", 1)[0].strip() if category else None
            events.append(
                CalendarEvent(
                    date=date_str,
                    title=subtitle or category,
                    category=cat,
                )
            )
    return events
