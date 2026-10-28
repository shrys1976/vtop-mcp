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
    get_marks,
    get_profile,
    get_spotlight,
    get_timetable,
    list_semesters,
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
    assert payload.get("name") == "Sample Student"


@pytest.mark.asyncio
@respx.mock
@pytest.mark.parametrize(
    ("tool", "fixture", "path", "extra"),
    [
        (
            get_attendance,
            "attendance.html",
            "/vtop/processViewStudentAttendance",
            {"semester_id": "VL2025261"},
        ),
        (
            get_timetable,
            "timetable.html",
            "/vtop/processViewTimeTable",
            {"semester_id": "VL2025261"},
        ),
        (
            get_marks,
            "marks.html",
            "/vtop/examinations/doStudentMarkView",
            {"semester_id": "VL2025261"},
        ),
        (
            get_courses,
            "courses.html",
            "/vtop/getSlotIdForCoursePage",
            {"semester_id": "VL2025261"},
        ),
    ],
)
async def test_contract_semester_tools(app, tool, fixture, path, extra) -> None:
    app.client.session_data.authenticated = True
    _auth_bootstrap("semesters.html")
    body = (FIXTURES / fixture).read_text()
    respx.post(f"{BASE_URL}{path}").mock(return_value=httpx.Response(200, text=body))
    payload = await tool(**extra)
    assert payload["ok"] is True


@pytest.mark.asyncio
@respx.mock
async def test_contract_get_exams(app) -> None:
    app.client.session_data.authenticated = True
    _auth_bootstrap("semesters.html")
    respx.post(f"{BASE_URL}/vtop/examinations/doSearchExamScheduleForStudent").mock(
        return_value=httpx.Response(200, text=(FIXTURES / "exams.html").read_text())
    )
    payload = await get_exams(semester_id="VL2025261")
    assert payload["ok"] is True
    assert "exams" in payload


@pytest.mark.asyncio
@respx.mock
async def test_contract_get_academic_calendar(app) -> None:
    app.client.session_data.authenticated = True
    _auth_bootstrap("semesters.html")
    respx.post(f"{BASE_URL}/vtop/academics/common/CalendarPage").mock(
        return_value=httpx.Response(200, text=(FIXTURES / "calendar.html").read_text())
    )
    payload = await get_academic_calendar(semester_id="VL2025261")
    assert payload["ok"] is True
    assert "events" in payload


@pytest.mark.asyncio
@respx.mock
async def test_contract_get_spotlight(app) -> None:
    respx.get(f"{BASE_URL}/vtop/login").mock(
        return_value=httpx.Response(
            200, text=(FIXTURES / "spotlight.html").read_text()
        )
    )
    payload = await get_spotlight()
    assert payload["ok"] is True
    assert "items" in payload
