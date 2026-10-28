"""Spotlight announcements service."""

from __future__ import annotations

from vtop_mcp.models.spotlight import SpotlightList
from vtop_mcp.parsers.spotlight import parse_spotlight
from vtop_mcp.services._http_helpers import ensure_ok, menu_post_params
from vtop_mcp.services.bootstrap import AuthContext
from vtop_mcp.vtop.client import VtopHttpClient


async def fetch_spotlight(client: VtopHttpClient, ctx: AuthContext) -> SpotlightList:
    response = await client.request_operation("read.home", menu_post_params(ctx))
    ensure_ok(response, operation_id="read.home")
    return parse_spotlight(response.text)
