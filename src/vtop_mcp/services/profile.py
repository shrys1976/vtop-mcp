"""Student profile service."""

from __future__ import annotations

from vtop_mcp.models.profile import Profile
from vtop_mcp.parsers.profile import parse_profile
from vtop_mcp.services._http_helpers import ensure_ok, menu_post_params
from vtop_mcp.services.bootstrap import AuthContext
from vtop_mcp.vtop.client import VtopHttpClient


async def fetch_profile(client: VtopHttpClient, ctx: AuthContext) -> Profile:
    response = await client.request_operation("read.profile", menu_post_params(ctx))
    ensure_ok(response, operation_id="read.profile")
    return parse_profile(response.text)
