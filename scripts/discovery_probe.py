#!/usr/bin/env python3
"""Local VTOP discovery probe (M1). Status codes only — no secrets logged."""

from __future__ import annotations

import re
import sys
import urllib.error
import urllib.parse
import urllib.request
from http.cookiejar import CookieJar

from vtop_mcp.vtop.constants import (
    BASE_URL,
    DEFAULT_USER_AGENT,
    FIELD_CSRF,
    FIELD_PRELOGIN_FLAG,
    PATH_CAPTCHA_NEW,
    PATH_INIT_PAGE,
    PATH_LOGIN_LANDING,
    PATH_PRELOGIN_SETUP,
    PRELOGIN_FLAG_STUDENT,
)

TIMEOUT_SEC = 30


def _open(
    jar: CookieJar,
    url: str,
    *,
    method: str = "GET",
    data: bytes | None = None,
) -> tuple[int, str | None]:
    opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(jar))
    headers = {"User-Agent": DEFAULT_USER_AGENT}
    if data is not None:
        headers["Content-Type"] = "application/x-www-form-urlencoded"
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with opener.open(req, timeout=TIMEOUT_SEC) as resp:
            final = resp.geturl()
            loc = final if final != url else None
            return resp.status, loc
    except urllib.error.HTTPError as exc:
        loc = exc.headers.get("Location")
        return exc.code, loc


def _fetch_html(jar: CookieJar, url: str) -> tuple[int, str]:
    opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(jar))
    req = urllib.request.Request(
        url,
        headers={"User-Agent": DEFAULT_USER_AGENT},
        method="GET",
    )
    with opener.open(req, timeout=TIMEOUT_SEC) as resp:
        body = resp.read().decode("utf-8", errors="replace")
        return resp.status, body


def _extract_csrf(html: str) -> str | None:
    match = re.search(rf'name="{FIELD_CSRF}" value="([^"]+)"', html)
    return match.group(1) if match else None


def main() -> int:
    jar = CookieJar()
    landing = f"{BASE_URL}{PATH_LOGIN_LANDING}"
    status, html = _fetch_html(jar, landing)
    print(f"GET {PATH_LOGIN_LANDING} -> {status}")
    csrf = _extract_csrf(html)
    if not csrf:
        print("WARN: no _csrf on landing page", file=sys.stderr)
        return 1

    setup_url = f"{BASE_URL}{PATH_PRELOGIN_SETUP}"
    body = urllib.parse.urlencode(
        {FIELD_CSRF: csrf, FIELD_PRELOGIN_FLAG: PRELOGIN_FLAG_STUDENT}
    ).encode()
    code, loc = _open(jar, setup_url, method="POST", data=body)
    print(f"POST {PATH_PRELOGIN_SETUP} -> {code} location={loc!r}")
    if code not in (302, 303, 307, 308) and loc is None:
        print(
            "WARN: expected redirect to init/page; check CSRF and cookie jar",
            file=sys.stderr,
        )

    init_url = f"{BASE_URL}{PATH_INIT_PAGE}"
    status, init_html = _fetch_html(jar, init_url)
    print(f"GET {PATH_INIT_PAGE} -> {status}")
    has_builtin = "captchaStr" in init_html
    has_recaptcha = "recaptcha" in init_html.lower()
    captcha_match = re.search(r"var captchaType=(\d+)", init_html)
    captcha_type = captcha_match.group(1) if captcha_match else "?"
    print(
        f"init/page: captchaType={captcha_type} "
        f"builtin_fields={has_builtin} recaptcha_script={has_recaptcha}"
    )

    captcha_url = f"{BASE_URL}{PATH_CAPTCHA_NEW}"
    status, cap_html = _fetch_html(jar, captcha_url)
    has_data_uri = "data:image/jpeg;base64," in cap_html
    print(f"GET {PATH_CAPTCHA_NEW} -> {status} base64_jpeg_fragment={has_data_uri}")

    print("OK (no cookies or tokens printed)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
