"""HTML parser unit tests."""

from __future__ import annotations

from pathlib import Path

from vtop_mcp.vtop.constants import CAPTCHA_TYPE_BUILTIN
from vtop_mcp.vtop.html_parse import (
    detect_captcha_type,
    extract_captcha_jpeg_base64,
    extract_csrf,
    page_has_otp_form,
)


def test_extract_csrf_and_captcha_from_fixture() -> None:
    html = Path("tests/fixtures/captcha/init_snippet.html").read_text()
    assert extract_csrf(html) == "test-csrf-token"
    assert extract_captcha_jpeg_base64(html) is not None
    assert detect_captcha_type(html) == CAPTCHA_TYPE_BUILTIN


def test_login_form_ignores_dashboard_chrome() -> None:
    from vtop_mcp.vtop.html_parse import page_has_login_form

    dashboard = '<a href="/vtop/prelogin/setup">menu</a><input id="username" />'
    assert page_has_login_form(dashboard) is False
    login = '<form id="vtopLoginForm"></form>'
    assert page_has_login_form(login) is True


def test_csrf_value_script() -> None:
    html = '<script>var csrfValue = "js-csrf-token";</script>'
    assert extract_csrf(html) == "js-csrf-token"


def test_otp_form_detection() -> None:
    assert page_has_otp_form('<form id="otpVerificationForm"></form>')
