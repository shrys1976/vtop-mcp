"""HTML helpers for VTOP login pages."""

from __future__ import annotations

import re

from bs4 import BeautifulSoup

from vtop_mcp.vtop.constants import (
    CAPTCHA_TYPE_BUILTIN,
    CAPTCHA_TYPE_GOOGLE,
    FIELD_CSRF,
)


def extract_csrf(html: str) -> str | None:
    soup = BeautifulSoup(html, "html.parser")
    tag = soup.find("input", attrs={"name": FIELD_CSRF})
    if tag and tag.get("value"):
        return str(tag["value"])
    return None


def detect_captcha_type(html: str) -> int:
    match = re.search(r"var\s+captchaType\s*=\s*(\d+)", html)
    if match:
        return int(match.group(1))
    if "g-recaptcha" in html and "captchaStr" not in html:
        return CAPTCHA_TYPE_GOOGLE
    return CAPTCHA_TYPE_BUILTIN


def extract_captcha_jpeg_base64(html: str) -> str | None:
    soup = BeautifulSoup(html, "html.parser")
    block = soup.find(id="captchaBlock") or soup
    img = block.find("img")
    if not img or not img.get("src"):
        return None
    src = str(img["src"])
    prefix = "data:image/jpeg;base64,"
    if not src.startswith(prefix):
        return None
    return src[len(prefix) :]


def page_has_login_form(html: str) -> bool:
    return "vtopLoginForm" in html or 'id="username"' in html


def page_has_otp_form(html: str) -> bool:
    return "otpVerificationForm" in html or "validateOtp" in html


def extract_authorized_id(html: str) -> str | None:
    soup = BeautifulSoup(html, "html.parser")
    tag = soup.find("input", attrs={"name": "authorizedID"})
    if tag and tag.get("value"):
        return str(tag["value"])
    return None


def extract_login_error(html: str) -> str | None:
    soup = BeautifulSoup(html, "html.parser")
    err = soup.find(class_=re.compile(r"text-danger"))
    if err and err.get_text(strip=True):
        return err.get_text(strip=True)
    if "Invalid" in html and page_has_login_form(html):
        return "Invalid username or password"
    return None
