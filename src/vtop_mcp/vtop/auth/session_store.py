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
    authorized_id: str | None = None
    csrf: str | None = None

    def to_json_dict(self) -> dict[str, Any]:
        return {
            "cookies": self.cookies,
            "saved_at": self.saved_at.isoformat(),
            "regno": self.regno,
            "authenticated": self.authenticated,
            "authorized_id": self.authorized_id,
            "csrf": self.csrf,
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
            authorized_id=payload.get("authorized_id"),
            csrf=payload.get("csrf"),
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
                self._fernet_key = self._load_or_create_key()
        return Fernet(self._fernet_key.encode())

    def _load_or_create_key(self) -> str:
        """Prefer the OS keyring, and mirror the key to disk for headless WSL."""
        key_path = self._settings.session_file.parent / "session.key"
        keyring_key = _read_keyring_key()
        if keyring_key:
            _write_key_file(key_path, keyring_key)
            return keyring_key
        if key_path.is_file():
            stored = key_path.read_text(encoding="utf-8").strip()
            if stored:
                return stored
        created = Fernet.generate_key().decode()
        _write_keyring_key(created)
        _write_key_file(key_path, created)
        return created

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


def _read_keyring_key() -> str | None:
    import keyring

    try:
        return keyring.get_password(KEYRING_SERVICE, KEYRING_USERNAME)
    except KeyringError:
        logger.info("OS keyring unavailable; using the on-disk session key")
        return None


def _write_keyring_key(key: str) -> None:
    import keyring

    try:
        keyring.set_password(KEYRING_SERVICE, KEYRING_USERNAME, key)
    except KeyringError:
        logger.info("Could not store the session key in the OS keyring")


def _write_key_file(path: Path, key: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(key, encoding="utf-8")
    try:
        path.chmod(0o600)
    except OSError:
        logger.info("Could not restrict permissions on %s", path)
