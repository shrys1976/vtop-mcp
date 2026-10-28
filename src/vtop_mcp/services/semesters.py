"""Semester list service."""

from __future__ import annotations

from vtop_mcp.models.semesters import SemesterList
from vtop_mcp.parsers.semesters import parse_semesters
from vtop_mcp.services.bootstrap import AuthContext, auth_post_params
from vtop_mcp.vtop.client import VtopHttpClient


async def fetch_semesters(client: VtopHttpClient, ctx: AuthContext) -> SemesterList:
    params = auth_post_params(ctx)
    params["verifyMenu"] = "true"
    response = await client.request_operation("read.semester_list_page", params)
    return parse_semesters(response.text)
