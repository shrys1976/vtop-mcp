"""Academic calendar service."""

from __future__ import annotations

from vtop_mcp.models.calendar import AcademicCalendar
from vtop_mcp.parsers.calendar import (
    calendar_month_header,
    extract_calendar_month_dates,
    parse_calendar_month,
    parse_default_calendar_semester,
)
from vtop_mcp.services._http_helpers import (
    VtopResponseError,
    calendar_class_group_params,
    calendar_month_params,
    calendar_semester_params,
    ensure_ok,
    menu_post_params,
    refresh_csrf_from_html,
)
from vtop_mcp.services.bootstrap import AuthContext
from vtop_mcp.vtop.constants import (
    CLASS_GROUP_GENERAL_LABEL,
    DEFAULT_CLASS_GROUP_GENERAL,
)
from vtop_mcp.vtop.client import VtopHttpClient


async def fetch_academic_calendar(
    client: VtopHttpClient,
    ctx: AuthContext,
    semester_id: str | None = None,
) -> AcademicCalendar:
    preview = await client.request_operation(
        "read.calendar_preview",
        menu_post_params(ctx, client=client),
    )
    if preview.status_code == 404:
        raise VtopResponseError(
            "VTOP calendar page returned HTTP 404; session may have expired. "
            "Call vtop_login again."
        )
    ensure_ok(preview, operation_id="read.calendar_preview")
    await refresh_csrf_from_html(client, preview.text)

    resolved_semester = semester_id or parse_default_calendar_semester(preview.text)
    if not resolved_semester:
        raise VtopResponseError(
            "Could not determine semester from the calendar page. Pass semester_id "
            "from list_semesters (e.g. VL20262701)."
        )

    sem_response = await client.request_operation(
        "read.calendar_semester_dates",
        calendar_semester_params(
            ctx,
            resolved_semester,
            client=client,
        ),
    )
    ensure_ok(sem_response, operation_id="read.calendar_semester_dates")
    await refresh_csrf_from_html(client, sem_response.text)

    group_response = await client.request_operation(
        "read.calendar_list_semester",
        calendar_class_group_params(
            ctx,
            resolved_semester,
            client=client,
        ),
    )
    ensure_ok(group_response, operation_id="read.calendar_list_semester")
    await refresh_csrf_from_html(client, group_response.text)
    month_dates = extract_calendar_month_dates(group_response.text)
    if not month_dates:
        month_dates = extract_calendar_month_dates(sem_response.text)

    if not month_dates:
        raise VtopResponseError(
            "No calendar month buttons found after getDateForSemesterPreview and "
            f"getListForSemester for semester {resolved_semester!r}. "
            f"Check semSubId and that getListForSemester ran with classGroupId=ALL. "
            f"Response sizes: dates={len(sem_response.text)}, "
            f"list={len(group_response.text)}."
        )

    class_group_id = DEFAULT_CLASS_GROUP_GENERAL
    events = []
    parse_failures: list[str] = []
    for cal_date in month_dates:
        response = await client.request_operation(
            "read.calendar_month",
            calendar_month_params(
                ctx,
                cal_date=cal_date,
                sem_sub_id=resolved_semester,
                class_group_id=class_group_id,
                client=client,
            ),
        )
        ensure_ok(response, operation_id="read.calendar_month")
        await refresh_csrf_from_html(client, response.text)
        header = calendar_month_header(response.text)
        month_events = parse_calendar_month(
            response.text,
            cal_date,
            class_group_label=CLASS_GROUP_GENERAL_LABEL,
        )
        if not month_events:
            parse_failures.append(
                f"{cal_date}: header={header!r}, bytes={len(response.text)}, "
                f"has_table={'calendar-table' in response.text}"
            )
        events.extend(month_events)

    if not events and month_dates:
        detail = "; ".join(parse_failures[:3])
        raise VtopResponseError(
            "Calendar months were fetched but no events were parsed. "
            f"If the month header is blank, check semSubId and CSRF. {detail}"
        )

    return AcademicCalendar(
        semester_id=resolved_semester,
        class_group_id=class_group_id,
        class_group_label=CLASS_GROUP_GENERAL_LABEL,
        events=events,
    )
