"""Domain errors for VTOP MCP."""

from __future__ import annotations


class VtopMcpError(Exception):
    """Base error."""


class HostNotAllowedError(VtopMcpError):
    """Request URL is outside the allowlisted VTOP host."""


class UnexpectedRedirectError(VtopMcpError):
    """Redirect target is off-host or redirect loop exceeded."""
