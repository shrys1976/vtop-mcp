"""Shared semester-scoped request params."""

from __future__ import annotations

from vtop_mcp.services.bootstrap import AuthContext, auth_post_params
from vtop_mcp.vtop.constants import FIELD_SEMESTER_SUB_ID


def with_semester(ctx: AuthContext, semester_id: str) -> dict[str, str]:
    params = auth_post_params(ctx)
    params[FIELD_SEMESTER_SUB_ID] = semester_id
    return params
