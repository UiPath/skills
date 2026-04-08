# UiPath Authentication

Set up authentication with UiPath Cloud or on-premise before running cloud commands.

## Quick Reference

```bash
# Interactive OAuth (recommended)
uip login --output json
uip login tenant set "MY_TENANT" --output json

# Unattended (automation/CI)
uip login --client-id ID --client-secret SECRET --base-url URL
```

## Documentation

- **[Authentication Guide](authentication.md)** — Complete authentication setup
  - Interactive OAuth flow (with tenant selection)
  - Unattended client credentials flow
  - Environment modes (--cloud, --staging, --alpha)
  - Network and proxy settings
  - Troubleshooting (browser issues, token expiry, tenant mismatch)

## Critical Rules

- **Skip auth if already authenticated.** Check if `.env` contains `UIPATH_URL` and auth tokens first. If auth is already configured, inform the user and skip.
- **NEVER run `uip login` without `--tenant`.** The interactive tenant picker cannot be used from Claude's Bash tool.
- **Auth MUST be an interactive question (when needed).** If auth is NOT configured, your ENTIRE response must be ONLY this question — no bullet points, no "Next Steps" headers, no status summaries:

  > What is your UiPath **environment** (cloud/staging/alpha), **organization name**, and **tenant name**?

  Then STOP and wait for the user's reply. Only after they answer, run `uip login --output json followed by uip login tenant set "<TENANT>" --output json`.

## Troubleshooting

| Error | Cause | Solution |
|-------|-------|----------|
| `401 Unauthorized` from LLM Gateway | Token expired or wrong tenant | Re-run `uip login --output json` then `uip login tenant set "<TENANT>" --output json` |
| `UIPATH_URL not found` | `.env` missing or not in project root | Check `.env` exists in the working directory with `UIPATH_URL` set |

## Additional Instructions

- If unsure about usage, read the [authentication reference](authentication.md) before making assumptions.

---

# UiPath Authentication

Authenticate with UiPath using the UiPath Python CLI. Authentication is required to run agents and access UiPath Cloud Platform.

## Authentication Modes

The UiPath CLI supports two main authentication approaches: **Interactive** (OAuth) and **Unattended** (client credentials). Additionally, you can target different UiPath environments:

- **`--cloud`** — Production UiPath Cloud (default)
- **`--staging`** — Staging environment for testing
- **`--alpha`** — Alpha/preview features environment

### 🔓 Interactive Mode (Default - Recommended)

Opens a browser for OAuth authentication.

**IMPORTANT — Ask upfront, don't interrupt:**

Before running auth, ask the user for **all required info in a single question**:
- **Environment**: cloud (default), staging, or alpha
- **Organization**: their UiPath organization name
- **Tenant**: their tenant name

Example prompt: "To authenticate, I need your UiPath **environment** (cloud/staging/alpha), **organization**, and **tenant name**."

The CLI's interactive tenant picker cannot be used from Claude's Bash tool, so `--tenant` MUST always be provided on the command line.

```bash
# Once you have the tenant name:
uip login --output json
uip login tenant set "MY_TENANT" --output json
# Or for other environments:
uip login --authority "https://staging.uipath.com/identity_" --it --output json
uip login tenant set "MY_TENANT" --output json
uip login --authority "https://alpha.uipath.com/identity_" --it --output json
uip login tenant set "MY_TENANT" --output json
```

**If the user doesn't know their tenant name**, use a two-step flow:

1. Log in first, then list available tenants:
   ```bash
   uip login --output json
   uip login tenant list --output json
   ```

2. Present ALL tenant names to the user and ask them to pick one.

3. Set the selected tenant:
   ```bash
   uip login tenant set "SELECTED_TENANT" --output json
   ```

### 🔐 Unattended Mode (For Automation)

Uses client credentials flow for automated authentication without user interaction.

```bash
uip login --client-id YOUR_CLIENT_ID \
                   --client-secret YOUR_CLIENT_SECRET \
                   --base-url YOUR_BASE_URL
```

## Prerequisites Check

First, verify the UiPath SDK is available:

```bash
uip codedagent --version
```

If this command fails, you need to set up your project first. Ensure you have a `pyproject.toml` with UiPath SDK dependencies and run `uv sync` to install them.

## Environment Setup

For **Automation Suite** (on-premise) deployments, set your instance URL:

```bash
export UIPATH_URL=https://your-instance-url
```

Or add to a `.env` file in your project directory.

## Additional Options

- **Force Re-authentication:** Use `-f` or `--force` to get a new token
- **Specify Tenant:** Use `--tenant TENANT_NAME` for a specific tenant
- **Custom Scopes:** Use `--scope "SCOPE1 SCOPE2"` (defaults to 'OR.Execution')

## Network Configuration

The CLI respects proxy settings via:
- `HTTP_PROXY`, `HTTPS_PROXY`, `NO_PROXY` environment variables
- `REQUESTS_CA_BUNDLE` for custom CA certificates

## Troubleshooting

### Browser Does Not Open

**Symptom:** Running `uip login --output json` does not open a browser window.

**Solutions:**
- Ensure you have a default browser configured on your system
- Try running the command from a standard terminal (not inside a remote SSH session or container)
- Use unattended mode with `--client-id` and `--client-secret` as an alternative

### Token Expired / "Unauthorized" Errors

**Symptom:** Commands fail with "Unauthorized" or "401" after previously working.

**Solutions:**
- Re-run `uip login --output json` then `uip login tenant set "YOUR_TENANT" --output json` to refresh the token
- Use `--force` (`-f`) flag to force a new token: `uip login --output json` (forces re-auth)
- Check that `UIPATH_URL` and `UIPATH_ACCESS_TOKEN` environment variables are not stale in your `.env` file

### Tenant Not Found / Mismatch

**Symptom:** `--tenant MY_TENANT` fails with "tenant not found" or returns no results.

**Solutions:**
- Run `uip login --output json` without `--tenant` first to see the full tenant list
- Verify the tenant name is spelled exactly as shown in the list (case-sensitive)
- Ensure your UiPath account has access to the target tenant

### Client Credentials Flow Fails

**Symptom:** Unattended authentication with `--client-id` / `--client-secret` returns errors.

**Solutions:**
- Verify the client ID and secret are correct and not expired
- Check that the `--base-url` points to the correct UiPath instance
- Ensure the external application has the required scopes configured in UiPath
