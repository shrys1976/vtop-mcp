"""Login flow tests with mocked HTTP."""

from __future__ import annotations

import httpx
import pytest
import respx
from cryptography.fernet import Fernet

from vtop_mcp.config import Settings
from vtop_mcp.exceptions import RecaptchaOnlyError
from vtop_mcp.vtop.auth.login import LoginFlow
from vtop_mcp.vtop.client import VtopHttpClient
from vtop_mcp.vtop.constants import BASE_URL, CAPTCHA_TYPE_GOOGLE


def _landing_html(csrf: str = "csrf-1") -> str:
    return f'<form id="stdForm"><input name="_csrf" value="{csrf}"/></form>'


def _init_html(csrf: str = "csrf-2", captcha_type: int = 1, captcha_b64: str = "abc") -> str:
    recaptcha = ""
    captcha_block = (
        f'<div id="captchaBlock"><img src="data:image/jpeg;base64,{captcha_b64}"/></div>'
        f'<input name="captchaStr" id="captchaStr"/>'
    )
    if captcha_type == CAPTCHA_TYPE_GOOGLE:
        captcha_block = '<div class="g-recaptcha"></div>'
    return (
        f'<form id="vtopLoginForm"><input name="_csrf" value="{csrf}"/>'
        f"{captcha_block}</form>"
        f"<script>var captchaType={captcha_type};</script>"
    )


@pytest.mark.asyncio
@respx.mock
async def test_login_recaptcha_retry_then_raises(tmp_path, monkeypatch) -> None:
    settings = Settings(
        session_file=tmp_path / "s.enc",
        session_key_env=Fernet.generate_key().decode(),
        max_recaptcha_refreshes=2,
        regno="21BCE0000",
        password="secret",
    )
    respx.get(f"{BASE_URL}/vtop/login").mock(
        return_value=httpx.Response(200, text=_landing_html())
    )
    respx.post(f"{BASE_URL}/vtop/prelogin/setup").mock(
        return_value=httpx.Response(302, headers={"Location": "/vtop/init/page"})
    )
    respx.get(f"{BASE_URL}/vtop/init/page").mock(
        return_value=httpx.Response(200, text=_init_html(captcha_type=CAPTCHA_TYPE_GOOGLE))
    )

    async with VtopHttpClient(settings) as client:
        flow = LoginFlow(client, settings)
        with pytest.raises(RecaptchaOnlyError):
            await flow.login()


@pytest.mark.asyncio
@respx.mock
async def test_login_recaptcha_refresh_until_text_captcha(tmp_path, monkeypatch) -> None:
    settings = Settings(
        session_file=tmp_path / "s.enc",
        session_key_env=Fernet.generate_key().decode(),
        max_recaptcha_refreshes=5,
        regno="21BCE0000",
        password="secret",
    )
    respx.get(f"{BASE_URL}/vtop/login").mock(
        return_value=httpx.Response(200, text=_landing_html())
    )
    respx.post(f"{BASE_URL}/vtop/prelogin/setup").mock(
        return_value=httpx.Response(302, headers={"Location": "/vtop/init/page"})
    )
    init_calls = {"n": 0}

    def _init_response(_request: httpx.Request) -> httpx.Response:
        init_calls["n"] += 1
        captcha_type = CAPTCHA_TYPE_GOOGLE if init_calls["n"] < 3 else 1
        return httpx.Response(200, text=_init_html(captcha_type=captcha_type))

    respx.get(f"{BASE_URL}/vtop/init/page").mock(side_effect=_init_response)
    respx.post(f"{BASE_URL}/vtop/login").mock(
        return_value=httpx.Response(
            200,
            text='<form id="otpVerificationForm"><input name="_csrf" value="otp-csrf"/></form>',
        )
    )
    monkeypatch.setattr(
        "vtop_mcp.vtop.auth.login.solve_captcha_base64",
        lambda _b64: "ABCDEF",
    )

    async with VtopHttpClient(settings) as client:
        flow = LoginFlow(client, settings)
        result = await flow.login()

    assert result.status == "otp_required"
    assert init_calls["n"] >= 3


@pytest.mark.asyncio
@respx.mock
async def test_login_otp_required(tmp_path, monkeypatch) -> None:
    settings = Settings(
        session_file=tmp_path / "s.enc",
        session_key_env=Fernet.generate_key().decode(),
        regno="21BCE0000",
        password="secret",
    )
    respx.get(f"{BASE_URL}/vtop/login").mock(
        return_value=httpx.Response(200, text=_landing_html())
    )
    respx.post(f"{BASE_URL}/vtop/prelogin/setup").mock(
        return_value=httpx.Response(302, headers={"Location": "/vtop/init/page"})
    )
    respx.get(f"{BASE_URL}/vtop/init/page").mock(
        return_value=httpx.Response(200, text=_init_html())
    )
    respx.post(f"{BASE_URL}/vtop/login").mock(
        return_value=httpx.Response(
            200,
            text='<form id="otpVerificationForm"><input name="_csrf" value="otp-csrf"/></form>',
        )
    )
    monkeypatch.setattr(
        "vtop_mcp.vtop.auth.login.solve_captcha_base64",
        lambda _b64: "ABCDEF",
    )

    async with VtopHttpClient(settings) as client:
        flow = LoginFlow(client, settings)
        result = await flow.login()
    assert result.status == "otp_required"
    assert flow.otp_pending


@pytest.mark.asyncio
@respx.mock
async def test_manual_captcha_login(tmp_path, monkeypatch) -> None:
    settings = Settings(
        session_file=tmp_path / "s.enc",
        session_key_env=Fernet.generate_key().decode(),
        regno="21BCE0000",
        password="secret",
    )
    respx.get(f"{BASE_URL}/vtop/login").mock(
        return_value=httpx.Response(200, text=_landing_html())
    )
    respx.post(f"{BASE_URL}/vtop/prelogin/setup").mock(
        return_value=httpx.Response(302, headers={"Location": "/vtop/init/page"})
    )
    respx.get(f"{BASE_URL}/vtop/init/page").mock(
        return_value=httpx.Response(200, text=_init_html())
    )
    respx.post(f"{BASE_URL}/vtop/login").mock(
        return_value=httpx.Response(
            200,
            text='<form id="otpVerificationForm"><input name="_csrf" value="otp-csrf"/></form>',
        )
    )

    async with VtopHttpClient(settings) as client:
        flow = LoginFlow(client, settings)
        challenge = await flow.fetch_login_captcha()
        assert challenge.captcha_image_base64 == "abc"
        result = await flow.login_with_captcha("ABCDEF")

    assert result.status == "otp_required"


def _dashboard_html() -> str:
    return (
        "<html><body><form>"
        '<input type="hidden" id="authorizedID" value="AUTH123"/>'
        '<input type="hidden" name="_csrf" value="dash-csrf"/>'
        "</form></body></html>"
    )


@pytest.mark.asyncio
@respx.mock
async def test_login_requires_dashboard_tokens(tmp_path, monkeypatch) -> None:
    settings = Settings(
        session_file=tmp_path / "s.enc",
        session_key_env=Fernet.generate_key().decode(),
        regno="21BCE0000",
        password="secret",
    )
    respx.get(f"{BASE_URL}/vtop/login").mock(
        return_value=httpx.Response(200, text=_landing_html())
    )
    respx.post(f"{BASE_URL}/vtop/prelogin/setup").mock(
        return_value=httpx.Response(302, headers={"Location": "/vtop/init/page"})
    )
    respx.get(f"{BASE_URL}/vtop/init/page").mock(
        return_value=httpx.Response(200, text=_init_html())
    )
    respx.post(f"{BASE_URL}/vtop/login").mock(
        return_value=httpx.Response(200, text="<html><body>Welcome</body></html>")
    )
    respx.get(f"{BASE_URL}/vtop/open/page").mock(
        return_value=httpx.Response(200, text=_dashboard_html())
    )
    monkeypatch.setattr(
        "vtop_mcp.vtop.auth.login.solve_captcha_base64",
        lambda _b64, manual=None: "ABCDEF",
    )

    async with VtopHttpClient(settings) as client:
        flow = LoginFlow(client, settings)
        result = await flow.login()
        assert result.status == "authenticated"
        assert client.session_data.authorized_id == "AUTH123"
        assert client.session_data.authenticated is True


@pytest.mark.asyncio
@respx.mock
async def test_login_rejects_dashboard_without_tokens(tmp_path, monkeypatch) -> None:
    settings = Settings(
        session_file=tmp_path / "s.enc",
        session_key_env=Fernet.generate_key().decode(),
        regno="21BCE0000",
        password="secret",
    )
    respx.get(f"{BASE_URL}/vtop/login").mock(
        return_value=httpx.Response(200, text=_landing_html())
    )
    respx.post(f"{BASE_URL}/vtop/prelogin/setup").mock(
        return_value=httpx.Response(302, headers={"Location": "/vtop/init/page"})
    )
    respx.get(f"{BASE_URL}/vtop/init/page").mock(
        return_value=httpx.Response(200, text=_init_html())
    )
    respx.post(f"{BASE_URL}/vtop/login").mock(
        return_value=httpx.Response(200, text="<html><body>Welcome</body></html>")
    )
    respx.get(f"{BASE_URL}/vtop/open/page").mock(
        return_value=httpx.Response(200, text="<html><body>shell</body></html>")
    )
    respx.get(f"{BASE_URL}/vtop/academics/common/StudentAttendance").mock(
        return_value=httpx.Response(200, text="<html><body>shell</body></html>")
    )
    monkeypatch.setattr(
        "vtop_mcp.vtop.auth.login.solve_captcha_base64",
        lambda _b64, manual=None: "ABCDEF",
    )

    async with VtopHttpClient(settings) as client:
        flow = LoginFlow(client, settings)
        result = await flow.login()
        assert result.status == "captcha_failed"
        assert client.session_data.authenticated is False
        assert client.session_data.authorized_id is None
