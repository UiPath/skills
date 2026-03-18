# Authentication

UiPath authentication and tenant management — OAuth2 browser login, client credentials for CI/CD, PAT tokens, and tenant selection.

## Overview

Authentication is the first step before any Orchestrator, Solution, or Integration Service operation. The CLI stores credentials at `~/.uipcli/.env` after login, which can be reused for direct REST API calls.

## Supported Auth Methods

| Method | Use Case | Command |
|---|---|---|
| **Interactive (OAuth2)** | Developer workstation — opens browser | `uip login --format json` |
| **Client Credentials** | CI/CD pipelines, headless environments | `uip login --client-id <ID> --client-secret <SECRET> --tenant <TENANT> --format json` |
| **PAT Token** | Personal access tokens | `uip login --file .env --format json` (with PAT in .env) |
| **Custom Authority** | Non-default identity endpoints (e.g., alpha) | `uip login --authority "https://alpha.uipath.com/identity_" --it --format json` |

## Tenant Management

After login, select the target tenant:

```bash
# List available tenants
uip login tenant list --format json

# Set active tenant
uip login tenant set "Production" --format json

# Check current status
uip login status --format json
```

Tenants provide complete isolation — each has its own folders, robots, assets, queues.

## Credential Storage

After successful login, credentials are stored at `~/.uipcli/.env`:

```
UIPATH_URL=https://cloud.uipath.com
UIPATH_ORG_NAME=my_org
UIPATH_TENANT_NAME=my_tenant
UIPATH_ACCESS_TOKEN=eyJ...
UIPATH_ORGANIZATION_ID=...
UIPATH_TENANT_ID=...
```

These values can be sourced for direct REST API calls when CLI commands don't cover a use case.

## See Also

- Full command syntax: [../cli/uip-commands.md - Authentication](../cli/uip-commands.md)
- REST API fallback: [../orchestrator/orchestrator-guide.md - REST API Reference](../orchestrator/orchestrator-guide.md)
