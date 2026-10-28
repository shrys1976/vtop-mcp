"""Parser tests for M6 read tools."""

from __future__ import annotations

from pathlib import Path

from vtop_mcp.parsers.attendance import parse_attendance
from vtop_mcp.parsers.calendar import parse_academic_calendar
from vtop_mcp.parsers.courses import parse_courses
from vtop_mcp.parsers.exams import parse_exam_schedule
from vtop_mcp.parsers.marks import parse_marks
from vtop_mcp.parsers.spotlight import parse_spotlight
from vtop_mcp.parsers.timetable import parse_timetable

FIXTURES = Path("tests/fixtures/responses")


def test_parse_attendance_fixture() -> None:
    html = (FIXTURES / "attendance.html").read_text()
    data = parse_attendance(html, "VL2025261")
    assert len(data.courses) == 2
    assert data.courses[0].percentage == 80.0


def test_parse_timetable_fixture() -> None:
    html = (FIXTURES / "timetable.html").read_text()
    data = parse_timetable(html, "VL2025261")
    assert len(data.slots) == 1
    assert data.slots[0].course_code == "CSE1001"


def test_parse_marks_fixture() -> None:
    html = (FIXTURES / "marks.html").read_text()
    data = parse_marks(html, "VL2025261")
    assert len(data.courses) == 1
    assert len(data.courses[0].components) >= 1


def test_parse_courses_fixture() -> None:
    html = (FIXTURES / "courses.html").read_text()
    data = parse_courses(html, "VL2025261")
    assert len(data.courses) == 1
    assert data.courses[0].faculty == "Dr A"


def test_parse_exams_fixture() -> None:
    html = (FIXTURES / "exams.html").read_text()
    data = parse_exam_schedule(html, "VL2025261")
    assert len(data.exams) == 1
    assert data.exams[0].seat_no == "12A"


def test_parse_spotlight_fixture() -> None:
    html = (FIXTURES / "spotlight.html").read_text()
    data = parse_spotlight(html)
    assert len(data.items) == 2
    assert data.items[0].file_id == "795"


def test_parse_calendar_fixture() -> None:
    html = (FIXTURES / "calendar.html").read_text()
    data = parse_academic_calendar(html, "VL2025261")
    assert len(data.events) == 2
