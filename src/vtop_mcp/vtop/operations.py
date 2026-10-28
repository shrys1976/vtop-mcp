"""Strict allowlist of VTOP HTTP operations (auth + read only)."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Literal

from vtop_mcp.exceptions import OperationNotAllowedError
from vtop_mcp.vtop.constants import (
    EXCLUDED_PATH_PATTERNS,
    FIELD_AUTHORIZED_ID,
    FIELD_CAL_DATE,
    FIELD_CAPTCHA,
    FIELD_CLASS_GROUP_ID,
    FIELD_CSRF,
    FIELD_EMP_ID,
    FIELD_GOOGLE_RECAPTCHA,
    FIELD_NOCACHE,
    FIELD_PASSWORD,
    FIELD_PRELOGIN_FLAG,
    FIELD_SEMESTER_SUB_ID,
    FIELD_SEM_SUB_ID,
    FIELD_USERNAME,
    FIELD_VERIFY_MENU,
    FIELD_X,
    PATH_CALENDAR_PREVIEW,
    PATH_CALENDAR_SEMESTER_DATES,
    PATH_CAPTCHA_NEW,
    PATH_COURSE_PAGE_CONSOLIDATED,
    PATH_COURSE_PAGE_SEMESTERS,
    PATH_COURSE_PAGE_SLOTS,
    PATH_EXAM_SCHEDULE,
    PATH_EXAM_SCHEDULE_PAGE,
    PATH_FACULTY_DETAIL,
    PATH_FACULTY_SEARCH,
    PATH_FACULTY_SEARCH_PAGE,
    PATH_GENERATE_OTP,
    PATH_GRADE_HISTORY,
    PATH_GRADE_VIEW_DATA,
    PATH_GRADE_VIEW_PAGE,
    PATH_HOD_DEAN,
    PATH_HOME,
    PATH_INIT_PAGE,
    PATH_LOGIN_LANDING,
    PATH_LOGIN_SUBMIT,
    PATH_CONTENT,
    PATH_OPEN_PAGE,
    PATH_PRELOGIN_SETUP,
    PATH_PROCESS_ATTENDANCE,
    PATH_PROCESS_ATTENDANCE_DETAIL,
    PATH_PROCESS_CALENDAR,
    PATH_PROCESS_COURSE_DETAIL,
    PATH_PROCESS_TIMETABLE,
    PATH_PROCTOR,
    PATH_RESEND_OTP,
    PATH_SEMESTER_ATTENDANCE_PAGE,
    PATH_SESSION_EXPIRED,
    PATH_SPOTLIGHT_DOWNLOAD_TEMPLATE,
    PATH_STUDENT_COURSE_PAGE,
    PATH_STUDENT_MARKS,
    PATH_STUDENT_MARKS_PAGE,
    PATH_STUDENT_PROFILE,
    PATH_STUDENT_TIMETABLE_PAGE,
    PATH_VALIDATE_OTP,
)

OperationCategory = Literal["auth", "read"]

_PATH_PARAM_RE = {
    "file_id": re.compile(r"^[0-9]+$"),
    "semesterSubId": re.compile(r"^[A-Za-z0-9_-]+$"),
}


def _assert_path_allowed(path: str) -> None:
    lower = path.lower()
    for pattern in EXCLUDED_PATH_PATTERNS:
        if pattern.lower() in lower:
            msg = f"Path matches excluded pattern {pattern!r}: {path}"
            raise ValueError(msg)


@dataclass(frozen=True, slots=True)
class OperationSpec:
    operation_id: str
    method: str
    path: str
    category: OperationCategory
    query_keys: frozenset[str] = frozenset()
    body_keys: frozenset[str] = frozenset()
    path_param_names: frozenset[str] = frozenset()

    def __post_init__(self) -> None:
        _assert_path_allowed(self.path)
        if self.method not in ("GET", "POST"):
            raise ValueError(f"Unsupported method: {self.method}")


def _op(
    operation_id: str,
    method: str,
    path: str,
    category: OperationCategory,
    *,
    query_keys: frozenset[str] | None = None,
    body_keys: frozenset[str] | None = None,
    path_param_names: frozenset[str] | None = None,
) -> OperationSpec:
    return OperationSpec(
        operation_id=operation_id,
        method=method,
        path=path,
        category=category,
        query_keys=query_keys or frozenset(),
        body_keys=body_keys or frozenset(),
        path_param_names=path_param_names or frozenset(),
    )


_MENU_BODY = frozenset(
    {FIELD_AUTHORIZED_ID, FIELD_CSRF, FIELD_VERIFY_MENU, FIELD_NOCACHE}
)
_AUTH_SEM = frozenset({FIELD_AUTHORIZED_ID, FIELD_CSRF, FIELD_SEMESTER_SUB_ID})
_AUTH_SEM_X = _AUTH_SEM | frozenset({FIELD_X})
_CALENDAR_BODY = frozenset(
    {
        FIELD_AUTHORIZED_ID,
        FIELD_CSRF,
        FIELD_CAL_DATE,
        FIELD_SEM_SUB_ID,
        FIELD_CLASS_GROUP_ID,
        FIELD_X,
    }
)

OPERATIONS: dict[str, OperationSpec] = {
    spec.operation_id: spec
    for spec in (
        _op("auth.login_landing", "GET", PATH_LOGIN_LANDING, "auth"),
        _op(
            "auth.prelogin_setup",
            "POST",
            PATH_PRELOGIN_SETUP,
            "auth",
            body_keys=frozenset({FIELD_CSRF, FIELD_PRELOGIN_FLAG}),
        ),
        _op("auth.init_page", "GET", PATH_INIT_PAGE, "auth"),
        _op("auth.captcha_refresh", "GET", PATH_CAPTCHA_NEW, "auth"),
        _op(
            "auth.login_submit",
            "POST",
            PATH_LOGIN_SUBMIT,
            "auth",
            body_keys=frozenset(
                {
                    FIELD_CSRF,
                    FIELD_USERNAME,
                    FIELD_PASSWORD,
                    FIELD_CAPTCHA,
                    FIELD_GOOGLE_RECAPTCHA,
                }
            ),
        ),
        _op(
            "auth.generate_otp",
            "POST",
            PATH_GENERATE_OTP,
            "auth",
            body_keys=frozenset({FIELD_CSRF, "otp", "username"}),
        ),
        _op(
            "auth.validate_otp",
            "POST",
            PATH_VALIDATE_OTP,
            "auth",
            body_keys=frozenset({FIELD_CSRF, "otp", "otpValue", "username"}),
        ),
        _op(
            "auth.resend_otp",
            "POST",
            PATH_RESEND_OTP,
            "auth",
            body_keys=frozenset({FIELD_CSRF, "username"}),
        ),
        _op(
            "auth.session_expired",
            "POST",
            PATH_SESSION_EXPIRED,
            "auth",
            body_keys=frozenset({FIELD_CSRF}),
        ),
        _op("read.open_page", "GET", PATH_OPEN_PAGE, "read"),
        _op("read.content", "GET", PATH_CONTENT, "read"),
        _op("read.home", "POST", PATH_HOME, "read", body_keys=_MENU_BODY),
        _op("read.attendance_page", "GET", PATH_SEMESTER_ATTENDANCE_PAGE, "read"),
        _op(
            "read.profile",
            "POST",
            PATH_STUDENT_PROFILE,
            "read",
            body_keys=_MENU_BODY,
        ),
        _op(
            "read.semester_list_page",
            "POST",
            PATH_SEMESTER_ATTENDANCE_PAGE,
            "read",
            body_keys=_MENU_BODY,
        ),
        _op(
            "read.attendance",
            "POST",
            PATH_PROCESS_ATTENDANCE,
            "read",
            body_keys=_AUTH_SEM_X,
        ),
        _op(
            "read.attendance_detail",
            "POST",
            PATH_PROCESS_ATTENDANCE_DETAIL,
            "read",
            body_keys=frozenset(
                {
                    FIELD_AUTHORIZED_ID,
                    FIELD_CSRF,
                    FIELD_SEMESTER_SUB_ID,
                    "classId",
                    "slotId",
                }
            ),
        ),
        _op(
            "read.timetable_page",
            "POST",
            PATH_STUDENT_TIMETABLE_PAGE,
            "read",
            body_keys=_MENU_BODY,
        ),
        _op(
            "read.timetable",
            "POST",
            PATH_PROCESS_TIMETABLE,
            "read",
            body_keys=_AUTH_SEM_X,
        ),
        _op(
            "read.marks_page",
            "POST",
            PATH_STUDENT_MARKS_PAGE,
            "read",
            body_keys=_MENU_BODY,
        ),
        _op(
            "read.marks",
            "POST",
            PATH_STUDENT_MARKS,
            "read",
            body_keys=_AUTH_SEM,
        ),
        _op(
            "read.exam_schedule_page",
            "POST",
            PATH_EXAM_SCHEDULE_PAGE,
            "read",
            body_keys=_MENU_BODY,
        ),
        _op(
            "read.exam_schedule",
            "POST",
            PATH_EXAM_SCHEDULE,
            "read",
            body_keys=_AUTH_SEM,
        ),
        _op(
            "read.grade_view_page",
            "POST",
            PATH_GRADE_VIEW_PAGE,
            "read",
            body_keys=_MENU_BODY,
        ),
        _op(
            "read.grade_view",
            "POST",
            PATH_GRADE_VIEW_DATA,
            "read",
            body_keys=_AUTH_SEM,
        ),
        _op(
            "read.grade_history",
            "POST",
            PATH_GRADE_HISTORY,
            "read",
            body_keys=frozenset({FIELD_AUTHORIZED_ID, FIELD_CSRF}),
        ),
        _op(
            "read.course_page",
            "POST",
            PATH_STUDENT_COURSE_PAGE,
            "read",
            body_keys=frozenset({FIELD_AUTHORIZED_ID, FIELD_CSRF}),
        ),
        _op(
            "read.course_page_consolidated",
            "POST",
            PATH_COURSE_PAGE_CONSOLIDATED,
            "read",
            body_keys=_MENU_BODY,
        ),
        _op(
            "read.course_semesters",
            "POST",
            PATH_COURSE_PAGE_SEMESTERS,
            "read",
            body_keys=frozenset({FIELD_AUTHORIZED_ID, FIELD_CSRF}),
        ),
        _op(
            "read.course_slots",
            "POST",
            PATH_COURSE_PAGE_SLOTS,
            "read",
            body_keys=frozenset(
                {FIELD_AUTHORIZED_ID, FIELD_CSRF, FIELD_SEMESTER_SUB_ID}
            ),
        ),
        _op(
            "read.course_detail",
            "POST",
            PATH_PROCESS_COURSE_DETAIL,
            "read",
            body_keys=frozenset(
                {
                    FIELD_AUTHORIZED_ID,
                    FIELD_CSRF,
                    FIELD_SEMESTER_SUB_ID,
                    "slotId",
                    "courseId",
                }
            ),
        ),
        _op(
            "read.calendar_preview",
            "POST",
            PATH_CALENDAR_PREVIEW,
            "read",
            body_keys=_MENU_BODY,
        ),
        _op(
            "read.calendar_semester_dates",
            "POST",
            PATH_CALENDAR_SEMESTER_DATES,
            "read",
            body_keys=frozenset(
                {FIELD_AUTHORIZED_ID, FIELD_CSRF, FIELD_SEM_SUB_ID}
            ),
        ),
        _op(
            "read.calendar_month",
            "POST",
            PATH_PROCESS_CALENDAR,
            "read",
            body_keys=_CALENDAR_BODY,
        ),
        _op(
            "read.hod_dean",
            "POST",
            PATH_HOD_DEAN,
            "read",
            body_keys=_MENU_BODY,
        ),
        _op(
            "read.faculty_search_page",
            "POST",
            PATH_FACULTY_SEARCH_PAGE,
            "read",
            body_keys=_MENU_BODY,
        ),
        _op(
            "read.faculty_search",
            "POST",
            PATH_FACULTY_SEARCH,
            "read",
            body_keys=frozenset(
                {FIELD_AUTHORIZED_ID, FIELD_CSRF, FIELD_EMP_ID, FIELD_X}
            ),
        ),
        _op(
            "read.faculty_detail",
            "POST",
            PATH_FACULTY_DETAIL,
            "read",
            body_keys=frozenset(
                {FIELD_AUTHORIZED_ID, FIELD_CSRF, FIELD_EMP_ID, FIELD_X}
            ),
        ),
        _op(
            "read.proctor",
            "POST",
            PATH_PROCTOR,
            "read",
            body_keys=_MENU_BODY,
        ),
        _op(
            "read.spotlight_download",
            "GET",
            PATH_SPOTLIGHT_DOWNLOAD_TEMPLATE,
            "read",
            path_param_names=frozenset({"file_id"}),
        ),
    )
}


def get_operation(operation_id: str) -> OperationSpec:
    spec = OPERATIONS.get(operation_id)
    if spec is None:
        raise OperationNotAllowedError(f"Unknown operation: {operation_id!r}")
    return spec


def validate_and_split_params(
    spec: OperationSpec,
    params: dict[str, str] | None,
) -> tuple[dict[str, str], dict[str, str], dict[str, str]]:
    """Return (query, body, path_params); reject unknown keys."""
    incoming = dict(params or {})
    allowed = spec.query_keys | spec.body_keys | spec.path_param_names
    extra = set(incoming) - allowed
    if extra:
        raise OperationNotAllowedError(
            f"Disallowed parameters for {spec.operation_id!r}: {sorted(extra)}"
        )

    path_values = {k: incoming[k] for k in spec.path_param_names if k in incoming}
    missing_path = spec.path_param_names - path_values.keys()
    if missing_path:
        raise OperationNotAllowedError(
            f"Missing path parameters for {spec.operation_id!r}: {sorted(missing_path)}"
        )

    for name, value in path_values.items():
        pattern = _PATH_PARAM_RE.get(name)
        if pattern and not pattern.fullmatch(value):
            raise OperationNotAllowedError(
                f"Invalid value for path parameter {name!r}: {value!r}"
            )

    query = {k: incoming[k] for k in spec.query_keys if k in incoming}
    body = {k: incoming[k] for k in spec.body_keys if k in incoming}
    return query, body, path_values


def render_path(spec: OperationSpec, path_params: dict[str, str]) -> str:
    path = spec.path
    for name, value in path_params.items():
        path = path.replace(f"{{{name}}}", value)
    if "{" in path:
        raise OperationNotAllowedError(
            f"Unresolved path template for {spec.operation_id!r}: {path}"
        )
    return path


def is_excluded_write_path(path: str) -> bool:
    """True if path matches a permanent v1 write exclusion."""
    lower = path.lower()
    return any(p.lower() in lower for p in EXCLUDED_PATH_PATTERNS)
