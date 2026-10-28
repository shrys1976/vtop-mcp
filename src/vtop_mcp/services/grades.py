"""Semester grades service."""

from __future__ import annotations

from vtop_mcp.models.grades import GradeList
from vtop_mcp.parsers.grades import parse_grades
from vtop_mcp.services._semester import with_semester
from vtop_mcp.services._http_helpers import ensure_ok, post_menu_shell
from vtop_mcp.services.bootstrap import AuthContext
from vtop_mcp.vtop.client import VtopHttpClient


async def fetch_grades(
    client: VtopHttpClient,
    ctx: AuthContext,
    semester_id: str,
) -> GradeList:
    await post_menu_shell(client, ctx, "read.grade_view_page")
    response = await client.request_operation(
        "read.grade_view",
        with_semester(ctx, semester_id),
    )
    ensure_ok(response, operation_id="read.grade_view")
    return parse_grades(response.text, semester_id)
