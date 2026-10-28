"""Session store encryption tests."""

from __future__ import annotations

from pathlib import Path

from cryptography.fernet import Fernet

from vtop_mcp.config import Settings
from vtop_mcp.vtop.auth.session_store import SessionData, SessionStore


def test_session_round_trip(tmp_path: Path) -> None:
    key = Fernet.generate_key().decode()
    settings = Settings(
        session_file=tmp_path / "session.enc",
        session_key_env=key,
    )
    store = SessionStore(settings)
    original = SessionData(
        cookies=[{"name": "JSESSIONID", "value": "abc", "domain": "vtop.vit.ac.in", "path": "/vtop"}],
        regno="21BCE0000",
        authenticated=True,
    )
    store.save(original)
    loaded = store.load()
    assert loaded is not None
    assert loaded.regno == "21BCE0000"
    assert loaded.authenticated is True
    assert loaded.cookies[0]["name"] == "JSESSIONID"


def test_session_clear(tmp_path: Path) -> None:
    key = Fernet.generate_key().decode()
    path = tmp_path / "session.enc"
    settings = Settings(session_file=path, session_key_env=key)
    store = SessionStore(settings)
    store.save(SessionData(cookies=[]))
    assert path.is_file()
    store.clear()
    assert not path.is_file()
