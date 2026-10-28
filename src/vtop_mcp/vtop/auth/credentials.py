"""Load VTOP credentials from environment or OS keyring."""

from __future__ import annotations

import json
import logging

from keyring.errors import KeyringError

from vtop_mcp.config import Settings
from vtop_mcp.exceptions import CredentialsMissingError
from vtop_mcp.vtop.auth.session_store import KEYRING_SERVICE

logger = logging.getLogger(__name__)

CREDENTIALS_KEYRING_USER = "credentials"


def load_credentials(settings: Settings) -> tuple[str, str]:
    """Return (regno, password)."""
    if settings.regno and settings.password:
        return settings.regno.strip().upper(), settings.password

    import keyring

    try:
        raw = keyring.get_password(KEYRING_SERVICE, CREDENTIALS_KEYRING_USER)
    except KeyringError:
        raw = None

    if raw:
        try:
            payload = json.loads(raw)
            regno = str(payload["regno"]).strip().upper()
            password = str(payload["password"])
            return regno, password
        except (KeyError, TypeError, json.JSONDecodeError):
            logger.warning("Invalid credentials JSON in keyring")

    raise CredentialsMissingError(
        "Set VTOP_REGNO and VTOP_PASSWORD, or store credentials in keyring "
        f"({KEYRING_SERVICE}/{CREDENTIALS_KEYRING_USER} JSON)."
    )
