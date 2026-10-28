"""Process-wide VTOP client and login state for MCP tools."""

from __future__ import annotations

from datetime import UTC, datetime

from vtop_mcp.config import Settings
from vtop_mcp.models.profile import Profile
from vtop_mcp.vtop.auth.login import LoginFlow
from vtop_mcp.vtop.client import VtopHttpClient


class VtopApp:
    """Lazy HTTP client + login flow (one MCP server process)."""

    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or Settings()
        self._client: VtopHttpClient | None = None
        self._login: LoginFlow | None = None
        self._profile_cache: Profile | None = None

    @property
    def client(self) -> VtopHttpClient:
        if self._client is None:
            self._client = VtopHttpClient(self.settings)
        return self._client

    @property
    def login_flow(self) -> LoginFlow:
        if self._login is None:
            self._login = LoginFlow(self.client, self.settings)
        return self._login

    @property
    def profile_cache(self) -> Profile | None:
        return self._profile_cache

    def set_profile_cache(self, profile: Profile | None) -> None:
        self._profile_cache = profile

    def session_age_seconds(self) -> float | None:
        saved = self.client.session_data.saved_at
        if not saved:
            return None
        now = datetime.now(UTC)
        if saved.tzinfo is None:
            saved = saved.replace(tzinfo=UTC)
        return (now - saved).total_seconds()

    async def aclose(self) -> None:
        if self._client is not None:
            await self._client.aclose()
            self._client = None
        self._login = None
