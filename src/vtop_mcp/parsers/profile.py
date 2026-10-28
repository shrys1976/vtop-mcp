"""Parse student profile HTML."""

from __future__ import annotations

import re

from bs4 import BeautifulSoup

from vtop_mcp.models.profile import Profile


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


def _label_value_pairs(soup: BeautifulSoup) -> dict[str, str]:
    pairs: dict[str, str] = {}
    for row in soup.find_all("tr"):
        cells = row.find_all(["th", "td"])
        if len(cells) < 2:
            continue
        key = cells[0].get_text(" ", strip=True).lower()
        val = cells[1].get_text(" ", strip=True)
        if key and val:
            pairs[key] = val
    for label in soup.find_all(["label", "span", "strong"]):
        text = label.get_text(" ", strip=True)
        if ":" not in text:
            continue
        key, val = text.split(":", 1)
        key = key.strip().lower()
        val = val.strip()
        if key and val and key not in pairs:
            pairs[key] = val
    return pairs


def parse_profile(html: str) -> Profile:
    soup = BeautifulSoup(html, "html.parser")
    pairs = _label_value_pairs(soup)

    def pick(*keys: str) -> str | None:
        for key in keys:
            for label, value in pairs.items():
                if key in label:
                    return value
        return None

    email = pick("email", "e-mail")
    regno = pick("register", "registration", "reg no", "student id")
    if not regno:
        match = re.search(r"\b(2[0-9][A-Z]{3}[0-9]{4,})\b", html)
        regno = match.group(1) if match else None

    return Profile(
        regno=regno,
        name=pick("name", "student name"),
        programme=pick("programme", "program", "degree"),
        branch=pick("branch", "specialization"),
        school=pick("school", "campus"),
        email=_mask_email(email) if email else None,
        mobile=pick("mobile", "phone", "contact"),
    )
