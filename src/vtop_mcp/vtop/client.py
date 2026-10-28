"""HTTP client for VTOP with hostname and redirect enforcement."""

from __future__ import annotations

import logging
from datetime import UTC, datetime
from typing import Any
from urllib.parse import urljoin, urlparse

import httpx

from vtop_mcp.config import Settings
from vtop_mcp.exceptions import HostNotAllowedError, UnexpectedRedirectError
from vtop_mcp.vtop.operations import (
    get_operation,
    render_path,
    validate_and_split_params,
)
from vtop_mcp.vtop.auth.session_store import (
    SessionData,
    SessionStore,
    apply_cookies_to_jar,
    serialize_cookies,
)
from vtop_mcp.vtop.constants import ALLOWED_HOSTNAME, DEFAULT_USER_AGENT

logger = logging.getLogger(__name__)

REDIRECT_STATUS = {301, 302, 303, 307, 308}


def _browser_headers(method: str, url: str) -> dict[str, str]:
    """Headers VTOP's Spring CSRF check expects on browser form posts."""
    origin = f"https://{ALLOWED_HOSTNAME}"
    path = urlparse(url).path
    if path.endswith("/prelogin/setup"):
        referer = f"{origin}/vtop/login"
    elif path.endswith("/login") and method == "POST":
        referer = f"{origin}/vtop/init/page"
    elif path.endswith(("validateOtp", "generateOtp", "resendOtp")):
        referer = f"{origin}/vtop/init/page"
    elif "/login" in path or path.endswith("/init/page"):
        referer = f"{origin}/vtop/login"
    else:
        referer = f"{origin}/vtop/content"
    headers = {
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
        "Referer": referer,
    }
    if method == "POST":
        headers["Origin"] = origin
    return headers


def assert_allowed_url(url: str, *, allowed_host: str = ALLOWED_HOSTNAME) -> str:
    """Validate URL host; return normalized URL string."""
    parsed = urlparse(url)
    if parsed.scheme not in ("https",):
        raise HostNotAllowedError(f"Only HTTPS URLs are allowed: {url!r}")
    host = (parsed.hostname or "").lower()
    if host != allowed_host.lower():
        raise HostNotAllowedError(
            f"Host {host!r} is not allowlisted (expected {allowed_host!r})"
        )
    return url


def resolve_path(base_url: str, path: str) -> str:
    """Build absolute URL under base_url and enforce hostname."""
    if path.startswith("http://") or path.startswith("https://"):
        return assert_allowed_url(path)
    base = base_url.rstrip("/") + "/"
    joined = urljoin(base, path.lstrip("/"))
    return assert_allowed_url(joined)


class VtopHttpClient:
    """Async HTTP front door to VTOP (M2: transport + session only)."""

    def __init__(
        self,
        settings: Settings,
        *,
        session_store: SessionStore | None = None,
    ) -> None:
        self._settings = settings
        self._store = session_store or SessionStore(settings)
        self._session_meta = SessionData()
        self._client = httpx.AsyncClient(
            headers={"User-Agent": DEFAULT_USER_AGENT},
            timeout=settings.request_timeout_sec,
            verify=True,
            follow_redirects=False,
        )
        self._load_persisted_session()
        if self._session_meta.authenticated and not self._session_meta.authorized_id:
            self._session_meta.authenticated = False
            self.persist_session()

    @property
    def session_data(self) -> SessionData:
        return self._session_meta

    def _load_persisted_session(self) -> None:
        loaded = self._store.load()
        if not loaded:
            return
        self._session_meta = loaded
        apply_cookies_to_jar(self._client.cookies.jar, loaded.cookies)

    def persist_session(self) -> None:
        """Write cookies and metadata to encrypted storage."""
        self._session_meta.cookies = serialize_cookies(self._client.cookies.jar)
        self._session_meta.saved_at = datetime.now(UTC)
        self._store.save(self._session_meta)

    def has_cookie(self, name: str) -> bool:
        return any(cookie.name == name for cookie in self._client.cookies.jar)

    def clear_session(self) -> None:
        self._client.cookies.clear()
        self._session_meta = SessionData()
        self._store.clear()

    async def aclose(self) -> None:
        await self._client.aclose()

    async def __aenter__(self) -> VtopHttpClient:
        return self

    async def __aexit__(self, *args: object) -> None:
        await self.aclose()

    async def request_operation(
        self,
        operation_id: str,
        params: dict[str, str] | None = None,
    ) -> httpx.Response:
        """Execute one allowlisted VTOP operation (sole public HTTP entry)."""
        spec = get_operation(operation_id)
        query, body, path_params = validate_and_split_params(spec, params)
        path = render_path(spec, path_params)
        return await self._send(
            spec.method,
            path,
            params=query or None,
            data=body or None,
        )

    async def _send(
        self,
        method: str,
        path: str,
        *,
        params: dict[str, Any] | None = None,
        data: dict[str, Any] | None = None,
        content: bytes | None = None,
        headers: dict[str, str] | None = None,
    ) -> httpx.Response:
        """Internal transport with safe redirect handling."""
        url = resolve_path(self._settings.base_url, path)
        redirects = 0
        while True:
            assert_allowed_url(url)
            request_headers = _browser_headers(method, url)
            if headers:
                request_headers.update(headers)
            response = await self._client.request(
                method,
                url,
                params=params,
                data=data,
                content=content,
                headers=request_headers,
            )
            if response.status_code not in REDIRECT_STATUS:
                return response

            location = response.headers.get("Location")
            if not location:
                return response

            next_url = urljoin(str(response.url), location)
            try:
                assert_allowed_url(next_url)
            except HostNotAllowedError as exc:
                raise UnexpectedRedirectError(
                    f"Redirect blocked to non-allowlisted host: {next_url!r}"
                ) from exc

            redirects += 1
            if redirects > self._settings.max_redirects:
                raise UnexpectedRedirectError("Too many redirects")

            url = next_url
            method = "GET"
            params = None
            data = None
            content = None
