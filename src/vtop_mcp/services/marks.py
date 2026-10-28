"""Marks service."""

from __future__ import annotations

from vtop_mcp.models.marks import MarksList
from vtop_mcp.parsers.marks import parse_marks
from vtop_mcp.services._semester import with_semester
from vtop_mcp.services.bootstrap import AuthContext
from vtop_mcp.vtop.client import VtopHttpClient


async def fetch_marks(
    client: VtopHttpClient,
    ctx: AuthContext,
    semester_id: str,
) -> MarksList:
    response = await client.request_operation(
        "read.marks",
        with_semester(ctx, semester_id),
    )
    return parse_marks(response.text, semester_id)
