"""VTOP student login flow (HTTP allowlist only)."""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass
from typing import Literal
from urllib.parse import urlparse

import httpx

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
    describe_form_fields,
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
    "login_rejected",
    "dashboard_unparsed",
]


@dataclass
class LoginResult:
    status: LoginStatus
    message: str | None = None
    regno: str | None = None


@dataclass
class CaptchaChallenge:
    """Pending login step: user or agent reads the image and submits text."""

    captcha_image_base64: str
    captcha_image_data_url: str
    regno: str


@dataclass
class _LoginCaptchaContext:
    username: str
    password: str
    login_csrf: str
    captcha_b64: str


@dataclass
class _OtpContext:
    csrf: str
    regno: str


def _should_retry_captcha(result: LoginResult) -> bool:
    """Retry only a wrong captcha answer, never a rejected session."""
    if result.status != "captcha_failed":
        return False
    message = (result.message or "").lower()
    if "login page" in message or "session" in message or "authorizedid" in message:
        return False
    return "captcha" in message


def _login_rejected_message(response: httpx.Response, client: VtopHttpClient) -> str:
    path = urlparse(str(response.url)).path or str(response.url)
    cookie = "present" if client.has_cookie("JSESSIONID") else "missing"
    return (
        "VTOP showed the login page again after submit "
        f"(HTTP {response.status_code} {path}; JSESSIONID {cookie}). "
        "The captcha was rejected or the session cookie was not kept. "
        "Submit one new captcha. Do not retry in a loop."
    )


class LoginFlow:
    """Orchestrate prelogin, captcha, login, and OTP verification."""

    def __init__(self, client: VtopHttpClient, settings: Settings) -> None:
        self._client = client
        self._settings = settings
        self._otp_context: _OtpContext | None = None
        self._captcha_context: _LoginCaptchaContext | None = None

    @property
    def otp_pending(self) -> bool:
        return self._otp_context is not None

    @property
    def captcha_pending(self) -> bool:
        return self._captcha_context is not None

    def captcha_hint(self) -> CaptchaChallenge | None:
        if not self._captcha_context:
            return None
        return self._challenge_from_context(self._captcha_context)

    async def fetch_login_captcha(
        self,
        *,
        regno: str | None = None,
        password: str | None = None,
    ) -> CaptchaChallenge:
        """Load the login page and return the current text captcha image."""
        username, passwd = self._resolve_credentials(regno, password)
        ctx = await self._prepare_captcha_context(username, passwd)
        self._captcha_context = ctx
        return self._challenge_from_context(ctx)

    async def login_with_captcha(
        self,
        captcha: str,
        *,
        regno: str | None = None,
    ) -> LoginResult:
        """Submit login using captcha text from fetch_login_captcha."""
        ctx = self._captcha_context
        if not ctx:
            return LoginResult(
                status="captcha_failed",
                message="No captcha challenge. Call fetch_login_captcha first.",
            )
        if regno and regno.upper() != ctx.username:
            return LoginResult(status="captcha_failed", message="Regno mismatch.")

        try:
            captcha_text = solve_captcha_base64(ctx.captcha_b64, manual=captcha)
        except CaptchaSolveError as exc:
            return LoginResult(status="captcha_failed", message=str(exc))

        result = await self._submit_login(ctx, captcha_text)
        if result.status in ("authenticated", "otp_required"):
            self._captcha_context = None
        return result

    async def login(
        self,
        *,
        regno: str | None = None,
        password: str | None = None,
        captcha: str | None = None,
    ) -> LoginResult:
        if captcha:
            if not self._captcha_context:
                await self.fetch_login_captcha(regno=regno, password=password)
            return await self.login_with_captcha(captcha, regno=regno)
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
            if not _should_retry_captcha(result):
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
        return await self._finalize(response, ctx.regno)

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
        ctx = await self._prepare_captcha_context(username, password)
        try:
            captcha_text = solve_captcha_base64(ctx.captcha_b64)
        except CaptchaSolveError:
            self._captcha_context = ctx
            raise

        return await self._submit_login(ctx, captcha_text)

    async def _prepare_captcha_context(
        self,
        username: str,
        password: str,
    ) -> _LoginCaptchaContext:
        init_html = await self._load_init_page_with_text_captcha()
        captcha_b64 = extract_captcha_jpeg_base64(init_html)
        if not captcha_b64:
            refresh = await self._client.request_operation("auth.captcha_refresh")
            captcha_b64 = extract_captcha_jpeg_base64(refresh.text)
        if not captcha_b64:
            raise CaptchaSolveError("Captcha image missing")

        login_csrf = extract_csrf(init_html)
        if not login_csrf:
            raise CaptchaSolveError("Missing CSRF on init page")

        return _LoginCaptchaContext(
            username=username,
            password=password,
            login_csrf=login_csrf,
            captcha_b64=captcha_b64,
        )

    @staticmethod
    def _challenge_from_context(ctx: _LoginCaptchaContext) -> CaptchaChallenge:
        return CaptchaChallenge(
            captcha_image_base64=ctx.captcha_b64,
            captcha_image_data_url=f"data:image/jpeg;base64,{ctx.captcha_b64}",
            regno=ctx.username,
        )

    async def _submit_login(
        self,
        ctx: _LoginCaptchaContext,
        captcha_text: str,
    ) -> LoginResult:
        submit = await self._client.request_operation(
            "auth.login_submit",
            {
                FIELD_CSRF: ctx.login_csrf,
                FIELD_USERNAME: ctx.username,
                FIELD_PASSWORD: ctx.password,
                FIELD_CAPTCHA: captcha_text,
            },
        )
        result = await self._finalize(submit, ctx.username)
        if result.status == "captcha_failed" and "captcha" in (result.message or "").lower():
            new_b64 = extract_captcha_jpeg_base64(submit.text)
            if not new_b64:
                refresh = await self._client.request_operation("auth.captcha_refresh")
                new_b64 = extract_captcha_jpeg_base64(refresh.text)
            if new_b64:
                ctx.captcha_b64 = new_b64
                self._captcha_context = ctx
        return result

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

    async def _finalize(self, response: httpx.Response, regno: str) -> LoginResult:
        html = response.text
        if page_has_otp_form(html):
            csrf = extract_csrf(html)
            if csrf:
                self._otp_context = _OtpContext(csrf=csrf, regno=regno)
            self._client.session_data.regno = regno
            self._client.session_data.authenticated = False
            self._client.session_data.authorized_id = None
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

        if page_has_login_form(html):
            return LoginResult(
                status="login_rejected",
                message=_login_rejected_message(response, self._client),
            )

        return await self._confirm_dashboard_session(response, html, regno)

    async def _confirm_dashboard_session(
        self,
        response: httpx.Response,
        submit_html: str,
        regno: str,
    ) -> LoginResult:
        """Read csrfValue from the login response, then the student home page."""
        auth_id = extract_authorized_id(submit_html)
        csrf = extract_csrf(submit_html)
        if csrf and not auth_id:
            auth_id = regno

        if not (auth_id and csrf):
            for operation_id in ("read.content", "read.open_page", "read.attendance_page"):
                follow = await self._client.request_operation(operation_id)
                if page_has_login_form(follow.text):
                    continue
                auth_id = auth_id or extract_authorized_id(follow.text)
                csrf = csrf or extract_csrf(follow.text)
                if csrf and not auth_id:
                    auth_id = regno
                if auth_id and csrf:
                    break

        if not auth_id or not csrf:
            self._mark_unauthenticated()
            path = urlparse(str(response.url)).path or str(response.url)
            details = describe_form_fields(submit_html)
            logger.warning(
                "Post-login page missing tokens path=%s %s",
                path,
                details,
            )
            return LoginResult(
                status="dashboard_unparsed",
                message=(
                    "Login left the captcha page, but no CSRF token was found "
                    f"(HTTP {response.status_code} {path}; {details}). "
                    f"Username sent: {regno}. "
                    "Use the registration number as VTOP_REGNO, and keep any "
                    "$ in the password literal (do not let the shell expand it)."
                ),
            )

        self._otp_context = None
        self._client.session_data.regno = regno
        self._client.session_data.authenticated = True
        self._client.session_data.authorized_id = auth_id
        self._client.session_data.csrf = csrf
        self._client.persist_session()
        return LoginResult(
            status="authenticated",
            message="Logged in. Dashboard authorizedID and CSRF confirmed.",
            regno=regno,
        )

    def _mark_unauthenticated(self) -> None:
        self._client.session_data.authenticated = False
        self._client.session_data.authorized_id = None
        self._client.session_data.csrf = None
        self._client.persist_session()
