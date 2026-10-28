"""Shared MCP tool helpers."""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from typing import Any, TypeVar

from pydantic import BaseModel

from vtop_mcp.app_state import VtopApp
from vtop_mcp.mcp_tools import err_payload, ok_payload
from vtop_mcp.services.bootstrap import NotAuthenticatedError, resolve_auth_context

T = TypeVar("T", bound=BaseModel)


async def with_auth(
    app: VtopApp,
    handler: Callable[..., Awaitable[T]],
    *args: str,
) -> dict[str, Any]:
    try:
        ctx = await resolve_auth_context(app.client)
        result = await handler(app.client, ctx, *args)
    except NotAuthenticatedError as exc:
        return err_payload("not_authenticated", str(exc))
    return ok_payload(result)
