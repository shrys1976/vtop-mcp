"""HOD and Dean service."""

from __future__ import annotations

from vtop_mcp.models.hod_dean import HodDeanInfo
from vtop_mcp.parsers.hod_dean import parse_hod_dean
from vtop_mcp.services._http_helpers import ensure_ok, menu_post_params
from vtop_mcp.services.bootstrap import AuthContext
from vtop_mcp.vtop.client import VtopHttpClient


async def fetch_hod_dean(client: VtopHttpClient, ctx: AuthContext) -> HodDeanInfo:
    response = await client.request_operation("read.hod_dean", menu_post_params(ctx))
    ensure_ok(response, operation_id="read.hod_dean")
    return parse_hod_dean(response.text)
