"""Parse spotlight announcements from HTML."""

from __future__ import annotations

import re

from bs4 import BeautifulSoup

from vtop_mcp.models.spotlight import SpotlightItem, SpotlightList
from vtop_mcp.parsers._common import cell_text


def parse_spotlight(html: str) -> SpotlightList:
    soup = BeautifulSoup(html, "html.parser")
    items: list[SpotlightItem] = []
    seen: set[tuple[str, str | None, str | None]] = set()
    current_category: str | None = None

    for element in soup.find_all(["h4", "h5", "h6", "strong", "a"]):
        if element.name in ("h4", "h5", "h6", "strong"):
            text = cell_text(element)
            if text and len(text) < 40:
                current_category = text
            continue
        if element.name != "a":
            continue
        title_tag = element.find("span")
        title = cell_text(title_tag or element)
        if not title:
            continue
        onclick = element.get("onclick") or ""
        href = element.get("href") or ""
        file_id = None
        download_path = None
        url = None
        match = re.search(
            r"downloadSpotLightViewFile/(\d+)|vtopDownload\s*\(\s*['\"]downloadSpotLightViewFile/(\d+)",
            onclick,
            re.I,
        )
        if match:
            file_id = match.group(1) or match.group(2)
            download_path = f"/vtop/downloadSpotLightViewFile/{file_id}"
        elif href and not href.startswith("javascript"):
            url = href
        elif "spotlight" not in title.lower() and not file_id:
            continue
        key = (title, file_id, url)
        if key in seen:
            continue
        seen.add(key)
        items.append(
            SpotlightItem(
                title=title,
                category=current_category,
                file_id=file_id,
                download_path=download_path,
                url=url,
            )
        )
    return SpotlightList(items=items)
