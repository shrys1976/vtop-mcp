"""Attendance service."""

from __future__ import annotations

from vtop_mcp.models.attendance import AttendanceList
from vtop_mcp.parsers.attendance import parse_attendance
from vtop_mcp.services._http_helpers import (
    ensure_ok,
    post_menu_shell,
    semester_data_params,
)
from vtop_mcp.services.bootstrap import AuthContext
from vtop_mcp.vtop.client import VtopHttpClient


async def fetch_attendance(
    client: VtopHttpClient,
    ctx: AuthContext,
    semester_id: str,
) -> AttendanceList:
    await post_menu_shell(client, ctx, "read.semester_list_page")
    response = await client.request_operation(
        "read.attendance",
        semester_data_params(ctx, semester_id),
    )
    ensure_ok(response, operation_id="read.attendance")
    return parse_attendance(response.text, semester_id)
