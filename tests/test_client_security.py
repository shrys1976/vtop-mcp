"""Transport security tests for VtopHttpClient."""

from __future__ import annotations

import httpx
import pytest
import respx

from vtop_mcp.config import Settings
from vtop_mcp.exceptions import HostNotAllowedError, UnexpectedRedirectError
from vtop_mcp.vtop.client import assert_allowed_url, resolve_path
from vtop_mcp.vtop.constants import BASE_URL
from vtop_mcp.vtop.client import VtopHttpClient


def test_resolve_path_rejects_foreign_host() -> None:
    with pytest.raises(HostNotAllowedError):
        resolve_path(BASE_URL, "https://evil.example/phish")


def test_assert_allowed_url_https_only() -> None:
    with pytest.raises(HostNotAllowedError):
        assert_allowed_url("http://vtop.vit.ac.in/vtop/login")


@pytest.mark.asyncio
@respx.mock
async def test_redirect_to_foreign_host_blocked(tmp_path) -> None:
    from cryptography.fernet import Fernet

    fernet_key = Fernet.generate_key().decode()
    settings = Settings(
        session_file=tmp_path / "s.enc",
        session_key_env=fernet_key,
    )
    route = respx.get(f"{BASE_URL}/vtop/login").mock(
        return_value=httpx.Response(
            302,
            headers={"Location": "https://evil.example/steal"},
        )
    )
    async with VtopHttpClient(settings) as client:
        with pytest.raises(UnexpectedRedirectError):
            await client.request_operation("auth.login_landing")
    assert route.called


@pytest.mark.asyncio
@respx.mock
async def test_redirect_cookie_is_sent_on_next_request(tmp_path) -> None:
    from cryptography.fernet import Fernet

    settings = Settings(
        session_file=tmp_path / "s.enc",
        session_key_env=Fernet.generate_key().decode(),
    )
    respx.get(f"{BASE_URL}/vtop/login").mock(
        return_value=httpx.Response(
            302,
            headers={
                "Location": "/vtop/init/page",
                "Set-Cookie": "JSESSIONID=abc123; Path=/vtop; Secure; HttpOnly",
            },
        )
    )

    seen: dict[str, str] = {}

    def _init(request: httpx.Request) -> httpx.Response:
        seen["cookie"] = request.headers.get("cookie", "")
        return httpx.Response(200, text="ok")

    respx.get(f"{BASE_URL}/vtop/init/page").mock(side_effect=_init)

    async with VtopHttpClient(settings) as client:
        await client.request_operation("auth.login_landing")
        assert client.has_cookie("JSESSIONID")

    assert "JSESSIONID=abc123" in seen["cookie"]


@pytest.mark.asyncio
@respx.mock
async def test_login_post_sends_referer(tmp_path) -> None:
    from cryptography.fernet import Fernet

    settings = Settings(
        session_file=tmp_path / "s.enc",
        session_key_env=Fernet.generate_key().decode(),
    )
    seen: dict[str, str] = {}

    def _login(request: httpx.Request) -> httpx.Response:
        seen["referer"] = request.headers.get("referer", "")
        seen["origin"] = request.headers.get("origin", "")
        return httpx.Response(200, text="ok")

    respx.post(f"{BASE_URL}/vtop/login").mock(side_effect=_login)
    async with VtopHttpClient(settings) as client:
        await client.request_operation(
            "auth.login_submit",
            {
                "_csrf": "t",
                "username": "USER",
                "password": "secret",
                "captchaStr": "ABCDEF",
            },
        )
    assert seen["referer"].endswith("/vtop/init/page")
    assert seen["origin"] == "https://vtop.vit.ac.in"
