"""Marks service."""

from __future__ import annotations

from vtop_mcp.services._semester import with_semester
from vtop_mcp.models.marks import MarksList
from vtop_mcp.parsers.marks import parse_marks
from vtop_mcp.services._http_helpers import ensure_ok, post_menu_shell
from vtop_mcp.services.bootstrap import AuthContext
from vtop_mcp.vtop.client import VtopHttpClient


async def fetch_marks(
    client: VtopHttpClient,
    ctx: AuthContext,
    semester_id: str,
) -> MarksList:
    await post_menu_shell(client, ctx, "read.marks_page")
    response = await client.request_operation(
        "read.marks",
        with_semester(ctx, semester_id),
    )
    ensure_ok(response, operation_id="read.marks")
    return parse_marks(response.text, semester_id)
