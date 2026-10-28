"""Domain errors for VTOP MCP."""

from __future__ import annotations


class VtopMcpError(Exception):
    """Base error."""


class HostNotAllowedError(VtopMcpError):
    """Request URL is outside the allowlisted VTOP host."""


class UnexpectedRedirectError(VtopMcpError):
    """Redirect target is off-host or redirect loop exceeded."""


class OperationNotAllowedError(VtopMcpError):
    """Operation is unknown or parameters are not allowlisted."""


class CredentialsMissingError(VtopMcpError):
    """VTOP username/password not configured."""


class CaptchaSolveError(VtopMcpError):
    """Built-in captcha OCR failed."""


class RecaptchaOnlyError(VtopMcpError):
    """VTOP kept serving Google reCAPTCHA after retry cap."""


class InvalidCredentialsError(VtopMcpError):
    """VTOP rejected username or password."""
