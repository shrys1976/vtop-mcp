"""Exam schedule service."""

from __future__ import annotations

from vtop_mcp.models.exams import ExamSchedule
from vtop_mcp.parsers.exams import parse_exam_schedule
from vtop_mcp.services._semester import with_semester
from vtop_mcp.services._http_helpers import ensure_ok, post_menu_shell
from vtop_mcp.services.bootstrap import AuthContext, auth_post_params
from vtop_mcp.vtop.client import VtopHttpClient


async def fetch_exam_schedule(
    client: VtopHttpClient,
    ctx: AuthContext,
    semester_id: str | None,
) -> ExamSchedule:
    await post_menu_shell(client, ctx, "read.exam_schedule_page")
    params = auth_post_params(ctx)
    if semester_id:
        params = with_semester(ctx, semester_id)
    response = await client.request_operation("read.exam_schedule", params)
    ensure_ok(response, operation_id="read.exam_schedule")
    return parse_exam_schedule(response.text, semester_id)
