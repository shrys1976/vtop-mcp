"""Parse academic calendar HTML."""

from __future__ import annotations

import re
from datetime import datetime
from html import unescape

from bs4 import BeautifulSoup, Tag

from vtop_mcp.models.calendar import CalendarEvent
from vtop_mcp.parsers._common import cell_text

_MONTH_HEADING_RE = re.compile(r"^[A-Z]+ \d{4}$")
_ONCLICK_CAL_DATE_RE = re.compile(
    r"processViewCalendar\s*\(\s*"
    r"(?:'|&#39;|&apos;|\")"
    r"(\d{2}-[A-Za-z]{3}-\d{4})"
    r"(?:'|&#39;|&apos;|\")"
    r"\s*\)",
    re.I,
)
_BTN_MONTH_LABEL_RE = re.compile(r"^[A-Z]{3}-\d{4}$", re.I)

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


def parse_default_calendar_semester(html: str) -> str | None:
    soup = BeautifulSoup(html, "html.parser")
    select = soup.find("select", id="semesterSubId")
    if select is None:
        select = soup.find("select", attrs={"name": "semesterSubId"})
    if select is None:
        return None
    for option in select.find_all("option"):
        value = (option.get("value") or "").strip()
        if value and value not in ("", "-1", "0"):
            return value
    return None


def normalize_cal_date(cal_date: str) -> str:
    match = re.match(r"(\d{2})-([A-Za-z]{3})-(\d{4})", cal_date.strip())
    if not match:
        return cal_date.strip().upper()
    return f"{match.group(1)}-{match.group(2).upper()}-{match.group(3)}"


def _dates_from_month_button(anchor: Tag) -> str | None:
    onclick = anchor.get("onclick") or ""
    match = _ONCLICK_CAL_DATE_RE.search(onclick)
    if match:
        return normalize_cal_date(match.group(1))
    label = cell_text(anchor).upper()
    if _BTN_MONTH_LABEL_RE.fullmatch(label):
        return normalize_cal_date(f"01-{label}")
    return None


def _dates_from_list_semester_dom(soup: BeautifulSoup) -> list[str]:
    container = soup.find(id="getListForSemester")
    if container is None:
        return []
    dates: list[str] = []
    anchors = container.select("a.btn")
    if not anchors:
        anchors = container.find_all("a")
    for anchor in anchors:
        cal_date = _dates_from_month_button(anchor)
        if cal_date:
            dates.append(cal_date)
    return dates


def extract_calendar_month_dates(html: str) -> list[str]:
    soup = BeautifulSoup(html, "html.parser")
    dates = _dates_from_list_semester_dom(soup)
    if dates:
        return list(dict.fromkeys(dates))

    decoded = unescape(html)
    raw = _ONCLICK_CAL_DATE_RE.findall(decoded)
    return list(dict.fromkeys(normalize_cal_date(item) for item in raw))


def _calendar_month_heading(soup: BeautifulSoup) -> Tag | None:
    for header in soup.find_all("h4"):
        text = cell_text(header)
        if _MONTH_HEADING_RE.fullmatch(text):
            return header
    return None


def calendar_month_header(html: str) -> str:
    soup = BeautifulSoup(html, "html.parser")
    header = _calendar_month_heading(soup)
    return cell_text(header) if header else ""


def _month_year_from_header(soup: BeautifulSoup, cal_date: str) -> tuple[int, int]:
    header = _calendar_month_heading(soup)
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
    style = span.get("style") or ""
    if "color: green" in style:
        return True
    compact = re.sub(r"\s+", "", style.lower())
    return "color:green" in compact


def _is_remark_span(span: Tag) -> bool:
    style = span.get("style") or ""
    return "#eb556e" in style.lower()


def _is_paren_remark(text: str) -> bool:
    stripped = text.strip()
    return stripped.startswith("(") and stripped.endswith(")")


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


def _split_combined_event_text(text: str) -> tuple[str, str]:
    category, _, class_group = text.rpartition(" - ")
    if not category:
        return text, ""
    return category, class_group


def parse_calendar_month(
    html: str,
    cal_date: str,
    *,
    class_group_label: str | None = None,
) -> list[CalendarEvent]:
    soup = BeautifulSoup(html, "html.parser")
    year, month = _month_year_from_header(soup, cal_date)
    events: list[CalendarEvent] = []
    table = soup.select_one("table.calendar-table")
    if table is None:
        for candidate in soup.find_all("table"):
            classes = candidate.get("class") or []
            if any("calendar-table" in str(item) for item in classes):
                table = candidate
                break
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
            text = cell_text(span)
            if not text:
                continue
            if _is_green_event_span(span):
                if class_group_label:
                    category = text
                    class_group = class_group_label
                else:
                    category, class_group = _split_combined_event_text(text)
                remark: str | None = None
                for follow in spans[index + 1 :]:
                    if _is_green_event_span(follow):
                        break
                    if _is_remark_span(follow):
                        remark_raw = cell_text(follow).strip()
                        if remark_raw and _is_paren_remark(remark_raw):
                            remark = remark_raw.strip("() ")
                        break
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
                continue
            if _is_remark_span(span) and not _is_paren_remark(text):
                events.append(
                    CalendarEvent(
                        date=date_str,
                        title=text,
                        category=text,
                        class_group=class_group_label,
                        remark=None,
                    )
                )
    return events
