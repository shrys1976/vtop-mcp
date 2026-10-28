"""Parse HOD and Dean HTML."""

from __future__ import annotations

from bs4 import BeautifulSoup, Tag

from vtop_mcp.models.hod_dean import HodDeanInfo, OfficialContact
from vtop_mcp.parsers._common import cell_text


def _parse_block(table: Tag, role: str) -> OfficialContact:
    pairs: dict[str, str] = {}
    for tr in table.find_all("tr"):
        cells = [c for c in tr.find_all("td") if not c.find("img")]
        if len(cells) < 2:
            continue
        key = cell_text(cells[0]).lower()
        val = cell_text(cells[1])
        if key and val:
            pairs[key] = val
    return OfficialContact(
        role=role,
        name=pairs.get("name of the faculty"),
        designation=pairs.get("designation"),
        cabin=pairs.get("cabin number"),
        email=pairs.get("email id"),
    )


def parse_hod_dean(html: str) -> HodDeanInfo:
    soup = BeautifulSoup(html, "html.parser")
    dean: OfficialContact | None = None
    hod: OfficialContact | None = None
    for header in soup.find_all("h3", class_="box-title"):
        title = cell_text(header).upper()
        table = header.find_parent("div").find_next("table") if header.find_parent("div") else None
        if table is None:
            table = header.find_next("table")
        if table is None:
            continue
        if "DEAN" in title and "HOD" not in title:
            dean = _parse_block(table, "DEAN")
        elif "HOD" in title or "HEAD OF THE DEPARTMENT" in title:
            hod = _parse_block(table, "HoD")
    if dean is None and hod is None:
        tables = soup.find_all("table")
        if tables:
            dean = _parse_block(tables[0], "DEAN")
        if len(tables) > 1:
            hod = _parse_block(tables[1], "HoD")
    return HodDeanInfo(dean=dean, hod=hod)
