# Deployment · AOps

Bind a created AOps product policy to a scope. Three branches based on `scope.level`.

## Input (from orchestrator)

```jsonc
{
  "policyKind":            "product",
  "policyId":              "<guid from Phase 1>",
  "policyName":            "<for logging>",
  "productIdentifier":     "AITrustLayer",
  "licenseTypeIdentifier": "NoLicense",
  "scope": {
    "level":      "tenant | group | user",
    "targetId":   "<guid>",                 // tenant | group | user GUID
    "targetName": "<human name>"            // for the deploy record
  }
}
```

## Resolving auth context from `~/.uipath/.auth`

Before any deployment call, read the `uip` CLI auth file for tenant and org identifiers:

```bash
AUTH_FILE="$HOME/.uipath/.auth"
# File format: KEY=VALUE (one per line, env-style, NOT JSON)
UIPATH_TENANT_ID=$(grep '^UIPATH_TENANT_ID=' "$AUTH_FILE" | cut -d'=' -f2-)
UIPATH_TENANT_NAME=$(grep '^UIPATH_TENANT_NAME=' "$AUTH_FILE" | cut -d'=' -f2-)
UIPATH_ORGANIZATION_ID=$(grep '^UIPATH_ORGANIZATION_ID=' "$AUTH_FILE" | cut -d'=' -f2-)
UIPATH_ACCESS_TOKEN=$(grep '^UIPATH_ACCESS_TOKEN=' "$AUTH_FILE" | cut -d'=' -f2-)
```

This file is written by `uip login` and kept current by the CLI. On Windows the path is `C:\Users\<user>\.uipath\.auth`.

Available fields:

| Key | Example | Use |
|---|---|---|
| `UIPATH_TENANT_ID` | `edb2c1a2-246e-4cd3-a5f1-08aea1cbecec` | `--tenant-identifier` for `assign-tenant` |
| `UIPATH_TENANT_NAME` | `DefaultTenant` | Display / deploy record |
| `UIPATH_ORGANIZATION_ID` | `3aa10965-a82d-4d9e-8366-0eff8e87bf7a` | Needed by principals plugin for Directory Search |
| `UIPATH_ORGANIZATION_NAME` | `procodeapps` | URL construction for Identity API |
| `UIPATH_URL` | `https://alpha.uipath.com` | Base URL for raw API calls |
| `UIPATH_ACCESS_TOKEN` | `eyJ...` (JWT) | Bearer token for raw API calls (principals plugin) |
| `UIPATH_REFRESH_TOKEN` | `...` | Do not use directly — CLI manages refresh |

**If the file is missing or `UIPATH_TENANT_ID` is empty:** `uip login` has not been run. Halt and ask the user to log in.

## Determining `scope.level` (orchestrator handles; documented here for context)

1. **User prompt says it** — "apply to the Finance group" → `group`, "to nishank.siddharth@uipath.com" → `user`.
2. **`policy.deploymentLevel` in the policy file** — typically `tenant` in V1 packs.
3. **Default** — `tenant`. The `UIPATH_TENANT_ID` from `~/.uipath/.auth` is the target.

If level is `group` or `user` and no `targetId` is provided, the orchestrator must call [../principals/impl.md](../principals/impl.md) first to resolve one.

## Branch: tenant

The `--tenant-identifier` value comes from `UIPATH_TENANT_ID` in `~/.uipath/.auth` — never guess or ask the user for it.

```bash
uip admin aops-policy assign-tenant \
  --policy-identifier "<policyId>" \
  --tenant-identifier "$UIPATH_TENANT_ID" \
  --product-identifier "<productIdentifier>" \
  --license-type-identifier "<licenseTypeIdentifier>" \
  --output json
```

## Branch: group

```bash
uip admin aops-policy assign-group \
  --policy-identifier "<policyId>" \
  --group-identifier "<scope.targetId>" \
  --product-identifier "<productIdentifier>" \
  --license-type-identifier "<licenseTypeIdentifier>" \
  --output json
```

Confirm exact flag names from `uip admin aops-policy assign-group --help` — the orchestrator validates this once per run before looping.

## Branch: user

```bash
uip admin aops-policy assign-user \
  --policy-identifier "<policyId>" \
  --user-identifier "<scope.targetId>" \
  --product-identifier "<productIdentifier>" \
  --license-type-identifier "<licenseTypeIdentifier>" \
  --output json
```

## Return to orchestrator

```jsonc
{
  "status":       "success",
  "assignmentId": "<guid-or-null>",     // whatever the CLI returns as the assignment handle
  "scope":        { "level": "...", "targetId": "...", "targetName": "..." },
  "warnings":     []
}
```

## Error map

| HTTP | Action |
|---|---|
| `400` | Halt. Bad identifier (policy/product/license/tenant-group-user). |
| `401 / 403` | Halt. Permission — ask user to check role. |
| `404` | Halt. Target not found — most commonly a bad tenant/group/user GUID. |
| `409` | Halt. Policy already assigned to this target. |
| `5xx` | Retry once after 3s. |

## Precedence note

Assignments resolve via `USER → GROUP → TENANT → GLOBAL` inheritance at runtime. Phase 2 just creates the binding; effective-policy resolution at request time is up to AOps. Use `uip admin aops-policy deployment get-by-tenant | get-by-user` to verify effective policy after a large apply.
