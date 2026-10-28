# vtop-mcp

Read-only mcp server for vit vellore vtop (`vtop.vit.ac.in`). 

## Features

- Stdio MCP server (Claude Desktop, Cursor, or any stdio-capable MCP host)
- Strict allowlist of VTOP HTTP operations (read-only; no registration/payment/profile edits)
- Encrypted session on disk; credentials via environment or OS keyring
- Text captcha login; reloads the login flow when Google reCAPTCHA appears until the built-in captcha is served (configurable via `VTOP_MAX_RECAPTCHA_REFRESHES`, default 60)

## Requirements

- Python 3.12+
- [uv](https://docs.astral.sh/uv/) (recommended)

## Setup

```bash
git clone <your-repo-url> vtop_mcp
cd vtop_mcp
uv sync
```

### Credentials

**Option A -- environment variables**

```bash
export VTOP_REGNO="YOUR_USERNAME"
export VTOP_PASSWORD="your-vtop-password"
# Optional: auto-submit OTP when VTOP emails a code
export VTOP_OTP="123456"
```

**Option B -- keyring**

Store JSON in keyring service `vtop-mcp`, username `credentials`:

```json
{"regno": "YOUR_REGNO", "password": "your-vtop-password"}
```

Session encryption uses keyring entry `vtop-mcp` / `session-key` (created on first run).

### Captcha (auto OCR + manual fallback)

VTOP text captchas are noisy; auto-solve fails most of the times, manual filling works the best.


## Run the MCP server

```bash
uv run vtop-mcp
# or
uv run python -m vtop_mcp
```

Transport: **stdio** (default). Logs go to **stderr**; do not print to stdout except MCP protocol traffic.


### Claude Desktop

`claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "vtop": {
      "command": "uv",
      "args": [
        "run",
        "--directory",
        "/home/shrys/dev/vtop_mcp",
        "vtop-mcp"
      ]
    }
  }
}
```

### Cursor

`.cursor/mcp.json` or Cursor settings:

```json
{
  "mcpServers": {
    "vtop": {
      "command": "uv",
      "args": [
        "run",
        "--directory",
        "/home/shrys/dev/vtop_mcp",
        "vtop-mcp"
      ]
    }
  }
}
```

## Local dev scripts

```bash
# Login page / prelogin probe (no secrets printed)
uv run python scripts/discovery_probe.py

# Attempt login with env/keyring credentials
uv run python scripts/login_probe.py
```



