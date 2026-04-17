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
# List policies (optionally filter by product) — used only for skipped/reporting context
uip admin aops-policy list --output json
uip admin aops-policy list --product-name AITrustLayer --output json
```

## Effective Policy Resolution (primary)

```bash
# Resolve the effective policy for the currently authenticated user
uip admin aops-policy deployment get-by-user \
  <LICENSE_TYPE> <PRODUCT_IDENTIFIER> <TENANT_GUID> \
  --output json
```

Positional args (all required):
- `<LICENSE_TYPE>` — e.g. `NoLicense`, `Attended` (from the pack's `policy.licenseTypeIdentifier`)
- `<PRODUCT_IDENTIFIER>` — e.g. `AITrustLayer` (from the pack's `policy.productIdentifier`)
- `<TENANT_GUID>` — `UIPATH_TENANT_ID` from `~/.uipath/.auth`

Returns the effective policy after applying the full USER → GROUP → TENANT → GLOBAL inheritance chain for the calling user. Response shape:

```jsonc
{
  "Result": "Success",
  "Code": "AopsPolicyDeploymentGetByUser",
  "Data": {
    "availability": 30,
    "policy-name": "<effective policy name>",
    "deployment": { "type": "USER|GROUP|TENANT|GLOBAL", "name": "<principal/tenant name>" },
    "data": { /* live formData — compare this against the pack's expectedFormData */ }
  }
}
```

| Response | Meaning | Action |
|---|---|---|
| `200` with `Data.data` | Policy effectively applied | Diff `Data.data` vs pack `formData` |
| `204 No Content` (`Data.Message == "No policy applies to this user."`) | No policy in the inheritance chain | Record clause/policy as `not-deployed` |
| `404` | License, product, or tenant identifier invalid | Halt. Surface the invalid input. |

## Products (discovery)

```bash
uip admin aops-policy product list --output json
uip admin aops-policy product get <PRODUCT_IDENTIFIER> --output json
```

## Identity Directory Search (not used in V1 check mode)

`get-by-user` resolves the effective policy for the authenticated session, so V1 drift checks do **not** look up group or user principals. The directory search endpoints remain documented for future scope (e.g. running a check as an admin on behalf of a named principal):

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

| HTTP | Context | Meaning | Action |
|---|---|---|---|
| `401 / 403` | any | Session expired or insufficient perms | Halt. Ask user to `uip login`. |
| `204` | `get-by-user` | No policy applies in the inheritance chain | Record clause/policy as `not-deployed`. |
| `404` | `get-by-user` | Invalid license / product / tenant identifier | Halt and surface — this is not drift. |
| `404` | `list` / `product get` | Resource not found | Surface as pack or input error. |
| `5xx` | any | Server-side | Retry once after 3s. Then halt and surface. |
