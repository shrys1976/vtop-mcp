"""MCP tool handler tests (no stdio)."""

from __future__ import annotations

import httpx
import pytest
import respx
from cryptography.fernet import Fernet

from vtop_mcp.app_state import VtopApp
from vtop_mcp.config import Settings
from vtop_mcp.server import list_semesters, vtop_logout, vtop_session_status
from vtop_mcp.vtop.constants import BASE_URL


@pytest.fixture
def vtop_app(tmp_path, monkeypatch) -> VtopApp:
    settings = Settings(
        session_file=tmp_path / "s.enc",
        session_key_env=Fernet.generate_key().decode(),
    )
    instance = VtopApp(settings)
    monkeypatch.setattr("vtop_mcp.server.app", instance)
    return instance


@pytest.mark.asyncio
async def test_session_status_not_authenticated(vtop_app) -> None:
    payload = await vtop_session_status()
    assert payload["ok"] is True
    assert payload["authenticated"] is False


@pytest.mark.asyncio
@respx.mock
async def test_list_semesters_not_authenticated(vtop_app) -> None:
    payload = await list_semesters()
    assert payload["ok"] is False
    assert payload["error_code"] == "not_authenticated"


@pytest.mark.asyncio
async def test_logout_clears_session(vtop_app) -> None:
    vtop_app.client.session_data.authenticated = True
    payload = await vtop_logout()
    assert payload["ok"] is True
    assert vtop_app.client.session_data.authenticated is False


@pytest.mark.asyncio
@respx.mock
async def test_list_semesters_happy_path(vtop_app) -> None:
    vtop_app.client.session_data.authenticated = True
    vtop_app.client.session_data.authorized_id = "SYNTH_AUTH_ID"

    fixture = open("tests/fixtures/responses/semesters.html").read()
    respx.get(f"{BASE_URL}/vtop/open/page").mock(
        return_value=httpx.Response(200, text=fixture)
    )
    respx.post(f"{BASE_URL}/vtop/academics/common/StudentAttendance").mock(
        return_value=httpx.Response(200, text=fixture)
    )

    payload = await list_semesters()
    assert payload["ok"] is True
    assert len(payload["semesters"]) == 2
