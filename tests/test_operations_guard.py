"""Read-only operations allowlist tests."""

from __future__ import annotations

import httpx
import pytest
import respx
from cryptography.fernet import Fernet

from vtop_mcp.config import Settings
from vtop_mcp.exceptions import OperationNotAllowedError, UnexpectedRedirectError
from vtop_mcp.vtop.client import VtopHttpClient
from vtop_mcp.vtop.constants import BASE_URL, PATH_PROCESS_ATTENDANCE
from vtop_mcp.vtop.operations import OPERATIONS, get_operation, is_excluded_write_path


def test_unregistered_operation_rejected() -> None:
    with pytest.raises(OperationNotAllowedError, match="Unknown operation"):
        get_operation("read.not_registered")


@pytest.mark.asyncio
@respx.mock
async def test_unregistered_operation_no_http(tmp_path) -> None:
    settings = Settings(
        session_file=tmp_path / "s.enc",
        session_key_env=Fernet.generate_key().decode(),
    )
    route = respx.get(f"{BASE_URL}/vtop/login").mock(
        return_value=httpx.Response(200, text="ok")
    )
    async with VtopHttpClient(settings) as client:
        with pytest.raises(OperationNotAllowedError):
            await client.request_operation("auth.does_not_exist")
    assert not route.called


@pytest.mark.asyncio
@respx.mock
async def test_extra_body_param_rejected_before_http(tmp_path) -> None:
    settings = Settings(
        session_file=tmp_path / "s.enc",
        session_key_env=Fernet.generate_key().decode(),
    )
    route = respx.post(f"{BASE_URL}{PATH_PROCESS_ATTENDANCE}").mock(
        return_value=httpx.Response(200, text="ok")
    )
    async with VtopHttpClient(settings) as client:
        with pytest.raises(OperationNotAllowedError, match="Disallowed parameters"):
            await client.request_operation(
                "read.attendance",
                {
                    "authorizedID": "x",
                    "_csrf": "y",
                    "semesterSubId": "VL2025261",
                    "dropCourse": "true",
                },
            )
    assert not route.called


def test_write_like_post_paths_not_in_registry() -> None:
    write_like = (
        "/vtop/academics/processRegistration",
        "/vtop/studentsRecord/processRegistration",
        "/vtop/processPayment",
        "/vtop/resetPassword",
    )
    registered_paths = {spec.path for spec in OPERATIONS.values()}
    for path in write_like:
        assert path not in registered_paths
        assert is_excluded_write_path(path)


def test_write_like_operation_id_not_invokable(tmp_path) -> None:
    assert "read.course_registration" not in OPERATIONS
    with pytest.raises(OperationNotAllowedError):
        get_operation("read.course_registration")


@pytest.mark.asyncio
@respx.mock
async def test_redirect_off_host_via_allowlisted_op(tmp_path) -> None:
    settings = Settings(
        session_file=tmp_path / "s.enc",
        session_key_env=Fernet.generate_key().decode(),
    )
    respx.get(f"{BASE_URL}/vtop/login").mock(
        return_value=httpx.Response(
            302,
            headers={"Location": "https://evil.example/phish"},
        )
    )
    async with VtopHttpClient(settings) as client:
        with pytest.raises(UnexpectedRedirectError):
            await client.request_operation("auth.login_landing")


@pytest.mark.asyncio
@respx.mock
async def test_allowlisted_get_succeeds(tmp_path) -> None:
    settings = Settings(
        session_file=tmp_path / "s.enc",
        session_key_env=Fernet.generate_key().decode(),
    )
    respx.get(f"{BASE_URL}/vtop/login").mock(
        return_value=httpx.Response(200, text="<html></html>")
    )
    async with VtopHttpClient(settings) as client:
        resp = await client.request_operation("auth.login_landing")
    assert resp.status_code == 200


@pytest.mark.asyncio
@respx.mock
async def test_spotlight_path_param_validation(tmp_path) -> None:
    settings = Settings(
        session_file=tmp_path / "s.enc",
        session_key_env=Fernet.generate_key().decode(),
    )
    respx.get(f"{BASE_URL}/vtop/downloadSpotLightViewFile/795").mock(
        return_value=httpx.Response(200, content=b"pdf")
    )
    async with VtopHttpClient(settings) as client:
        resp = await client.request_operation(
            "read.spotlight_download",
            {"file_id": "795"},
        )
    assert resp.status_code == 200

    async with VtopHttpClient(settings) as client:
        with pytest.raises(OperationNotAllowedError, match="Invalid value"):
            await client.request_operation(
                "read.spotlight_download",
                {"file_id": "../etc/passwd"},
            )
