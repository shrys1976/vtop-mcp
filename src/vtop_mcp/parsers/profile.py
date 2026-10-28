"""Parse student profile HTML."""

from __future__ import annotations

import re

from bs4 import BeautifulSoup

from vtop_mcp.models.profile import Profile
from vtop_mcp.parsers._common import accordion_value


def _mask_email(email: str) -> str:
    email = email.strip()
    if "@" not in email:
        return email
    local, domain = email.split("@", 1)
    if len(local) <= 2:
        masked_local = "*" * len(local)
    else:
        masked_local = local[:2] + "*" * (len(local) - 2)
    return f"{masked_local}@{domain}"


def _header_label_value(soup: BeautifulSoup, key_phrase: str) -> str | None:
    labels = soup.find_all("label", class_="col-form-label")
    key_lower = key_phrase.lower()
    for i, label in enumerate(labels):
        text = label.get_text(" ", strip=True)
        if key_lower not in text.lower():
            continue
        style = label.get("style") or ""
        if "c7254e" in style or text.endswith(":"):
            if i + 1 < len(labels):
                value = labels[i + 1].get_text(" ", strip=True)
                if value and key_lower not in value.lower():
                    return value
        elif "c7254e" not in style and text and not text.endswith(":"):
            return text
    return None


def _profile_name(soup: BeautifulSoup) -> str | None:
    photo = soup.find("img", class_=re.compile(r"img-rounded|profile", re.I))
    if photo:
        for tag in photo.find_all_previous(["h3", "h4", "h5"], limit=3):
            text = tag.get_text(" ", strip=True)
            if text and len(text) < 80:
                return text
        for tag in photo.find_all_next(["h3", "h4", "h5"], limit=3):
            text = tag.get_text(" ", strip=True)
            if text and len(text) < 80:
                return text
    personal = accordion_value(soup, "PERSONAL", "name")
    if personal:
        return personal
    return _header_label_value(soup, "student name")


def parse_profile(html: str) -> Profile:
    soup = BeautifulSoup(html, "html.parser")
    regno = _header_label_value(soup, "register")
    programme_branch = _header_label_value(soup, "program")
    programme: str | None = None
    branch: str | None = None
    if programme_branch and " - " in programme_branch:
        programme, branch = programme_branch.split(" - ", 1)
    elif programme_branch:
        programme = programme_branch

    email = _header_label_value(soup, "email") or _header_label_value(
        soup, "e-mail"
    )
    mobile = accordion_value(soup, "PERSONAL", "mobile") or accordion_value(
        soup, "PERSONAL", "phone"
    )

    return Profile(
        regno=regno,
        name=_profile_name(soup),
        programme=programme,
        branch=branch,
        school=_header_label_value(soup, "school"),
        email=_mask_email(email) if email else None,
        mobile=mobile,
    )
