"""VTOP Vellore portal URLs and discovery metadata (M1).

All paths are relative to BASE_URL unless noted. Verified against live
``GET /vtop/login`` probing on 2026-10-27; authenticated read paths follow
the shared VIT VTOP platform (to be validated in M4+ integration).
"""

from __future__ import annotations

# --- Transport allowlist (M2/M3 enforce hostname) ---

ALLOWED_HOSTNAME = "vtop.vit.ac.in"
BASE_URL = f"https://{ALLOWED_HOSTNAME}"
VTOP_PREFIX = "/vtop"

# --- Pre-login & session ---

PATH_LOGIN_LANDING = f"{VTOP_PREFIX}/login"
PATH_PRELOGIN_SETUP = f"{VTOP_PREFIX}/prelogin/setup"
PATH_INIT_PAGE = f"{VTOP_PREFIX}/init/page"
PATH_OPEN_PAGE = f"{VTOP_PREFIX}/open/page"
PATH_CONTENT = f"{VTOP_PREFIX}/content"
PATH_HOME = f"{VTOP_PREFIX}/home"
PATH_SESSION_EXPIRED = f"{VTOP_PREFIX}/session/expired/out"

# --- Auth (student login) ---

PATH_LOGIN_SUBMIT = f"{VTOP_PREFIX}/login"
PATH_CAPTCHA_NEW = f"{VTOP_PREFIX}/get/new/captcha"

# Post-login OTP (login flow / new IP)
PATH_GENERATE_OTP = f"{VTOP_PREFIX}/generateOtp"
PATH_VALIDATE_OTP = f"{VTOP_PREFIX}/validateOtp"
PATH_RESEND_OTP = f"{VTOP_PREFIX}/resendOtp"

# Password / userid recovery (never register as MCP write ops in v1)
PATH_FORGOT_USERID_OTP = f"{VTOP_PREFIX}/get/otp/for/forget/userid"
PATH_VALIDATE_USERID_OTP = f"{VTOP_PREFIX}/validate/user/id/otp"
PATH_RESEND_USERID_OTP = f"{VTOP_PREFIX}/resend/otp/for/userid"
PATH_RESET_PASSWORD = f"{VTOP_PREFIX}/resetPassword"
PATH_ALLOW_CHANGE_PASSWORD = f"{VTOP_PREFIX}/allowChangePassword"

# --- Pre-login spotlight (public on landing page) ---

PATH_SPOTLIGHT_DOWNLOAD_TEMPLATE = f"{VTOP_PREFIX}/downloadSpotLightViewFile/{{file_id}}"

# --- Authenticated read endpoints ---

PATH_STUDENT_PROFILE = f"{VTOP_PREFIX}/studentsRecord/StudentProfileAllView"
PATH_SEMESTER_ATTENDANCE_PAGE = f"{VTOP_PREFIX}/academics/common/StudentAttendance"
PATH_PROCESS_ATTENDANCE = f"{VTOP_PREFIX}/processViewStudentAttendance"
PATH_PROCESS_ATTENDANCE_DETAIL = f"{VTOP_PREFIX}/processViewAttendanceDetail"
PATH_STUDENT_TIMETABLE_PAGE = f"{VTOP_PREFIX}/academics/common/StudentTimeTable"
PATH_PROCESS_TIMETABLE = f"{VTOP_PREFIX}/processViewTimeTable"
PATH_STUDENT_MARKS_PAGE = f"{VTOP_PREFIX}/examinations/StudentMarkView"
PATH_STUDENT_MARKS = f"{VTOP_PREFIX}/examinations/doStudentMarkView"
PATH_EXAM_SCHEDULE_PAGE = f"{VTOP_PREFIX}/examinations/StudExamSchedule"
PATH_EXAM_SCHEDULE = f"{VTOP_PREFIX}/examinations/doSearchExamScheduleForStudent"
PATH_GRADE_VIEW_PAGE = f"{VTOP_PREFIX}/examinations/examGradeView/StudentGradeView"
PATH_GRADE_VIEW_DATA = f"{VTOP_PREFIX}/examinations/examGradeView/doStudentGradeView"
PATH_GRADE_HISTORY = f"{VTOP_PREFIX}/examinations/examGradeView/StudentGradeHistory"
PATH_STUDENT_COURSE_PAGE = f"{VTOP_PREFIX}/academics/common/StudentCoursePage"
PATH_COURSE_PAGE_CONSOLIDATED = f"{VTOP_PREFIX}/academics/common/CoursePageConsolidated"
PATH_COURSE_PAGE_SEMESTERS = f"{VTOP_PREFIX}/getCourseForCoursePage"
PATH_COURSE_PAGE_SLOTS = f"{VTOP_PREFIX}/getSlotIdForCoursePage"
PATH_PROCESS_COURSE_DETAIL = f"{VTOP_PREFIX}/processViewStudentCourseDetail"
PATH_CURRICULUM = f"{VTOP_PREFIX}/academics/common/Curriculum"

PATH_CALENDAR_PREVIEW = f"{VTOP_PREFIX}/academics/common/CalendarPreview"
PATH_CALENDAR_SEMESTER_DATES = f"{VTOP_PREFIX}/getDateForSemesterPreview"
PATH_PROCESS_CALENDAR = f"{VTOP_PREFIX}/processViewCalendar"

PATH_HOD_DEAN = f"{VTOP_PREFIX}/hrms/viewHodDeanDetails"
PATH_FACULTY_SEARCH_PAGE = f"{VTOP_PREFIX}/hrms/employeeSearchForStudent"
PATH_FACULTY_SEARCH = f"{VTOP_PREFIX}/hrms/EmployeeSearchForStudent"
PATH_FACULTY_DETAIL = f"{VTOP_PREFIX}/hrms/EmployeeSearch1ForStudent"
PATH_PROCTOR = f"{VTOP_PREFIX}/proctor/viewProctorDetails"

# --- Form / JSON field names (login & session) ---

FIELD_CSRF = "_csrf"
FIELD_PRELOGIN_FLAG = "flag"
PRELOGIN_FLAG_STUDENT = "VTOP"

FIELD_USERNAME = "username"
FIELD_PASSWORD = "password"
FIELD_CAPTCHA = "captchaStr"
FIELD_GOOGLE_RECAPTCHA = "g-recaptcha-response"

FIELD_AUTHORIZED_ID = "authorizedID"
FIELD_SEMESTER_SUB_ID = "semesterSubId"
FIELD_SEM_SUB_ID = "semSubId"
FIELD_VERIFY_MENU = "verifyMenu"
FIELD_NOCACHE = "nocache"
FIELD_X = "x"
FIELD_CAL_DATE = "calDate"
FIELD_CLASS_GROUP_ID = "classGroupId"
FIELD_EMP_ID = "empId"

NOCACHE_LITERAL = "@(new Date().getTime())"
DEFAULT_CLASS_GROUP_COMBINED = "COMB"

# --- Cookies ---

COOKIE_JSESSIONID = "JSESSIONID"
COOKIE_SERVERID = "SERVERID"

# --- Captcha modes (from /vtop/init/page inline JS) ---

CAPTCHA_TYPE_BUILTIN = 1
CAPTCHA_TYPE_GOOGLE = 2

# --- HTTP client defaults ---

DEFAULT_USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/120.0.0.0 Safari/537.36"
)
DEFAULT_MAX_CAPTCHA_RETRIES = 2
DEFAULT_MAX_RECAPTCHA_REFRESHES = 60

# --- Permanent v1 exclusions (audit list for operations.py in M3) ---

EXCLUDED_PATH_PATTERNS = (
    "registration",
    "payment",
    "saveOuting",
    "resetPassword",
    "allowChangePassword",
    "processRegistration",
)
