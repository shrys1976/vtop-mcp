"""Encrypted on-disk session persistence."""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from datetime import UTC, datetime
from http.cookiejar import Cookie
from pathlib import Path
from typing import Any

from cryptography.fernet import Fernet, InvalidToken
from keyring.errors import KeyringError

from vtop_mcp.config import Settings

logger = logging.getLogger(__name__)

KEYRING_SERVICE = "vtop-mcp"
KEYRING_USERNAME = "session-key"


@dataclass
class SessionData:
    """Persisted session payload (cookies + metadata)."""

    cookies: list[dict[str, Any]] = field(default_factory=list)
    saved_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    regno: str | None = None
    authenticated: bool = False

    def to_json_dict(self) -> dict[str, Any]:
        return {
            "cookies": self.cookies,
            "saved_at": self.saved_at.isoformat(),
            "regno": self.regno,
            "authenticated": self.authenticated,
        }

    @classmethod
    def from_json_dict(cls, payload: dict[str, Any]) -> SessionData:
        saved_raw = payload.get("saved_at")
        saved_at = (
            datetime.fromisoformat(saved_raw)
            if isinstance(saved_raw, str)
            else datetime.now(UTC)
        )
        return cls(
            cookies=list(payload.get("cookies") or []),
            saved_at=saved_at,
            regno=payload.get("regno"),
            authenticated=bool(payload.get("authenticated")),
        )


def serialize_cookies(jar: Any) -> list[dict[str, Any]]:
    """Serialize http.cookiejar cookies for storage."""
    items: list[dict[str, Any]] = []
    for cookie in jar:
        if not isinstance(cookie, Cookie):
            continue
        items.append(
            {
                "name": cookie.name,
                "value": cookie.value,
                "domain": cookie.domain,
                "path": cookie.path or "/",
                "secure": bool(cookie.secure),
            }
        )
    return items


def apply_cookies_to_jar(jar: Any, cookies: list[dict[str, Any]]) -> None:
    """Restore cookies into a cookie jar."""
    for item in cookies:
        jar.set_cookie(
            Cookie(
                version=0,
                name=item["name"],
                value=item["value"],
                port=None,
                port_specified=False,
                domain=item.get("domain") or "",
                domain_specified=bool(item.get("domain")),
                domain_initial_dot=item.get("domain", "").startswith("."),
                path=item.get("path") or "/",
                path_specified=True,
                secure=bool(item.get("secure")),
                expires=None,
                discard=True,
                comment=None,
                comment_url=None,
                rest={"HttpOnly": None},
                rfc2109=False,
            )
        )


class SessionStore:
    """Encrypt and persist session data using Fernet + OS keyring."""

    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self._path = settings.session_file
        self._fernet_key: str | None = None

    def _fernet(self) -> Fernet:
        if self._fernet_key is None:
            if self._settings.session_key_env:
                self._fernet_key = self._settings.session_key_env
            else:
                self._fernet_key = _load_or_create_keyring_key()
        return Fernet(self._fernet_key.encode())

    def load(self) -> SessionData | None:
        if not self._path.is_file():
            return None
        raw = self._path.read_bytes()
        try:
            plaintext = self._fernet().decrypt(raw)
        except InvalidToken:
            logger.warning("Session file decrypt failed; ignoring stored session")
            return None
        payload = json.loads(plaintext.decode("utf-8"))
        return SessionData.from_json_dict(payload)

    def save(self, data: SessionData) -> None:
        self._path.parent.mkdir(parents=True, exist_ok=True)
        plaintext = json.dumps(data.to_json_dict()).encode("utf-8")
        token = self._fernet().encrypt(plaintext)
        self._path.write_bytes(token)

    def clear(self) -> None:
        if self._path.is_file():
            self._path.unlink()


def _load_or_create_keyring_key() -> str:
    import keyring

    try:
        existing = keyring.get_password(KEYRING_SERVICE, KEYRING_USERNAME)
    except KeyringError:
        logger.warning("Keyring unavailable; generating ephemeral session key")
        return Fernet.generate_key().decode()

    if existing:
        return existing

    created = Fernet.generate_key().decode()
    try:
        keyring.set_password(KEYRING_SERVICE, KEYRING_USERNAME, created)
    except KeyringError:
        logger.warning("Could not persist session key to keyring")
    return created
