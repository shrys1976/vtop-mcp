# Test fixture policy

All committed test data must be **synthetic** or **redacted**. Never commit live VTOP data.

## Do not commit

- Session cookies (`JSESSIONID`, `SERVERID`, etc.)
- Passwords, OTPs, or API tokens
- Real `authorizedID` / CSRF values from production sessions
- Real student names, registration numbers, emails, phone numbers, marks, or attendance tied to a real person
- Captcha images captured from the live portal (use generated or minimal JPEG snippets only)

## Allowed in `tests/fixtures/`

- Placeholder reg nos (e.g. `21BCE0000`)
- Fictional course titles and faculty names
- HTML table shapes that mirror VTOP layout without real content
- Minimal base64 JPEG stubs for captcha HTML parsing tests

## Integration tests

- Run only with `VTOP_INTEGRATION=1` and local env credentials.
- **Do not** save integration responses back into fixture files.
- CI must not set `VTOP_INTEGRATION`.

## Review checklist

Before opening a PR, confirm:

1. No `.env` or credential files are staged.
2. New fixtures under `tests/fixtures/` contain no PII.
3. Logs and debug prints redact secrets (server logs to stderr only).
