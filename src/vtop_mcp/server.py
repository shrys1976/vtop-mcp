"""VTOP MCP server (stdio)."""

from __future__ import annotations

import json
import logging
import sys
from typing import Any

from mcp.server import MCPServer

from vtop_mcp.app_state import VtopApp
from vtop_mcp.exceptions import (
    CaptchaSolveError,
    CredentialsMissingError,
    InvalidCredentialsError,
    RecaptchaOnlyError,
)
from vtop_mcp.mcp_tools import err_payload, ok_payload
from vtop_mcp.models.profile import Profile
from vtop_mcp.models.semesters import SemesterList
from vtop_mcp.models.session import SessionStatus
from vtop_mcp.server_tools import with_auth
from vtop_mcp.services._http_helpers import VtopResponseError
from vtop_mcp.services.attendance import fetch_attendance
from vtop_mcp.services.bootstrap import NotAuthenticatedError, resolve_auth_context
from vtop_mcp.services.calendar import fetch_academic_calendar
from vtop_mcp.services.courses import fetch_courses
from vtop_mcp.services.exams import fetch_exam_schedule
from vtop_mcp.services.faculty import FacultyQueryTooShortError, fetch_faculty
from vtop_mcp.services.grades import fetch_grades
from vtop_mcp.services.hod_dean import fetch_hod_dean
from vtop_mcp.services.marks import fetch_marks
from vtop_mcp.services.profile import fetch_profile
from vtop_mcp.services.proctor import fetch_proctor
from vtop_mcp.services.semesters import fetch_semesters
from vtop_mcp.services.spotlight import fetch_spotlight
from vtop_mcp.services.timetable import fetch_timetable

logging.basicConfig(stream=sys.stderr, level=logging.INFO)
logger = logging.getLogger(__name__)

INSTRUCTIONS = (
    "Call vtop_session_status first. If not authenticated, call vtop_login "
    "(auto OCR) or vtop_get_login_captcha then vtop_login_with_captcha when "
    "OCR fails. For semester-scoped data, call list_semesters and pass "
    "semester_id from the result."
)

mcp = MCPServer(
    "vtop-mcp",
    instructions=INSTRUCTIONS,
)
app = VtopApp()

# collect session info
def _session_status() -> SessionStatus:
    meta = app.client.session_data
    return SessionStatus(
        authenticated=bool(meta.authenticated and meta.authorized_id),
        regno=meta.regno,
        session_age_seconds=app.session_age_seconds(),
        otp_pending=app.login_flow.otp_pending,
        captcha_pending=app.login_flow.captcha_pending,
        authorized_id_present=bool(meta.authorized_id),
    )


@mcp.tool(name="vtop_session_status")
async def vtop_session_status() -> dict[str, Any]:
    """Report whether a VTOP session is active."""
    return ok_payload(_session_status())


def _login_captcha_hint() -> dict[str, Any]:
    challenge = app.login_flow.captcha_hint()
    if not challenge:
        return {}
    return {
        "captcha_image_base64": challenge.captcha_image_base64,
        "captcha_image_data_url": challenge.captcha_image_data_url,
        "hint": "Call vtop_get_login_captcha or vtop_login_with_captcha.",
    }


@mcp.tool(name="vtop_get_login_captcha")
async def vtop_get_login_captcha() -> dict[str, Any]:
    """Fetch the current VTOP text captcha image for manual entry."""
    try:
        challenge = await app.login_flow.fetch_login_captcha()
    except CredentialsMissingError as exc:
        return err_payload("credentials_missing", str(exc))
    except RecaptchaOnlyError as exc:
        return err_payload("recaptcha_only", str(exc))
    except CaptchaSolveError as exc:
        return err_payload("captcha_failed", str(exc))

    return ok_payload(
        {
            "regno": challenge.regno,
            "captcha_image_base64": challenge.captcha_image_base64,
            "captcha_image_data_url": challenge.captcha_image_data_url,
            "message": "Read the captcha and call vtop_login_with_captcha.",
        }
    )


@mcp.tool(name="vtop_login_with_captcha")
async def vtop_login_with_captcha(captcha: str) -> dict[str, Any]:
    """Complete login with captcha text you read from vtop_get_login_captcha."""
    try:
        result = await app.login_flow.login_with_captcha(captcha)
    except InvalidCredentialsError as exc:
        return err_payload("invalid_credentials", str(exc))

    return _login_result_payload(result)


@mcp.tool(name="vtop_login")
async def vtop_login(captcha: str | None = None) -> dict[str, Any]:
    """Log in using VTOP_REGNO/VTOP_PASSWORD or keyring credentials."""
    try:
        result = await app.login_flow.login(captcha=captcha)
    except CredentialsMissingError as exc:
        return err_payload("credentials_missing", str(exc))
    except RecaptchaOnlyError as exc:
        return err_payload("recaptcha_only", str(exc))
    except InvalidCredentialsError as exc:
        return err_payload("invalid_credentials", str(exc))
    except CaptchaSolveError as exc:
        payload = err_payload("captcha_failed", str(exc))
        payload.update(_login_captcha_hint())
        return payload

    return _login_result_payload(result)


def _login_result_payload(result: Any) -> dict[str, Any]:
    if result.status == "authenticated":
        app.set_profile_cache(None)
        return ok_payload(
            {
                "status": result.status,
                "regno": result.regno,
                "message": "Logged in successfully.",
            }
        )
    if result.status == "otp_required":
        return ok_payload(
            {
                "status": result.status,
                "regno": result.regno,
                "message": result.message,
                "error_code": "otp_required",
            }
        )
    payload = err_payload(result.status, result.message or "Login failed.")
    if result.status == "captcha_failed":
        payload.update(_login_captcha_hint())
    return payload


@mcp.tool(name="vtop_verify_otp")
async def vtop_verify_otp(otp: str) -> dict[str, Any]:
    """Complete login when VTOP requires an email OTP."""
    result = await app.login_flow.verify_otp(otp)
    if result.status == "authenticated":
        app.set_profile_cache(None)
        return ok_payload(
            {"status": result.status, "regno": result.regno, "message": "OTP accepted."}
        )
    return err_payload(result.status, result.message or "OTP verification failed.")


@mcp.tool(name="vtop_logout")
async def vtop_logout() -> dict[str, Any]:
    """Clear local encrypted session and cookies."""
    app.client.clear_session()
    app.set_profile_cache(None)
    return ok_payload({"message": "Local VTOP session cleared."})


@mcp.tool(name="list_semesters")
async def list_semesters() -> dict[str, Any]:
    """List semesterSubId values for semester-scoped tools."""
    try:
        ctx = await resolve_auth_context(app.client)
        semesters: SemesterList = await fetch_semesters(app.client, ctx)
    except NotAuthenticatedError as exc:
        return err_payload("not_authenticated", str(exc))
    if not semesters.semesters:
        return err_payload("parse_failed", "No semesters found in VTOP response.")
    return ok_payload(semesters)


@mcp.tool(name="get_profile")
async def get_profile() -> dict[str, Any]:
    """Fetch student profile summary (read-only)."""
    try:
        ctx = await resolve_auth_context(app.client)
        profile: Profile = await fetch_profile(app.client, ctx)
        app.set_profile_cache(profile)
    except NotAuthenticatedError as exc:
        return err_payload("not_authenticated", str(exc))
    except VtopResponseError as exc:
        return err_payload("vtop_error", str(exc))
    return ok_payload(profile)


@mcp.tool(name="get_attendance")
async def get_attendance(semester_id: str) -> dict[str, Any]:
    """Fetch attendance for a semester (use list_semesters for semester_id)."""
    return await with_auth(app, fetch_attendance, semester_id)


@mcp.tool(name="get_timetable")
async def get_timetable(semester_id: str, week: int | None = None) -> dict[str, Any]:
    """Fetch timetable for a semester. week is reserved for future filtering."""
    _ = week
    return await with_auth(app, fetch_timetable, semester_id)


@mcp.tool(name="get_marks")
async def get_marks(semester_id: str) -> dict[str, Any]:
    """Fetch internal marks for a semester."""
    return await with_auth(app, fetch_marks, semester_id)


@mcp.tool(name="get_courses")
async def get_courses(semester_id: str) -> dict[str, Any]:
    """Fetch registered courses and faculty for a semester."""
    return await with_auth(app, fetch_courses, semester_id)


@mcp.tool(name="get_exams")
async def get_exams(semester_id: str | None = None) -> dict[str, Any]:
    """Fetch exam schedule; semester_id is optional."""
    try:
        ctx = await resolve_auth_context(app.client)
        schedule = await fetch_exam_schedule(app.client, ctx, semester_id)
    except NotAuthenticatedError as exc:
        return err_payload("not_authenticated", str(exc))
    except VtopResponseError as exc:
        return err_payload("vtop_error", str(exc))
    return ok_payload(schedule)


@mcp.tool(name="get_spotlight")
async def get_spotlight() -> dict[str, Any]:
    """Fetch spotlight links from the post-login dashboard."""
    return await with_auth(app, fetch_spotlight)


@mcp.tool(name="get_academic_calendar")
async def get_academic_calendar(semester_id: str | None = None) -> dict[str, Any]:
    """Fetch academic calendar entries; semester_id optional."""
    try:
        ctx = await resolve_auth_context(app.client)
        calendar = await fetch_academic_calendar(app.client, ctx, semester_id)
    except NotAuthenticatedError as exc:
        return err_payload("not_authenticated", str(exc))
    except VtopResponseError as exc:
        return err_payload("vtop_error", str(exc))
    return ok_payload(calendar)


@mcp.tool(name="get_grades")
async def get_grades(semester_id: str) -> dict[str, Any]:
    """Fetch semester grades (use list_semesters for semester_id)."""
    return await with_auth(app, fetch_grades, semester_id)


@mcp.tool(name="get_hod_dean")
async def get_hod_dean() -> dict[str, Any]:
    """Fetch school dean and head-of-department contact details."""
    return await with_auth(app, fetch_hod_dean)


@mcp.tool(name="get_proctor")
async def get_proctor() -> dict[str, Any]:
    """Fetch assigned proctor contact details."""
    return await with_auth(app, fetch_proctor)


@mcp.tool(name="search_faculty")
async def search_faculty(
    query: str,
    employee_id: str | None = None,
) -> dict[str, Any]:
    """Search faculty by name, or load detail when employee_id is set."""
    try:
        ctx = await resolve_auth_context(app.client)
        result = await fetch_faculty(app.client, ctx, query, employee_id)
    except NotAuthenticatedError as exc:
        return err_payload("not_authenticated", str(exc))
    except VtopResponseError as exc:
        return err_payload("vtop_error", str(exc))
    except FacultyQueryTooShortError as exc:
        return err_payload("invalid_query", str(exc))
    return ok_payload(result)


@mcp.resource("vtop://session/status")
async def resource_session_status() -> str:
    return json.dumps(ok_payload(_session_status()), indent=2)


@mcp.resource("vtop://profile")
async def resource_profile() -> str:
    cached = app.profile_cache
    if cached is None:
        payload = err_payload(
            "not_authenticated",
            "No cached profile. Call get_profile after login.",
        )
    else:
        payload = ok_payload(cached)
    return json.dumps(payload, indent=2)


def main() -> None:
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
