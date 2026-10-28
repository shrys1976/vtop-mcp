"""Proctor details service."""

from __future__ import annotations

from vtop_mcp.models.proctor import ProctorDetails
from vtop_mcp.parsers.proctor import parse_proctor
from vtop_mcp.services._http_helpers import ensure_ok, menu_post_params
from vtop_mcp.services.bootstrap import AuthContext
from vtop_mcp.vtop.client import VtopHttpClient


async def fetch_proctor(client: VtopHttpClient, ctx: AuthContext) -> ProctorDetails:
    response = await client.request_operation("read.proctor", menu_post_params(ctx))
    ensure_ok(response, operation_id="read.proctor")
    return parse_proctor(response.text)
