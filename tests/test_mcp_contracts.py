"""MCP tool contract tests (mocked HTTP, synthetic fixtures)."""

from __future__ import annotations

from pathlib import Path

import httpx
import pytest
import respx
from cryptography.fernet import Fernet

from vtop_mcp.app_state import VtopApp
from vtop_mcp.config import Settings
from vtop_mcp.server import (
    get_academic_calendar,
    get_attendance,
    get_courses,
    get_exams,
    get_grades,
    get_hod_dean,
    get_marks,
    get_profile,
    get_proctor,
    get_spotlight,
    get_timetable,
    list_semesters,
    search_faculty,
    vtop_logout,
    vtop_session_status,
)
from vtop_mcp.vtop.constants import BASE_URL

FIXTURES = Path("tests/fixtures/responses")


@pytest.fixture
def app(tmp_path, monkeypatch) -> VtopApp:
    settings = Settings(
        session_file=tmp_path / "s.enc",
        session_key_env=Fernet.generate_key().decode(),
    )
    instance = VtopApp(settings)
    monkeypatch.setattr("vtop_mcp.server.app", instance)
    return instance


def _auth_bootstrap(fixture_name: str) -> None:
    html = (FIXTURES / fixture_name).read_text()
    respx.get(f"{BASE_URL}/vtop/open/page").mock(
        return_value=httpx.Response(200, text=html)
    )


def _mock_menu_post(path: str, fixture: str) -> None:
    respx.post(f"{BASE_URL}{path}").mock(
        return_value=httpx.Response(200, text=(FIXTURES / fixture).read_text())
    )


@pytest.mark.asyncio
@respx.mock
async def test_contract_session_and_logout(app) -> None:
    payload = await vtop_session_status()
    assert payload["ok"] is True
    assert "authenticated" in payload

    logout = await vtop_logout()
    assert logout["ok"] is True


@pytest.mark.asyncio
@respx.mock
async def test_contract_list_semesters(app) -> None:
    app.client.session_data.authenticated = True
    html = (FIXTURES / "semesters.html").read_text()
    _auth_bootstrap("semesters.html")
    respx.post(f"{BASE_URL}/vtop/academics/common/StudentAttendance").mock(
        return_value=httpx.Response(200, text=html)
    )
    payload = await list_semesters()
    assert payload["ok"] is True
    assert "semesters" in payload


@pytest.mark.asyncio
@respx.mock
async def test_contract_get_profile(app) -> None:
    app.client.session_data.authenticated = True
    _auth_bootstrap("semesters.html")
    profile_html = (FIXTURES / "profile.html").read_text()
    respx.post(f"{BASE_URL}/vtop/studentsRecord/StudentProfileAllView").mock(
        return_value=httpx.Response(200, text=profile_html)
    )
    payload = await get_profile()
    assert payload["ok"] is True
    assert payload.get("regno") == "21BCE0000"


@pytest.mark.asyncio
@respx.mock
@pytest.mark.parametrize(
    ("tool", "fixture", "shell_path", "data_path", "extra"),
    [
        (
            get_attendance,
            "attendance.html",
            "/vtop/academics/common/StudentAttendance",
            "/vtop/processViewStudentAttendance",
            {"semester_id": "VL20262701"},
        ),
        (
            get_timetable,
            "timetable.html",
            "/vtop/academics/common/StudentTimeTable",
            "/vtop/processViewTimeTable",
            {"semester_id": "VL20262701"},
        ),
        (
            get_marks,
            "marks.html",
            "/vtop/examinations/StudentMarkView",
            "/vtop/examinations/doStudentMarkView",
            {"semester_id": "VL20262701"},
        ),
        (
            get_courses,
            "courses.html",
            "/vtop/academics/common/StudentTimeTable",
            "/vtop/processViewTimeTable",
            {"semester_id": "VL20262701"},
        ),
    ],
)
async def test_contract_semester_tools(
    app, tool, fixture, shell_path, data_path, extra
) -> None:
    app.client.session_data.authenticated = True
    _auth_bootstrap("semesters.html")
    body = (FIXTURES / fixture).read_text()
    respx.post(f"{BASE_URL}{shell_path}").mock(
        return_value=httpx.Response(200, text=body)
    )
    respx.post(f"{BASE_URL}{data_path}").mock(
        return_value=httpx.Response(200, text=body)
    )
    payload = await tool(**extra)
    assert payload["ok"] is True


@pytest.mark.asyncio
@respx.mock
async def test_contract_get_exams(app) -> None:
    app.client.session_data.authenticated = True
    _auth_bootstrap("semesters.html")
    exams = (FIXTURES / "exams.html").read_text()
    respx.post(f"{BASE_URL}/vtop/examinations/StudExamSchedule").mock(
        return_value=httpx.Response(200, text=exams)
    )
    respx.post(f"{BASE_URL}/vtop/examinations/doSearchExamScheduleForStudent").mock(
        return_value=httpx.Response(200, text=exams)
    )
    payload = await get_exams(semester_id="VL20262701")
    assert payload["ok"] is True
    assert "exams" in payload


@pytest.mark.asyncio
@respx.mock
async def test_contract_get_academic_calendar(app) -> None:
    app.client.session_data.authenticated = True
    _auth_bootstrap("semesters.html")
    preview = (FIXTURES / "calendar_preview.html").read_text()
    semester_dates = (FIXTURES / "calendar_semester_dates.html").read_text()
    month = (FIXTURES / "calendar.html").read_text()
    respx.post(f"{BASE_URL}/vtop/academics/common/CalendarPreview").mock(
        return_value=httpx.Response(200, text=preview)
    )
    respx.post(f"{BASE_URL}/vtop/getDateForSemesterPreview").mock(
        return_value=httpx.Response(200, text=semester_dates)
    )
    list_semester = (FIXTURES / "calendar_list_semester.html").read_text()
    respx.post(f"{BASE_URL}/vtop/getListForSemester").mock(
        return_value=httpx.Response(200, text=list_semester)
    )
    respx.post(f"{BASE_URL}/vtop/processViewCalendar").mock(
        return_value=httpx.Response(200, text=month)
    )
    payload = await get_academic_calendar()
    assert payload["ok"] is True
    assert payload.get("semester_id") == "VL20262701"
    assert len(payload["events"]) >= 1
    assert payload.get("class_group_label") == "General (Semester)"


@pytest.mark.asyncio
@respx.mock
async def test_contract_get_spotlight(app) -> None:
    app.client.session_data.authenticated = True
    _auth_bootstrap("semesters.html")
    respx.post(f"{BASE_URL}/vtop/home").mock(
        return_value=httpx.Response(
            200, text=(FIXTURES / "spotlight.html").read_text()
        )
    )
    payload = await get_spotlight()
    assert payload["ok"] is True
    assert "items" in payload


@pytest.mark.asyncio
@respx.mock
async def test_contract_get_grades(app) -> None:
    app.client.session_data.authenticated = True
    _auth_bootstrap("semesters.html")
    grades = (FIXTURES / "grades.html").read_text()
    respx.post(
        f"{BASE_URL}/vtop/examinations/examGradeView/StudentGradeView"
    ).mock(return_value=httpx.Response(200, text=grades))
    respx.post(
        f"{BASE_URL}/vtop/examinations/examGradeView/doStudentGradeView"
    ).mock(return_value=httpx.Response(200, text=grades))
    payload = await get_grades(semester_id="VL20252605")
    assert payload["ok"] is True
    assert payload.get("gpa") == 8.0


@pytest.mark.asyncio
@respx.mock
async def test_contract_get_hod_dean(app) -> None:
    app.client.session_data.authenticated = True
    _auth_bootstrap("semesters.html")
    respx.post(f"{BASE_URL}/vtop/hrms/viewHodDeanDetails").mock(
        return_value=httpx.Response(200, text=(FIXTURES / "hod_dean.html").read_text())
    )
    payload = await get_hod_dean()
    assert payload["ok"] is True
    assert payload.get("dean") is not None


@pytest.mark.asyncio
@respx.mock
async def test_contract_get_proctor(app) -> None:
    app.client.session_data.authenticated = True
    _auth_bootstrap("semesters.html")
    respx.post(f"{BASE_URL}/vtop/proctor/viewProctorDetails").mock(
        return_value=httpx.Response(200, text=(FIXTURES / "proctor.html").read_text())
    )
    payload = await get_proctor()
    assert payload["ok"] is True
    assert payload.get("faculty_id") == "11960"


@pytest.mark.asyncio
@respx.mock
async def test_contract_search_faculty(app) -> None:
    app.client.session_data.authenticated = True
    _auth_bootstrap("semesters.html")
    search = (FIXTURES / "faculty_search.html").read_text()
    respx.post(f"{BASE_URL}/vtop/hrms/employeeSearchForStudent").mock(
        return_value=httpx.Response(200, text=search)
    )
    respx.post(f"{BASE_URL}/vtop/hrms/EmployeeSearchForStudent").mock(
        return_value=httpx.Response(200, text=search)
    )
    payload = await search_faculty(query="sample")
    assert payload["ok"] is True
    assert len(payload.get("matches", [])) == 1
