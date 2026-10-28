"""Spotlight announcement models."""

from __future__ import annotations

from pydantic import BaseModel


class SpotlightItem(BaseModel):
    title: str
    category: str | None = None
    file_id: str | None = None
    download_path: str | None = None
    url: str | None = None


class SpotlightList(BaseModel):
    items: list[SpotlightItem]
