"""Authenticated VTOP POST helpers."""

from __future__ import annotations

from datetime import UTC, datetime
from email.utils import format_datetime

import httpx

from vtop_mcp.exceptions import VtopMcpError
from vtop_mcp.parsers.calendar import normalize_cal_date
from vtop_mcp.services.bootstrap import AuthContext, auth_post_params
from vtop_mcp.vtop.constants import (
    CALENDAR_PARAM_RETURN_GET_DATES,
    CALENDAR_PARAM_RETURN_LIST_SEMESTER,
    DEFAULT_CLASS_GROUP_GENERAL,
    FIELD_CAL_DATE,
    FIELD_CLASS_GROUP_ID,
    FIELD_EMP_ID,
    FIELD_NOCACHE,
    FIELD_PARAM_RETURN_ID,
    FIELD_SEMESTER_SUB_ID,
    FIELD_SEM_SUB_ID,
    FIELD_VERIFY_MENU,
    FIELD_X,
    NOCACHE_LITERAL,
)
from vtop_mcp.vtop.html_parse import extract_csrf, page_has_login_form
from vtop_mcp.vtop.client import VtopHttpClient


class VtopResponseError(VtopMcpError):
    """VTOP returned an unexpected HTTP status or login page."""


def gmt_x_header() -> str:
    return format_datetime(datetime.now(UTC), usegmt=True)


def menu_post_params(
    ctx: AuthContext,
    *,
    client: VtopHttpClient | None = None,
) -> dict[str, str]:
    params = auth_post_params(ctx, client=client)
    params[FIELD_VERIFY_MENU] = "true"
    params[FIELD_NOCACHE] = NOCACHE_LITERAL
    return params


def semester_data_params(ctx: AuthContext, semester_id: str) -> dict[str, str]:
    params = auth_post_params(ctx)
    params[FIELD_SEMESTER_SUB_ID] = semester_id
    params[FIELD_X] = gmt_x_header()
    return params


def calendar_semester_params(
    ctx: AuthContext,
    sem_sub_id: str,
    *,
    client: VtopHttpClient | None = None,
) -> dict[str, str]:
    params = auth_post_params(ctx, client=client)
    params[FIELD_SEM_SUB_ID] = sem_sub_id
    params[FIELD_PARAM_RETURN_ID] = CALENDAR_PARAM_RETURN_GET_DATES
    params[FIELD_X] = gmt_x_header()
    return params


def calendar_class_group_params(
    ctx: AuthContext,
    sem_sub_id: str,
    *,
    class_group_id: str = DEFAULT_CLASS_GROUP_GENERAL,
    client: VtopHttpClient | None = None,
) -> dict[str, str]:
    params = auth_post_params(ctx, client=client)
    params[FIELD_SEM_SUB_ID] = sem_sub_id
    params[FIELD_CLASS_GROUP_ID] = class_group_id
    params[FIELD_PARAM_RETURN_ID] = CALENDAR_PARAM_RETURN_LIST_SEMESTER
    params[FIELD_X] = gmt_x_header()
    return params


def calendar_month_params(
    ctx: AuthContext,
    *,
    cal_date: str,
    sem_sub_id: str,
    class_group_id: str = DEFAULT_CLASS_GROUP_GENERAL,
    client: VtopHttpClient | None = None,
) -> dict[str, str]:
    params = auth_post_params(ctx, client=client)
    params[FIELD_CAL_DATE] = normalize_cal_date(cal_date)
    params[FIELD_SEM_SUB_ID] = sem_sub_id
    params[FIELD_CLASS_GROUP_ID] = class_group_id
    params[FIELD_X] = gmt_x_header()
    return params


def faculty_search_params(ctx: AuthContext, query: str) -> dict[str, str]:
    params = auth_post_params(ctx)
    params[FIELD_EMP_ID] = query
    params[FIELD_X] = gmt_x_header()
    return params


def faculty_detail_params(ctx: AuthContext, employee_id: str) -> dict[str, str]:
    params = auth_post_params(ctx)
    params[FIELD_EMP_ID] = employee_id
    params[FIELD_X] = gmt_x_header()
    return params


def ensure_ok(response: httpx.Response, *, operation_id: str) -> None:
    if response.status_code != 200:
        msg = (
            f"VTOP {operation_id} returned HTTP {response.status_code} "
            f"(expected 200)."
        )
        raise VtopResponseError(msg)
    if page_has_login_form(response.text):
        raise VtopResponseError(
            f"VTOP {operation_id} returned the login page; session may have expired."
        )


async def refresh_csrf_from_html(client: VtopHttpClient, html: str) -> None:
    token = extract_csrf(html)
    if token:
        client.session_data.csrf = token
        client.persist_session()


async def post_menu_shell(
    client: VtopHttpClient,
    ctx: AuthContext,
    operation_id: str,
) -> httpx.Response:
    response = await client.request_operation(operation_id, menu_post_params(ctx))
    ensure_ok(response, operation_id=operation_id)
    await refresh_csrf_from_html(client, response.text)
    return response
