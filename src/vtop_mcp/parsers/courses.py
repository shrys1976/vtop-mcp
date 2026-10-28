"""Parse registered courses from timetable course list HTML."""

from __future__ import annotations

from vtop_mcp.models.courses import CourseList
from vtop_mcp.parsers.course_list import parse_course_list


def parse_courses(html: str, semester_id: str) -> CourseList:
    return CourseList(semester_id=semester_id, courses=parse_course_list(html))
