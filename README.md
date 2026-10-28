# vtop-mcp

Read-only [Model Context Protocol](https://modelcontextprotocol.io/) server for **VIT Vellore VTOP** (`vtop.vit.ac.in`). Agents can log in and fetch your authorized academic data through typed tools (no raw HTTP).

**Personal use only.** Use only on your own account and respect institute policies and terms of service.

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

**Option A — environment variables**

```bash
export VTOP_REGNO="YOUR_REGNO"
export VTOP_PASSWORD="your-vtop-password"
# Optional: auto-submit OTP when VTOP emails a code
export VTOP_OTP="123456"
```

**Option B — keyring**

Store JSON in keyring service `vtop-mcp`, username `credentials`:

```json
{"regno": "YOUR_REGNO", "password": "your-vtop-password"}
```

Session encryption uses keyring entry `vtop-mcp` / `session-key` (created on first run).

### Optional OCR fallback

If bitmap captcha solving fails:

```bash
uv sync --extra ocr
```

## Run the MCP server

```bash
uv run vtop-mcp
# or
uv run python -m vtop_mcp
```

Transport: **stdio** (default). Logs go to **stderr**; do not print to stdout except MCP protocol traffic.

## MCP client configuration

Replace `/home/shrys/dev/vtop_mcp` with your clone path.

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

## Agent workflow

1. `vtop_session_status`
2. If not authenticated → `vtop_login` (then `vtop_verify_otp` if needed)
3. `list_semesters` → use `semester_id` on semester-scoped tools
4. Read tools: `get_profile`, `get_attendance`, `get_timetable`, `get_marks`, `get_courses`, `get_exams`, `get_spotlight`, `get_academic_calendar`

There is **no** generic HTTP tool; agents cannot specify arbitrary URLs or bodies.

## MCP resources

- `vtop://session/status`
- `vtop://profile` (cached after `get_profile`)

## Local dev scripts

```bash
# Login page / prelogin probe (no secrets printed)
uv run python scripts/discovery_probe.py

# Attempt login with env/keyring credentials
uv run python scripts/login_probe.py
```

## Tests

```bash
uv sync --group dev
uv run pytest -q
```

Integration (live VTOP; **not** run in CI):

```bash
export VTOP_INTEGRATION=1
export VTOP_REGNO=...
export VTOP_PASSWORD=...
uv run pytest tests/test_integration_login.py -q
```

See [docs/fixture_policy.md](docs/fixture_policy.md) for test data rules.

## Troubleshooting

| Issue | What to do |
|-------|------------|
| `recaptcha_only` | VTOP is showing Google reCAPTCHA only; retry later or login once in a browser on the same network |
| `otp_required` | Call `vtop_verify_otp` with the email OTP or set `VTOP_OTP` for one-shot login |
| `not_authenticated` | Run `vtop_login` again; session may have expired |
| 403 on scripts | Use a browser-like environment; the probe sets User-Agent automatically |

## Documentation

- [docs/vtop_api_map.md](docs/vtop_api_map.md) — login flow and endpoint map
- [docs/fixture_policy.md](docs/fixture_policy.md) — safe test fixtures

## License

Add your license here if publishing the repository.
