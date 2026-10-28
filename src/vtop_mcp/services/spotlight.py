"""Spotlight announcements service."""

from __future__ import annotations

from vtop_mcp.models.spotlight import SpotlightList
from vtop_mcp.parsers.spotlight import parse_spotlight
from vtop_mcp.vtop.client import VtopHttpClient


async def fetch_spotlight(client: VtopHttpClient) -> SpotlightList:
    response = await client.request_operation("auth.login_landing")
    return parse_spotlight(response.text)
