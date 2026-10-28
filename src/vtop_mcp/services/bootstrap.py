"""Resolve authorizedID and CSRF for authenticated POSTs."""

from __future__ import annotations

from dataclasses import dataclass

from vtop_mcp.exceptions import VtopMcpError
from vtop_mcp.vtop.client import VtopHttpClient
from vtop_mcp.vtop.constants import FIELD_AUTHORIZED_ID, FIELD_CSRF
from vtop_mcp.vtop.html_parse import extract_authorized_id, extract_csrf, page_has_login_form


class NotAuthenticatedError(VtopMcpError):
    """Session is missing or expired."""


@dataclass(frozen=True)
class AuthContext:
    authorized_id: str
    csrf: str


async def resolve_auth_context(client: VtopHttpClient) -> AuthContext:
    meta = client.session_data
    if not meta.authenticated:
        raise NotAuthenticatedError("Not logged in. Call vtop_login first.")

    for operation_id in ("read.open_page", "read.attendance_page"):
        response = await client.request_operation(operation_id)
        html = response.text
        if page_has_login_form(html):
            meta.authenticated = False
            meta.authorized_id = None
            meta.csrf = None
            client.persist_session()
            raise NotAuthenticatedError("Session expired. Call vtop_login again.")

        auth_id = extract_authorized_id(html) or meta.authorized_id
        csrf = extract_csrf(html) or meta.csrf
        if auth_id and csrf:
            meta.authorized_id = auth_id
            meta.csrf = csrf
            meta.authenticated = True
            client.persist_session()
            return AuthContext(authorized_id=auth_id, csrf=csrf)

    raise NotAuthenticatedError(
        "Could not read a fresh CSRF token from VTOP. "
        "The saved login was kept. Call list_semesters once more, "
        "or log in again a single time."
    )


def auth_post_params(
    ctx: AuthContext,
    *,
    client: VtopHttpClient | None = None,
) -> dict[str, str]:
    authorized_id = ctx.authorized_id
    csrf = ctx.csrf
    if client is not None:
        meta = client.session_data
        authorized_id = meta.authorized_id or authorized_id
        csrf = meta.csrf or csrf
    return {FIELD_AUTHORIZED_ID: authorized_id, FIELD_CSRF: csrf}
