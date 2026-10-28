"""Parse academic calendar HTML."""

from __future__ import annotations

import re
from datetime import datetime

from bs4 import BeautifulSoup, Tag

from vtop_mcp.models.calendar import CalendarEvent
from vtop_mcp.parsers._common import cell_text

_MONTHS = {
    name: index
    for index, name in enumerate(
        [
            "JANUARY",
            "FEBRUARY",
            "MARCH",
            "APRIL",
            "MAY",
            "JUNE",
            "JULY",
            "AUGUST",
            "SEPTEMBER",
            "OCTOBER",
            "NOVEMBER",
            "DECEMBER",
        ],
        start=1,
    )
}


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


def _month_year_from_header(soup: BeautifulSoup, cal_date: str) -> tuple[int, int]:
    header = soup.find("h4")
    if header:
        parts = cell_text(header).split()
        if len(parts) >= 2:
            month_name = parts[0].upper()
            year = int(parts[1])
            month_num = _MONTHS.get(month_name)
            if month_num:
                return year, month_num
    return _parse_cal_date(cal_date)


def _parse_cal_date(cal_date: str) -> tuple[int, int]:
    dt = datetime.strptime(cal_date, "%d-%b-%Y")
    return dt.year, dt.month


def _is_green_event_span(span: Tag) -> bool:
    style = (span.get("style") or "").lower()
    return "color: green" in style or "color:green" in style


def _is_remark_span(span: Tag) -> bool:
    style = span.get("style") or ""
    return "#eb556e" in style.lower()


def _day_number_from_cell(td: Tag) -> int | None:
    for span in td.find_all("span", recursive=False):
        text = cell_text(span)
        if re.fullmatch(r"\d{1,2}", text):
            style = (span.get("style") or "").lower()
            if "font-weight: bold" in style or "font-weight:bold" in style:
                return int(text)
    for span in td.find_all("span"):
        text = cell_text(span)
        if re.fullmatch(r"\d{1,2}", text):
            return int(text)
    return None


def parse_calendar_month(html: str, cal_date: str) -> list[CalendarEvent]:
    soup = BeautifulSoup(html, "html.parser")
    year, month = _month_year_from_header(soup, cal_date)
    events: list[CalendarEvent] = []
    table = soup.select_one("table.calendar-table")
    if table is None:
        return events

    for td in table.find_all("td"):
        day_num = _day_number_from_cell(td)
        if day_num is None:
            continue
        date_str = (
            f"{day_num:02d}-"
            f"{datetime(year, month, day_num).strftime('%b').upper()}-"
            f"{year}"
        )
        spans = td.find_all("span", recursive=False)
        if not spans:
            spans = td.find_all("span")
        for index, span in enumerate(spans):
            if not _is_green_event_span(span):
                continue
            text = cell_text(span)
            if not text:
                continue
            category, _, class_group = text.rpartition(" - ")
            if not category:
                category = text
                class_group = ""
            remark: str | None = None
            if index + 1 < len(spans) and _is_remark_span(spans[index + 1]):
                remark_raw = cell_text(spans[index + 1]).strip()
                remark = remark_raw.strip("() ") if remark_raw else None
            title = remark or category or text
            events.append(
                CalendarEvent(
                    date=date_str,
                    title=title,
                    category=category or None,
                    class_group=class_group or None,
                    remark=remark,
                )
            )
    return events
