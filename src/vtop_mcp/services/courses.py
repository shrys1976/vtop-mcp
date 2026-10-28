"""Registered courses service."""

from __future__ import annotations

from vtop_mcp.models.courses import CourseList
from vtop_mcp.parsers.courses import parse_courses
from vtop_mcp.services._semester import with_semester
from vtop_mcp.services.bootstrap import AuthContext
from vtop_mcp.vtop.client import VtopHttpClient


async def fetch_courses(
    client: VtopHttpClient,
    ctx: AuthContext,
    semester_id: str,
) -> CourseList:
    response = await client.request_operation(
        "read.course_slots",
        with_semester(ctx, semester_id),
    )
    return parse_courses(response.text, semester_id)
