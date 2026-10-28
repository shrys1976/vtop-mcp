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


def test_otp_form_detection() -> None:
    assert page_has_otp_form('<form id="otpVerificationForm"></form>')
