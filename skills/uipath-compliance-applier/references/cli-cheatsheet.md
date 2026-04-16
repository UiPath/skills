# CLI Cheat Sheet

Every command accepts `--output json`. Parse the structured response:

```json
// Success
{ "Result": "Success", "Code": "<OperationCode>", "Data": { ... } }

// Failure
{ "Result": "Failure", "Message": "...", "Instructions": "..." }
```

## Session + Auth Context

```bash
uip login status --output json                 # Data.Status == "Logged in"
uip login                                      # interactive OAuth
uip login --authority https://alpha.uipath.com # non-prod
```

### `~/.uipath/.auth` — canonical source for IDs and tokens

After `uip login`, the CLI writes a `KEY=VALUE` env file at `~/.uipath/.auth` (Windows: `C:\Users\<user>\.uipath\.auth`). **Always read this file for tenant/org identifiers and bearer tokens** instead of asking the user or decoding JWTs.

```bash
AUTH_FILE="$HOME/.uipath/.auth"
UIPATH_TENANT_ID=$(grep '^UIPATH_TENANT_ID=' "$AUTH_FILE" | cut -d'=' -f2-)
UIPATH_ORGANIZATION_ID=$(grep '^UIPATH_ORGANIZATION_ID=' "$AUTH_FILE" | cut -d'=' -f2-)
UIPATH_ACCESS_TOKEN=$(grep '^UIPATH_ACCESS_TOKEN=' "$AUTH_FILE" | cut -d'=' -f2-)
```

| Key | Use in the skill |
|---|---|
| `UIPATH_TENANT_ID` | `--tenant-identifier` for `assign-tenant` |
| `UIPATH_TENANT_NAME` | Display / deploy record |
| `UIPATH_ORGANIZATION_ID` | `{orgId}` in Directory Search for principals plugin |
| `UIPATH_ORGANIZATION_NAME` | URL path segment for Identity API |
| `UIPATH_URL` | Base URL (e.g. `https://alpha.uipath.com`) |
| `UIPATH_ACCESS_TOKEN` | Bearer token for raw API calls (principals plugin) |

**If the file is missing:** `uip login` has not been run. Halt.

## Products (discovery only — apply uses the pack's value)

```bash
uip admin aops-policy product list --output json
uip admin aops-policy product get <productIdentifier> --output json
```

Returns AOPS products available in the current org: `AITrustLayer`, `Robot`, `Development`, `StudioWeb`, `Assistant`, `AssistantWeb`, `Automate`, `Business`, `StudioPro`, `IntegrationService`.

## Templates (optional validation)

```bash
uip admin aops-policy template get <productIdentifier> --output json
uip admin aops-policy template generate-data <productIdentifier> \
  --output-file <path> --output json
```

`template generate-data` writes the default `formData` object from the current form template. Useful for comparing pack-provided formData against current product defaults.

## Policy CRUD

```bash
# Create
uip admin aops-policy create \
  --name <policyName> \
  --product-name <productIdentifier> \
  --data-file <path-to-formData.json> \
  [--description <text>] \
  [--priority <n>] \
  [--availability <n>] \
  --output json
# Response: Data.identifier = the new policy GUID

# Read
uip admin aops-policy list [--product-name X] [--search Q] [--limit N] [--offset M] --output json
uip admin aops-policy get <policyIdentifier> --output json

# Update
uip admin aops-policy update \
  --policy-identifier <guid> \
  --name <policyName> \
  --product-name <productIdentifier> \
  [--description <text>] \
  [--priority <n>] \
  [--availability <n>] \
  [--data-file <path>] \
  --output json

# Delete
uip admin aops-policy delete <policyIdentifier> --output json
```

### Data file format

`--data-file` expects the **bare `formData` object** (NOT wrapped in `{ "data": ... }` — the CLI wraps it internally). Example content:

```json
{
  "pii-processing-mode": "DetectionAndMasking",
  "pii-execution-stage": "Both",
  "container": { "pii-in-flight-agents": true }
}
```

## Assignment (Phase 2 only — deployment plugin)

Three levels. Pick one per policy; the skill dispatches based on `scope.level`.

```bash
# Tenant
uip admin aops-policy assign-tenant \
  --policy-identifier <guid> \
  --tenant-identifier <tenantGuid> \
  --product-identifier <productIdentifier> \
  --license-type-identifier <licenseType> \
  --output json

# Group (requires group GUID from principals plugin)
uip admin aops-policy assign-group \
  --policy-identifier <guid> \
  --group-identifier <groupGuid> \
  --product-identifier <productIdentifier> \
  --license-type-identifier <licenseType> \
  --output json

# User (requires user GUID from principals plugin)
uip admin aops-policy assign-user \
  --policy-identifier <guid> \
  --user-identifier <userGuid> \
  --product-identifier <productIdentifier> \
  --license-type-identifier <licenseType> \
  --output json
```

Runtime inheritance resolves `USER → GROUP → TENANT → GLOBAL`.

## Identity Directory Search (principals plugin — no `uip` wrapper yet, use curl)

```bash
# Groups
curl -sS -G "{identityBase}/api/Directory/Search/{orgId}" \
  --data-urlencode "startsWith=<prefix>" \
  --data "sourceFilter=localGroups" \
  --data "sourceFilter=directoryGroups" \
  -H "Authorization: Bearer $TOKEN"

# Users
curl -sS -G "{identityBase}/api/Directory/Search/{orgId}" \
  --data-urlencode "startsWith=<prefix>" \
  --data "sourceFilter=localUsers" \
  --data "sourceFilter=directoryUsers" \
  -H "Authorization: Bearer $TOKEN"
```

`{identityBase}` = `https://<cloud>/<orgName>/identity_` (alpha or cloud). `{orgId}` = organization GUID (not name).

## Effective policy resolution (readback / verification)

```bash
uip admin aops-policy deployment get-by-tenant \
  --license-type <licenseType> \
  --product-name <productIdentifier> \
  --tenant-identifier <tenantGuid> \
  --output json
```

Returns the **effective** policy for a product at tenant scope after applying the USER → GROUP → TENANT → GLOBAL inheritance chain. Useful for post-apply verification.

## Error codes we react to

| HTTP | Meaning | Orchestrator response |
|---|---|---|
| `400` | Schema mismatch (unknown `formData` leaves, etc.) | Halt the run. Surface missing / unknown paths from the error. |
| `401 / 403` | Session expired or insufficient perms | Halt. Ask user to `uip login`. |
| `409` | Duplicate policy name | Halt. V1 = do NOT retry-as-update. (Critical Rule #4) |
| `5xx` | Server-side | Halt. Retry once after a short delay; then surface. |

All halts write a deploy record with `status: "failed"` on the offending policy and `skipped` on the rest.

## Access policies — out of V1 scope

`uip govern policy …` commands from branch `jianjunwang/governance-policy-tool` are not used by this skill in V1. Access policy support is tracked as a follow-up. Do not invoke these commands from the orchestrator or any plugin.
