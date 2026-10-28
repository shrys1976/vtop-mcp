"""Student profile service."""

from __future__ import annotations

from vtop_mcp.models.profile import Profile
from vtop_mcp.parsers.profile import parse_profile
from vtop_mcp.services.bootstrap import AuthContext, auth_post_params
from vtop_mcp.vtop.client import VtopHttpClient


async def fetch_profile(client: VtopHttpClient, ctx: AuthContext) -> Profile:
    params = auth_post_params(ctx)
    params["verifyMenu"] = "true"
    response = await client.request_operation("read.profile", params)
    return parse_profile(response.text)
