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
            await client.send("GET", "/vtop/login")
    assert route.called
