"""Captcha solver unit tests."""

from __future__ import annotations

import pytest

from vtop_mcp.exceptions import CaptchaSolveError
from vtop_mcp.vtop.auth.captcha import solve_captcha_base64


def test_manual_captcha_normalizes() -> None:
    assert solve_captcha_base64("ignored", manual=" ab12cd ") == "AB12CD"


def test_manual_captcha_rejects_wrong_length() -> None:
    with pytest.raises(CaptchaSolveError):
        solve_captcha_base64("ignored", manual="ABC")
