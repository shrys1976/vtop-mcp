#!/usr/bin/env python3
"""Attempt VTOP login using env/keyring credentials (local dev only)."""

from __future__ import annotations

import asyncio
import logging
import sys

from vtop_mcp.config import Settings
from vtop_mcp.exceptions import (
    CredentialsMissingError,
    InvalidCredentialsError,
    RecaptchaOnlyError,
)
from vtop_mcp.vtop.auth.login import LoginFlow
from vtop_mcp.vtop.client import VtopHttpClient

logging.basicConfig(level=logging.INFO, stream=sys.stderr)


async def _main() -> int:
    settings = Settings()
    try:
        async with VtopHttpClient(settings) as client:
            flow = LoginFlow(client, settings)
            result = await flow.login()
    except CredentialsMissingError as exc:
        print(f"credentials_missing: {exc}", file=sys.stderr)
        return 2
    except RecaptchaOnlyError as exc:
        print(f"recaptcha_only: {exc}", file=sys.stderr)
        return 3
    except InvalidCredentialsError as exc:
        print(f"invalid_credentials: {exc}", file=sys.stderr)
        return 4

    print(f"status={result.status} regno={result.regno} message={result.message}")
    return 0 if result.status in ("authenticated", "otp_required") else 1


if __name__ == "__main__":
    raise SystemExit(asyncio.run(_main()))
