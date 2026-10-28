"""VTOP student login flow (HTTP allowlist only)."""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass
from typing import Literal

from vtop_mcp.config import Settings
from vtop_mcp.exceptions import (
    CaptchaSolveError,
    InvalidCredentialsError,
    RecaptchaOnlyError,
)
from vtop_mcp.vtop.auth.captcha import solve_captcha_base64
from vtop_mcp.vtop.auth.credentials import load_credentials
from vtop_mcp.vtop.client import VtopHttpClient
from vtop_mcp.vtop.constants import (
    CAPTCHA_TYPE_GOOGLE,
    FIELD_CAPTCHA,
    FIELD_CSRF,
    FIELD_PASSWORD,
    FIELD_PRELOGIN_FLAG,
    FIELD_USERNAME,
    PRELOGIN_FLAG_STUDENT,
)
from vtop_mcp.vtop.html_parse import (
    detect_captcha_type,
    extract_authorized_id,
    extract_captcha_jpeg_base64,
    extract_csrf,
    extract_login_error,
    page_has_login_form,
    page_has_otp_form,
)

logger = logging.getLogger(__name__)

LoginStatus = Literal[
    "authenticated",
    "otp_required",
    "invalid_credentials",
    "captcha_failed",
]


@dataclass
class LoginResult:
    status: LoginStatus
    message: str | None = None
    regno: str | None = None


@dataclass
class _OtpContext:
    csrf: str
    regno: str


class LoginFlow:
    """Orchestrate prelogin, captcha, login, and OTP verification."""

    def __init__(self, client: VtopHttpClient, settings: Settings) -> None:
        self._client = client
        self._settings = settings
        self._otp_context: _OtpContext | None = None

    @property
    def otp_pending(self) -> bool:
        return self._otp_context is not None

    async def login(
        self,
        *,
        regno: str | None = None,
        password: str | None = None,
    ) -> LoginResult:
        username, passwd = self._resolve_credentials(regno, password)
        attempts = 0
        while attempts < self._settings.max_captcha_retries:
            attempts += 1
            try:
                result = await self._attempt_login(username, passwd)
            except CaptchaSolveError as exc:
                logger.info("Captcha solve failed: %s", exc)
                self._client.clear_session()
                continue

            if result.status == "otp_required" and self._settings.otp:
                return await self.verify_otp(self._settings.otp, regno=username)
            if result.status != "captcha_failed":
                return result

            self._client.clear_session()

        return LoginResult(
            status="captcha_failed",
            message=(
                f"Login failed after {self._settings.max_captcha_retries} "
                "captcha attempts (wrong answer or solve error)."
            ),
        )

    async def verify_otp(self, otp: str, *, regno: str | None = None) -> LoginResult:
        if not self._otp_context:
            return LoginResult(
                status="captcha_failed",
                message="No OTP challenge in progress. Call login first.",
            )
        ctx = self._otp_context
        if regno and regno.upper() != ctx.regno:
            return LoginResult(status="captcha_failed", message="Regno mismatch for OTP.")

        response = await self._client.request_operation(
            "auth.validate_otp",
            {
                FIELD_CSRF: ctx.csrf,
                "otp": otp,
                "otpValue": otp,
                "username": ctx.regno,
            },
        )
        html = response.text
        return self._finalize(html, ctx.regno)

    def _resolve_credentials(
        self,
        regno: str | None,
        password: str | None,
    ) -> tuple[str, str]:
        if regno and password:
            return regno.strip().upper(), password
        loaded = load_credentials(self._settings)
        return loaded

    async def _attempt_login(self, username: str, password: str) -> LoginResult:
        init_html = await self._load_init_page_with_text_captcha()

        captcha_b64 = extract_captcha_jpeg_base64(init_html)
        if not captcha_b64:
            refresh = await self._client.request_operation("auth.captcha_refresh")
            captcha_b64 = extract_captcha_jpeg_base64(refresh.text)
        if not captcha_b64:
            return LoginResult(status="captcha_failed", message="Captcha image missing")

        captcha_text = solve_captcha_base64(captcha_b64)
        login_csrf = extract_csrf(init_html)
        if not login_csrf:
            return LoginResult(status="captcha_failed", message="Missing CSRF on init page")

        submit = await self._client.request_operation(
            "auth.login_submit",
            {
                FIELD_CSRF: login_csrf,
                FIELD_USERNAME: username,
                FIELD_PASSWORD: password,
                FIELD_CAPTCHA: captcha_text,
            },
        )
        return self._finalize(submit.text, username)

    async def _load_init_page_with_text_captcha(self) -> str:
        """Restart landing → prelogin → init until VTOP serves built-in captcha."""
        limit = self._settings.max_recaptcha_refreshes
        for refresh in range(1, limit + 1):
            landing = await self._client.request_operation("auth.login_landing")
            csrf = extract_csrf(landing.text)
            if not csrf:
                raise CaptchaSolveError("Missing CSRF on landing")

            await self._client.request_operation(
                "auth.prelogin_setup",
                {FIELD_CSRF: csrf, FIELD_PRELOGIN_FLAG: PRELOGIN_FLAG_STUDENT},
            )

            init = await self._client.request_operation("auth.init_page")
            init_html = init.text
            if detect_captcha_type(init_html) != CAPTCHA_TYPE_GOOGLE:
                return init_html

            logger.info(
                "Google reCAPTCHA on init page; reloading login (%s/%s)",
                refresh,
                limit,
            )
            self._client.clear_session()

        raise RecaptchaOnlyError(
            "Could not obtain a built-in text captcha after "
            f"{limit} login reloads. VTOP kept serving Google reCAPTCHA."
        )

    def _finalize(self, html: str, regno: str) -> LoginResult:
        if page_has_otp_form(html):
            csrf = extract_csrf(html)
            if csrf:
                self._otp_context = _OtpContext(csrf=csrf, regno=regno)
            self._client.session_data.regno = regno
            self._client.session_data.authenticated = False
            self._client.persist_session()
            return LoginResult(
                status="otp_required",
                message="OTP required. Use verify_otp with the emailed code.",
                regno=regno,
            )

        err = extract_login_error(html)
        if err and page_has_login_form(html):
            if re.search(r"invalid|captcha|password", err, re.I):
                if "captcha" in err.lower():
                    return LoginResult(status="captcha_failed", message=err)
                raise InvalidCredentialsError(err)
            return LoginResult(status="invalid_credentials", message=err)

        auth_id = extract_authorized_id(html)
        if auth_id or not page_has_login_form(html):
            self._otp_context = None
            self._client.session_data.regno = regno
            self._client.session_data.authenticated = True
            if auth_id:
                self._client.session_data.authorized_id = auth_id
            self._client.persist_session()
            return LoginResult(status="authenticated", regno=regno)

        return LoginResult(
            status="captcha_failed",
            message="Unrecognized login response",
        )
