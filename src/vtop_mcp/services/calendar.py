"""Academic calendar service."""

from __future__ import annotations

from vtop_mcp.models.calendar import AcademicCalendar
from vtop_mcp.parsers.calendar import (
    extract_calendar_month_dates,
    parse_calendar_month,
)
from vtop_mcp.services._http_helpers import (
    VtopResponseError,
    calendar_month_params,
    calendar_semester_params,
    ensure_ok,
    menu_post_params,
    refresh_csrf_from_html,
)
from vtop_mcp.services.bootstrap import AuthContext
from vtop_mcp.vtop.constants import DEFAULT_CLASS_GROUP_GENERAL
from vtop_mcp.vtop.client import VtopHttpClient


async def fetch_academic_calendar(
    client: VtopHttpClient,
    ctx: AuthContext,
    semester_id: str | None,
    *,
    class_group_id: str = DEFAULT_CLASS_GROUP_GENERAL,
) -> AcademicCalendar:
    if not semester_id:
        raise VtopResponseError(
            "semester_id is required. Call list_semesters and pass semester_id "
            "(e.g. VL20262701)."
        )

    preview = await client.request_operation(
        "read.calendar_preview",
        menu_post_params(ctx),
    )
    if preview.status_code == 404:
        raise VtopResponseError(
            "VTOP calendar page returned HTTP 404; session may have expired. "
            "Call vtop_login again."
        )
    ensure_ok(preview, operation_id="read.calendar_preview")
    await refresh_csrf_from_html(client, preview.text)

    sem_response = await client.request_operation(
        "read.calendar_semester_dates",
        calendar_semester_params(ctx, semester_id),
    )
    ensure_ok(sem_response, operation_id="read.calendar_semester_dates")
    month_dates = extract_calendar_month_dates(sem_response.text)
    if not month_dates:
        month_dates = extract_calendar_month_dates(preview.text)

    if not month_dates:
        return AcademicCalendar(
            semester_id=semester_id,
            class_group_id=class_group_id,
            events=[],
        )

    events = []
    for cal_date in month_dates:
        response = await client.request_operation(
            "read.calendar_month",
            calendar_month_params(
                ctx,
                cal_date=cal_date,
                sem_sub_id=semester_id,
                class_group_id=class_group_id,
            ),
        )
        ensure_ok(response, operation_id="read.calendar_month")
        events.extend(parse_calendar_month(response.text, cal_date))

    return AcademicCalendar(
        semester_id=semester_id,
        class_group_id=class_group_id,
        events=events,
    )
