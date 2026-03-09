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
uv run uipath auth --cloud --tenant MY_TENANT
# Or for other environments:
uv run uipath auth --staging --tenant MY_TENANT
uv run uipath auth --alpha --tenant MY_TENANT
```

**If the user doesn't know their tenant name**, use a two-step flow:

1. Run auth without `--tenant` to discover available tenants:
   ```bash
   uv run uipath auth --cloud
   ```
   This opens the browser for OAuth login, then prints available tenants and hangs at "Select tenant number:". Cancel after the tenant list appears.

2. Present ALL tenant names to the user and ask them to pick one.

3. Run auth again with the selected tenant:
   ```bash
   uv run uipath auth --cloud --tenant SELECTED_TENANT
   ```

### 🔐 Unattended Mode (For Automation)

Uses client credentials flow for automated authentication without user interaction.

```bash
uv run uipath auth --client-id YOUR_CLIENT_ID \
                   --client-secret YOUR_CLIENT_SECRET \
                   --base-url YOUR_BASE_URL
```

## Prerequisites Check

First, verify the UiPath SDK is available:

```bash
uv run uipath --version
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

**Symptom:** Running `uv run uipath auth --cloud` does not open a browser window.

**Solutions:**
- Ensure you have a default browser configured on your system
- Try running the command from a standard terminal (not inside a remote SSH session or container)
- Use unattended mode with `--client-id` and `--client-secret` as an alternative

### Token Expired / "Unauthorized" Errors

**Symptom:** Commands fail with "Unauthorized" or "401" after previously working.

**Solutions:**
- Re-run `uv run uipath auth --cloud --tenant YOUR_TENANT` to refresh the token
- Use `--force` (`-f`) flag to force a new token: `uv run uipath auth --cloud --tenant YOUR_TENANT -f`
- Check that `UIPATH_URL` and `UIPATH_ACCESS_TOKEN` environment variables are not stale in your `.env` file

### Tenant Not Found / Mismatch

**Symptom:** `--tenant MY_TENANT` fails with "tenant not found" or returns no results.

**Solutions:**
- Run `uv run uipath auth --cloud` without `--tenant` first to see the full tenant list
- Verify the tenant name is spelled exactly as shown in the list (case-sensitive)
- Ensure your UiPath account has access to the target tenant

### Client Credentials Flow Fails

**Symptom:** Unattended authentication with `--client-id` / `--client-secret` returns errors.

**Solutions:**
- Verify the client ID and secret are correct and not expired
- Check that the `--base-url` points to the correct UiPath instance
- Ensure the external application has the required scopes configured in UiPath
