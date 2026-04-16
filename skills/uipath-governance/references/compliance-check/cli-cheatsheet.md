# CLI Cheat Sheet (Read-Only)

Every command accepts `--output json`. Parse the structured response:

```json
// Success
{ "Result": "Success", "Code": "<OperationCode>", "Data": { ... } }

// Failure
{ "Result": "Failure", "Message": "...", "Instructions": "..." }
```

> **Read-only constraint.** This skill only uses `list`, `get`, and `status` commands. Never call `create`, `assign`, `update`, or `delete`.

## Session + Auth Context

```bash
uip login status --output json                 # Data.Status == "Logged in"
```

### `~/.uipath/.auth` — canonical source for IDs and tokens

After `uip login`, the CLI writes a `KEY=VALUE` env file at `~/.uipath/.auth` (Windows: `C:\Users\<user>\.uipath\.auth`). Read this file for tenant/org identifiers.

```bash
AUTH_FILE="$HOME/.uipath/.auth"
UIPATH_TENANT_ID=$(grep '^UIPATH_TENANT_ID=' "$AUTH_FILE" | cut -d'=' -f2-)
UIPATH_TENANT_NAME=$(grep '^UIPATH_TENANT_NAME=' "$AUTH_FILE" | cut -d'=' -f2-)
UIPATH_ORGANIZATION_ID=$(grep '^UIPATH_ORGANIZATION_ID=' "$AUTH_FILE" | cut -d'=' -f2-)
UIPATH_ACCESS_TOKEN=$(grep '^UIPATH_ACCESS_TOKEN=' "$AUTH_FILE" | cut -d'=' -f2-)
```

| Key | Use |
|---|---|
| `UIPATH_TENANT_ID` | Identify the tenant being checked |
| `UIPATH_TENANT_NAME` | Display in terminal summary and report |
| `UIPATH_ORGANIZATION_ID` | Needed for principals lookup (group/user level checks) |
| `UIPATH_URL` | Base URL (e.g. `https://alpha.uipath.com`) |
| `UIPATH_ACCESS_TOKEN` | Bearer token for raw API calls (principals lookup) |

**If the file is missing:** `uip login` has not been run. Halt.

## Policy Read Commands

```bash
# List policies (optionally filter by product)
uip admin aops-policy list --output json
uip admin aops-policy list --product-name AITrustLayer --output json
uip admin aops-policy list --search "<POLICY_NAME>" --output json

# Get a specific policy by ID (returns full formData)
uip admin aops-policy get <POLICY_IDENTIFIER> --output json
```

## Effective Policy Resolution

```bash
# Get the effective policy for a product at tenant scope
uip admin aops-policy deployment get-by-tenant \
  --license-type <LICENSE_TYPE> \
  --product-name <PRODUCT_IDENTIFIER> \
  --tenant-identifier <TENANT_GUID> \
  --output json
```

Returns the effective policy after applying the USER → GROUP → TENANT → GLOBAL inheritance chain.

## Products (discovery)

```bash
uip admin aops-policy product list --output json
uip admin aops-policy product get <PRODUCT_IDENTIFIER> --output json
```

## Identity Directory Search (for group/user level checks)

```bash
# Groups
curl -sS -G "{identityBase}/api/Directory/Search/{orgId}" \
  --data-urlencode "startsWith=<PREFIX>" \
  --data "sourceFilter=localGroups" \
  --data "sourceFilter=directoryGroups" \
  -H "Authorization: Bearer $TOKEN"

# Users
curl -sS -G "{identityBase}/api/Directory/Search/{orgId}" \
  --data-urlencode "startsWith=<PREFIX>" \
  --data "sourceFilter=localUsers" \
  --data "sourceFilter=directoryUsers" \
  -H "Authorization: Bearer $TOKEN"
```

`{identityBase}` = `https://<cloud>/<orgName>/identity_`. `{orgId}` = organization GUID.

## Error codes

| HTTP | Meaning | Action |
|---|---|---|
| `401 / 403` | Session expired or insufficient perms | Halt. Ask user to `uip login`. |
| `404` | Policy or product not found | Record as `not-deployed`. |
| `5xx` | Server-side | Retry once after 3s. Then halt and surface. |
