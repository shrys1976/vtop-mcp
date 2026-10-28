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
        value = str(tag["value"]).strip()
        if value:
            return value
    meta = soup.find("meta", attrs={"name": FIELD_CSRF})
    if meta and meta.get("content"):
        value = str(meta["content"]).strip()
        if value:
            return value
    match = re.search(
        r"""(?:name|id)=["']_csrf["'][^>]*?(?:value|content)=["']([^"']+)["']"""
        r"""|(?:value|content)=["']([^"']+)["'][^>]*?(?:name|id)=["']_csrf["']""",
        html,
        re.I,
    )
    if match:
        return (match.group(1) or match.group(2) or "").strip() or None
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
    return (
        "vtopLoginForm" in html
        or 'name="captchaStr"' in html
        or 'id="username"' in html
        or "prelogin/setup" in html
    )


def page_has_otp_form(html: str) -> bool:
    return "otpVerificationForm" in html or "validateOtp" in html


def extract_authorized_id(html: str) -> str | None:
    soup = BeautifulSoup(html, "html.parser")
    tag = soup.find("input", attrs={"name": "authorizedID"})
    if tag is None:
        tag = soup.find(id="authorizedID")
    if tag and tag.get("value"):
        value = str(tag["value"]).strip()
        if value:
            return value
    match = re.search(
        r"""authorizedID["']?\s*[:=]\s*["']([^"']+)["']""",
        html,
        re.I,
    )
    if match:
        return match.group(1).strip() or None
    return None


def extract_login_error(html: str) -> str | None:
    soup = BeautifulSoup(html, "html.parser")
    err = soup.find(class_=re.compile(r"text-danger"))
    if err and err.get_text(strip=True):
        return err.get_text(strip=True)
    if "Invalid" in html and page_has_login_form(html):
        return "Invalid username or password"
    return None
