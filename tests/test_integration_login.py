"""Optional live VTOP login integration test."""

from __future__ import annotations

import os

import pytest

from vtop_mcp.config import Settings
from vtop_mcp.exceptions import CredentialsMissingError, RecaptchaOnlyError
from vtop_mcp.vtop.auth.login import LoginFlow
from vtop_mcp.vtop.client import VtopHttpClient

pytestmark = pytest.mark.skipif(
    os.environ.get("VTOP_INTEGRATION") != "1",
    reason="Set VTOP_INTEGRATION=1 with VTOP_REGNO/VTOP_PASSWORD to run",
)


@pytest.mark.asyncio
async def test_live_login_flow() -> None:
    settings = Settings()
    try:
        async with VtopHttpClient(settings) as client:
            flow = LoginFlow(client, settings)
            result = await flow.login()
    except CredentialsMissingError:
        pytest.skip("VTOP credentials not configured")
    except RecaptchaOnlyError as exc:
        pytest.skip(str(exc))

    assert result.status in ("authenticated", "otp_required")
