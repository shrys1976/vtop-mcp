"""Parse spotlight announcements from HTML."""

from __future__ import annotations

import re

from bs4 import BeautifulSoup

from vtop_mcp.models.spotlight import SpotlightItem, SpotlightList


def parse_spotlight(html: str) -> SpotlightList:
    soup = BeautifulSoup(html, "html.parser")
    items: list[SpotlightItem] = []
    seen: set[str] = set()
    for anchor in soup.find_all("a"):
        onclick = anchor.get("onclick") or ""
        title = anchor.get_text(" ", strip=True)
        if not title:
            continue
        match = re.search(r"downloadSpotLightViewFile/(\d+)", onclick)
        file_id = match.group(1) if match else None
        if file_id is None and "spotlight" not in title.lower():
            continue
        key = file_id or title
        if key in seen:
            continue
        seen.add(key)
        download_path = f"/vtop/downloadSpotLightViewFile/{file_id}" if file_id else None
        items.append(
            SpotlightItem(title=title, file_id=file_id, download_path=download_path)
        )
    return SpotlightList(items=items)
