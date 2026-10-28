"""MCP tool result helpers."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel


def ok_payload(data: BaseModel | dict[str, Any]) -> dict[str, Any]:
    if isinstance(data, BaseModel):
        body = data.model_dump()
    else:
        body = data
    return {"ok": True, **body}


def err_payload(error_code: str, message: str) -> dict[str, Any]:
    return {"ok": False, "error_code": error_code, "message": message}
