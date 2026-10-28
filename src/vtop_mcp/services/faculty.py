"""Faculty search service."""

from __future__ import annotations

from vtop_mcp.exceptions import VtopMcpError
from vtop_mcp.models.faculty import FacultySearchResult
from vtop_mcp.parsers.faculty import parse_faculty_detail, parse_faculty_search_results
from vtop_mcp.services._http_helpers import (
    ensure_ok,
    faculty_detail_params,
    faculty_search_params,
    post_menu_shell,
)
from vtop_mcp.services.bootstrap import AuthContext
from vtop_mcp.vtop.client import VtopHttpClient


class FacultyQueryTooShortError(VtopMcpError):
    """Search text must be at least three characters."""


async def fetch_faculty(
    client: VtopHttpClient,
    ctx: AuthContext,
    query: str,
    employee_id: str | None = None,
) -> FacultySearchResult:
    if employee_id:
        response = await client.request_operation(
            "read.faculty_detail",
            faculty_detail_params(ctx, employee_id),
        )
        ensure_ok(response, operation_id="read.faculty_detail")
        detail = parse_faculty_detail(response.text, employee_id)
        return FacultySearchResult(query=query, detail=detail)

    trimmed = query.strip()
    if len(trimmed) < 3:
        raise FacultyQueryTooShortError(
            "Faculty search requires at least 3 characters."
        )
    await post_menu_shell(client, ctx, "read.faculty_search_page")
    response = await client.request_operation(
        "read.faculty_search",
        faculty_search_params(ctx, trimmed),
    )
    ensure_ok(response, operation_id="read.faculty_search")
    return parse_faculty_search_results(response.text, trimmed)
