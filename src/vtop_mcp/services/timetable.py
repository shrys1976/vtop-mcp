"""Timetable service."""

from __future__ import annotations

from vtop_mcp.models.timetable import Timetable
from vtop_mcp.parsers.timetable import parse_timetable
from vtop_mcp.services._semester import with_semester
from vtop_mcp.services.bootstrap import AuthContext
from vtop_mcp.vtop.client import VtopHttpClient


async def fetch_timetable(
    client: VtopHttpClient,
    ctx: AuthContext,
    semester_id: str,
) -> Timetable:
    response = await client.request_operation(
        "read.timetable",
        with_semester(ctx, semester_id),
    )
    return parse_timetable(response.text, semester_id)
