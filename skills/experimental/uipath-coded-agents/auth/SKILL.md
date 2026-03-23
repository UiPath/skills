---
name: auth
description: Authenticate with UiPath Cloud or on-premise deployments. Handles OAuth interactive login, unattended client credentials, tenant selection, and environment configuration. Use when the user says "log in to UiPath", "authenticate", "connect to my tenant", or "set up UiPath credentials".
allowed-tools: Bash, Read, Write, Glob, Grep, AskUserQuestion
user-invocable: true
---

# UiPath Authentication

Set up authentication with UiPath Cloud or on-premise before running cloud commands.

## Quick Reference

```bash
# Interactive OAuth (recommended)
uv run uipath auth --cloud --tenant MY_TENANT

# Unattended (automation/CI)
uv run uipath auth --client-id ID --client-secret SECRET --base-url URL
```

## Documentation

- **[Authentication Guide](references/authentication.md)** — Complete authentication setup
  - Interactive OAuth flow (with tenant selection)
  - Unattended client credentials flow
  - Environment modes (--cloud, --staging, --alpha)
  - Network and proxy settings
  - Troubleshooting (browser issues, token expiry, tenant mismatch)

## Critical Rules

- **Skip auth if already authenticated.** Check if `.env` contains `UIPATH_URL` and auth tokens first. If auth is already configured, inform the user and skip.
- **NEVER run `uipath auth` without `--tenant`.** The interactive tenant picker cannot be used from Claude's Bash tool.
- **Auth MUST be an interactive question (when needed).** If auth is NOT configured, your ENTIRE response must be ONLY this question — no bullet points, no "Next Steps" headers, no status summaries:

  > What is your UiPath **environment** (cloud/staging/alpha), **organization name**, and **tenant name**?

  Then STOP and wait for the user's reply. Only after they answer, run `uv run uipath auth --<env> --tenant <TENANT>`.

## Troubleshooting

| Error | Cause | Solution |
|-------|-------|----------|
| `401 Unauthorized` from LLM Gateway | Token expired or wrong tenant | Re-run `uv run uipath auth --cloud --tenant <TENANT>` |
| `UIPATH_URL not found` | `.env` missing or not in project root | Check `.env` exists in the working directory with `UIPATH_URL` set |

## Additional Instructions

- If unsure about usage, read the [authentication reference](references/authentication.md) before making assumptions.
