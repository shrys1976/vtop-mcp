"""VTOP MCP server (stdio)."""

from __future__ import annotations

import json
import logging
import sys
from typing import Any

from mcp.server import MCPServer

from vtop_mcp.app_state import VtopApp
from vtop_mcp.exceptions import (
    CredentialsMissingError,
    InvalidCredentialsError,
    RecaptchaOnlyError,
)
from vtop_mcp.mcp_tools import err_payload, ok_payload
from vtop_mcp.models.profile import Profile
from vtop_mcp.models.semesters import SemesterList
from vtop_mcp.models.session import SessionStatus
from vtop_mcp.services.bootstrap import NotAuthenticatedError, resolve_auth_context
from vtop_mcp.services.profile import fetch_profile
from vtop_mcp.services.semesters import fetch_semesters

logging.basicConfig(stream=sys.stderr, level=logging.INFO)
logger = logging.getLogger(__name__)

INSTRUCTIONS = (
    "Call vtop_session_status first. If not authenticated, call vtop_login. "
    "For semester-scoped data in later tools, call list_semesters and pass "
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
        authenticated=meta.authenticated,
        regno=meta.regno,
        session_age_seconds=app.session_age_seconds(),
        otp_pending=app.login_flow.otp_pending,
    )


@mcp.tool(name="vtop_session_status")
async def vtop_session_status() -> dict[str, Any]:
    """Report whether a VTOP session is active."""
    return ok_payload(_session_status())


@mcp.tool(name="vtop_login")
async def vtop_login() -> dict[str, Any]:
    """Log in using VTOP_REGNO/VTOP_PASSWORD or keyring credentials."""
    try:
        result = await app.login_flow.login()
    except CredentialsMissingError as exc:
        return err_payload("credentials_missing", str(exc))
    except RecaptchaOnlyError as exc:
        return err_payload("recaptcha_only", str(exc))
    except InvalidCredentialsError as exc:
        return err_payload("invalid_credentials", str(exc))

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
    return err_payload(
        result.status,
        result.message or "Login failed.",
    )


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
    return ok_payload(profile)


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
