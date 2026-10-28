"""Academic calendar service."""

from __future__ import annotations

from vtop_mcp.models.calendar import AcademicCalendar
from vtop_mcp.parsers.calendar import (
    extract_calendar_month_dates,
    parse_calendar_month,
)
from vtop_mcp.services._http_helpers import (
    calendar_month_params,
    ensure_ok,
    post_menu_shell,
)
from vtop_mcp.services.bootstrap import AuthContext, auth_post_params
from vtop_mcp.vtop.constants import FIELD_SEM_SUB_ID
from vtop_mcp.vtop.client import VtopHttpClient


async def fetch_academic_calendar(
    client: VtopHttpClient,
    ctx: AuthContext,
    semester_id: str | None,
) -> AcademicCalendar:
    preview = await post_menu_shell(client, ctx, "read.calendar_preview")
    month_dates = extract_calendar_month_dates(preview.text)
    if semester_id:
        sem_params = auth_post_params(ctx)
        sem_params[FIELD_SEM_SUB_ID] = semester_id
        sem_response = await client.request_operation(
            "read.calendar_semester_dates",
            sem_params,
        )
        ensure_ok(sem_response, operation_id="read.calendar_semester_dates")
        month_dates = extract_calendar_month_dates(sem_response.text) or month_dates

    if not month_dates:
        return AcademicCalendar(semester_id=semester_id, events=[])

    if not semester_id:
        return AcademicCalendar(semester_id=semester_id, events=[])

    events = []
    for cal_date in month_dates:
        response = await client.request_operation(
            "read.calendar_month",
            calendar_month_params(ctx, cal_date=cal_date, sem_sub_id=semester_id),
        )
        ensure_ok(response, operation_id="read.calendar_month")
        events.extend(parse_calendar_month(response.text, cal_date))

    return AcademicCalendar(semester_id=semester_id, events=events)
