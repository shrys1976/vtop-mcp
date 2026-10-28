"""Parse proctor details HTML."""

from __future__ import annotations

from bs4 import BeautifulSoup

from vtop_mcp.models.proctor import ProctorDetails
from vtop_mcp.parsers._common import cell_text


def parse_proctor(html: str) -> ProctorDetails:
    soup = BeautifulSoup(html, "html.parser")
    form = soup.find("form", id="viewProctorDetailsForm") or soup
    pairs: dict[str, str] = {}
    for tr in form.find_all("tr"):
        cells = [c for c in tr.find_all("td") if not c.find("img")]
        if len(cells) < 2:
            continue
        key = cell_text(cells[0]).lower()
        val = cell_text(cells[1])
        if key and val:
            pairs[key] = val

    def pick(*fragments: str) -> str | None:
        for label, value in pairs.items():
            if any(f in label for f in fragments):
                return value
        return None

    return ProctorDetails(
        faculty_id=pick("faculty id"),
        name=pick("faculty name"),
        designation=pick("faculty designation", "designation"),
        school=pick("school"),
        cabin=pick("cabin"),
        department=pick("department"),
        email=pick("email"),
        intercom=pick("intercom"),
        mobile=pick("mobile"),
    )
