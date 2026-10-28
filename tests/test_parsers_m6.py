"""Parser tests for M6 read tools."""

from __future__ import annotations

from pathlib import Path

from vtop_mcp.parsers.attendance import parse_attendance
from vtop_mcp.parsers.calendar import (
    parse_calendar_month,
    parse_default_calendar_semester,
)
from vtop_mcp.parsers.courses import parse_courses
from vtop_mcp.parsers.exams import parse_exam_schedule
from vtop_mcp.parsers.faculty import parse_faculty_detail, parse_faculty_search_results
from vtop_mcp.parsers.grades import parse_grades
from vtop_mcp.parsers.hod_dean import parse_hod_dean
from vtop_mcp.parsers.marks import parse_marks
from vtop_mcp.parsers.profile import parse_profile
from vtop_mcp.parsers.proctor import parse_proctor
from vtop_mcp.parsers.spotlight import parse_spotlight
from vtop_mcp.parsers.timetable import parse_timetable

FIXTURES = Path("tests/fixtures/responses")


def test_parse_attendance_fixture() -> None:
    html = (FIXTURES / "attendance.html").read_text()
    data = parse_attendance(html, "VL20262701")
    assert len(data.courses) == 1
    assert data.courses[0].attended == 30
    assert data.courses[0].total == 40
    assert data.courses[0].percentage == 80.0
    assert data.courses[0].code == "BCSE302L"


def test_parse_timetable_fixture() -> None:
    html = (FIXTURES / "timetable.html").read_text()
    data = parse_timetable(html, "VL20262701")
    assert len(data.slots) == 2
    codes = {slot.course_code for slot in data.slots}
    assert codes == {"BCSE355L", "BCSE302P"}
    assert any(slot.faculty == "Dr A" for slot in data.slots)


def test_parse_marks_fixture() -> None:
    html = (FIXTURES / "marks.html").read_text()
    data = parse_marks(html, "VL20262701")
    assert len(data.courses) == 1
    assert data.courses[0].code == "BSTS301P"
    assert len(data.courses[0].components) == 1
    assert data.courses[0].components[0].score == "80"


def test_parse_courses_fixture() -> None:
    html = (FIXTURES / "courses.html").read_text()
    data = parse_courses(html, "VL20262701")
    assert len(data.courses) == 1
    assert data.courses[0].code == "BCSE302L"
    assert data.courses[0].faculty == "Dr A"
    assert data.courses[0].venue == "SJT415"


def test_parse_exams_fixture() -> None:
    html = (FIXTURES / "exams.html").read_text()
    data = parse_exam_schedule(html, "VL20262701")
    assert len(data.exams) == 2
    assert data.exams[0].exam_name == "FAT"
    assert data.exams[1].seat_no == "53"


def test_parse_spotlight_fixture() -> None:
    html = (FIXTURES / "spotlight.html").read_text()
    data = parse_spotlight(html)
    assert len(data.items) == 2
    assert data.items[0].file_id == "820"
    assert data.items[1].url is not None


def test_parse_default_calendar_semester() -> None:
    html = (FIXTURES / "calendar_preview.html").read_text()
    assert parse_default_calendar_semester(html) == "VL20262701"


def test_parse_calendar_november_all_group() -> None:
    html = (FIXTURES / "calendar_november_all.html").read_text()
    data = parse_calendar_month(
        html,
        "01-NOV-2026",
        class_group_label="General (Semester)",
    )
    assert len(data) == 3
    holiday = next(e for e in data if e.date == "04-NOV-2026")
    assert holiday.title == "Holiday (Deepavali)"
    assert holiday.category == "Holiday (Deepavali)"


def test_parse_calendar_october_all_group() -> None:
    from vtop_mcp.parsers.calendar import calendar_month_header

    html = (FIXTURES / "calendar_october_all.html").read_text()
    assert calendar_month_header(html) == "OCTOBER 2026"
    data = parse_calendar_month(
        html,
        "01-OCT-2026",
        class_group_label="General (Semester)",
    )
    assert len(data) == 3
    assert not any(e.date == "10-OCT-2026" for e in data)
    exam = next(e for e in data if e.date == "01-OCT-2026")
    assert exam.category == "CAT - II"
    assert exam.remark == "Exam Day"
    assert exam.class_group == "General (Semester)"
    holiday = next(e for e in data if e.date == "02-OCT-2026")
    assert holiday.category == "Holiday"
    assert holiday.title == "Gandhi Jayanthi"
    pooja = next(e for e in data if e.date == "19-OCT-2026")
    assert pooja.category == "Holiday"
    assert pooja.title == "Ayutha Pooja"


def test_parse_profile_fixture() -> None:
    html = (FIXTURES / "profile.html").read_text()
    profile = parse_profile(html)
    assert profile.regno == "21BCE0000"
    assert profile.branch == "Computer Science and Engineering"
    assert profile.name == "Sample Student"


def test_parse_grades_fixture() -> None:
    html = (FIXTURES / "grades.html").read_text()
    data = parse_grades(html, "VL20252605")
    assert data.gpa == 8.0
    assert data.courses[0].grade == "A"


def test_parse_hod_dean_fixture() -> None:
    html = (FIXTURES / "hod_dean.html").read_text()
    data = parse_hod_dean(html)
    assert data.dean is not None
    assert data.dean.name == "Dr Dean"
    assert data.hod is not None


def test_parse_faculty_fixtures() -> None:
    search_html = (FIXTURES / "faculty_search.html").read_text()
    search = parse_faculty_search_results(search_html, "sample")
    assert len(search.matches) == 1
    assert search.matches[0].employee_id == "15776"
    detail_html = (FIXTURES / "faculty_detail.html").read_text()
    detail = parse_faculty_detail(detail_html, "15776")
    assert detail.email == "faculty@example.com"
    assert len(detail.open_hours) == 1


def test_parse_proctor_fixture() -> None:
    html = (FIXTURES / "proctor.html").read_text()
    data = parse_proctor(html)
    assert data.faculty_id == "11960"
    assert data.name == "Dr Proctor"
