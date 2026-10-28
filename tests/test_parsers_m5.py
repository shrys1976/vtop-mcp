"""Parser tests for M5 services."""

from __future__ import annotations

from pathlib import Path

from vtop_mcp.parsers.profile import parse_profile
from vtop_mcp.parsers.semesters import parse_semesters


def test_parse_semesters_fixture() -> None:
    html = Path("tests/fixtures/responses/semesters.html").read_text()
    result = parse_semesters(html)
    assert len(result.semesters) == 2
    assert result.semesters[0].id == "VL2025261"
    assert result.semesters[0].active is True


def test_parse_profile_fixture_masks_email() -> None:
    html = Path("tests/fixtures/responses/profile.html").read_text()
    profile = parse_profile(html)
    assert profile.regno == "21BCE0000"
    assert profile.name == "Sample Student"
    assert profile.email is not None
    assert "@" in profile.email
    assert "sample.student" not in profile.email
