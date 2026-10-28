"""Generic HTML table extraction."""

from __future__ import annotations

from bs4 import BeautifulSoup, Tag


def iter_data_rows(table: Tag) -> list[list[str]]:
    rows: list[list[str]] = []
    for tr in table.find_all("tr"):
        cells = tr.find_all(["td", "th"])
        if not cells:
            continue
        values = [cell.get_text(" ", strip=True) for cell in cells]
        if any(values):
            rows.append(values)
    return rows


def find_tables(html: str) -> list[Tag]:
    soup = BeautifulSoup(html, "html.parser")
    return soup.find_all("table")
