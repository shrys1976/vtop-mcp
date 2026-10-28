"""Academic calendar service."""

from __future__ import annotations

from vtop_mcp.models.calendar import AcademicCalendar
from vtop_mcp.parsers.calendar import parse_academic_calendar
from vtop_mcp.services._semester import with_semester
from vtop_mcp.services.bootstrap import AuthContext, auth_post_params
from vtop_mcp.vtop.client import VtopHttpClient


async def fetch_academic_calendar(
    client: VtopHttpClient,
    ctx: AuthContext,
    semester_id: str | None,
) -> AcademicCalendar:
    params = auth_post_params(ctx)
    if semester_id:
        params = with_semester(ctx, semester_id)
    response = await client.request_operation("read.academic_calendar", params)
    return parse_academic_calendar(response.text, semester_id)
