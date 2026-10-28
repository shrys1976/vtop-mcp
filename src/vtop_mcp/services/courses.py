"""Registered courses service."""

from __future__ import annotations

from vtop_mcp.models.courses import CourseList
from vtop_mcp.parsers.courses import parse_courses
from vtop_mcp.services._http_helpers import (
    ensure_ok,
    post_menu_shell,
    semester_data_params,
)
from vtop_mcp.services.bootstrap import AuthContext
from vtop_mcp.vtop.client import VtopHttpClient


async def fetch_courses(
    client: VtopHttpClient,
    ctx: AuthContext,
    semester_id: str,
) -> CourseList:
    await post_menu_shell(client, ctx, "read.timetable_page")
    response = await client.request_operation(
        "read.timetable",
        semester_data_params(ctx, semester_id),
    )
    ensure_ok(response, operation_id="read.timetable")
    return parse_courses(response.text, semester_id)
