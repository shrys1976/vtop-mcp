"""Attendance service."""

from __future__ import annotations

from vtop_mcp.models.attendance import AttendanceList
from vtop_mcp.parsers.attendance import parse_attendance
from vtop_mcp.services._semester import with_semester
from vtop_mcp.services.bootstrap import AuthContext
from vtop_mcp.vtop.client import VtopHttpClient


async def fetch_attendance(
    client: VtopHttpClient,
    ctx: AuthContext,
    semester_id: str,
) -> AttendanceList:
    response = await client.request_operation(
        "read.attendance",
        with_semester(ctx, semester_id),
    )
    return parse_attendance(response.text, semester_id)
