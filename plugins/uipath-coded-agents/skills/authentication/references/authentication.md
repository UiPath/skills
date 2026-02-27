# UiPath Authentication

Authenticate with UiPath using the UiPath Python CLI. Authentication is required to run agents and access UiPath Cloud Platform.

## Authentication Modes

The UiPath CLI supports two authentication modes:

### 🔓 Interactive Mode (Default - Recommended)

Opens a browser for OAuth authentication.

**IMPORTANT — Tenant selection flow:**

The CLI's interactive tenant picker prompts for input that Claude's Bash tool cannot provide, so `--tenant` MUST always be used on the final auth call. Follow this flow:

1. **If the user already specified a tenant**, use it directly:
   ```bash
   uv run uipath auth --cloud --tenant MY_TENANT
   ```

2. **If the user did NOT specify a tenant**, use a two-step flow:

   **Step 1** — Run auth without `--tenant`. This opens the browser for OAuth login, then prints the available tenants and hangs waiting for interactive selection. Use a timeout to capture the tenant list:
   ```bash
   uv run uipath auth --cloud
   ```
   The output will look like:
   ```
   Select tenant:
     0: TenantA
     1: TenantB
     2: TenantC
   Select tenant number:
   ```
   The command will hang at "Select tenant number:" — this is expected. Wait for the tenant list to appear, then cancel the command (Ctrl+C or timeout).

   **Step 2** — Parse ALL tenant names from the output and present them to the user as a numbered list. Show every tenant even if there are many (50+). Do NOT truncate or summarize the list. Ask them to choose one.

   **Step 3** — Run auth again with the selected tenant:
   ```bash
   uv run uipath auth --cloud --tenant SELECTED_TENANT
   ```
   This second run will reuse the cached browser token and complete without opening the browser again.

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
