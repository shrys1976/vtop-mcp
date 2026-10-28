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
        max_captcha_retries=2,
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
