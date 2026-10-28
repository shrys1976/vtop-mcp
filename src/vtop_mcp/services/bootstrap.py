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
            client.persist_session()
            raise NotAuthenticatedError("Session expired. Call vtop_login again.")

        auth_id = extract_authorized_id(html) or meta.authorized_id
        csrf = extract_csrf(html)
        if auth_id and csrf:
            meta.authorized_id = auth_id
            meta.authenticated = True
            client.persist_session()
            return AuthContext(authorized_id=auth_id, csrf=csrf)

    meta.authenticated = False
    client.persist_session()
    raise NotAuthenticatedError(
        "Could not resolve authorizedID and CSRF from the VTOP dashboard. "
        "Call vtop_login again."
    )


def auth_post_params(ctx: AuthContext) -> dict[str, str]:
    return {FIELD_AUTHORIZED_ID: ctx.authorized_id, FIELD_CSRF: ctx.csrf}
