# CLI Cheat Sheet

Every command accepts `--output json`. Parse the structured response:

```json
// Success
{ "Result": "Success", "Code": "<OperationCode>", "Data": { ... } }

// Failure — newer CLI: server-side validation message surfaces in Message
{ "Result": "Failure", "Message": "...", "Instructions": "..." }
```

## Session + Auth Context

```bash
uip login status --output json                 # Data.Status == "Logged in"
uip login                                      # interactive OAuth
uip login --authority https://alpha.uipath.com # non-prod
```

See [auth-context.md](auth-context.md) for reading `~/.uipath/.auth` (the canonical source for `UIPATH_TENANT_ID`, `UIPATH_TENANT_NAME`, `UIPATH_ORGANIZATION_ID`, `UIPATH_ACCESS_TOKEN`).

## Products

```bash
uip gov aops-policy product list --output json
uip gov aops-policy product get <productIdentifier> --output json
```

## License Types

```bash
uip gov aops-policy license-type list --output json
```

Returns all license types (`Attended`, `Unattended`, `Development`, `StudioPro`, `StudioX`, `NoLicense`, …) with the products each license type covers. Needed to build `deployment * configure --input` JSON.

## Templates (form-data blueprints + locale labels)

```bash
# Raw template (structure + i18n component tree)
uip gov aops-policy template get <productIdentifier> --output json

# FILLABLE blueprint — the object you edit and submit to policy create/update
uip gov aops-policy template get <productIdentifier> \
  --output-form-data ./form-data.json --output json

# LOCALE-RESOLVED reference — field-by-field labels, descriptions, tooltips for the product
uip gov aops-policy template get <productIdentifier> \
  --output-template-locale-resource ./locale-resource.json --output json

# Bulk — write all three JSON files per product under the output dir
uip gov aops-policy template list --output-dir ./templates/ --output json
```

The locale-resource is the runtime equivalent of the static `property-labels.json` snapshot. Fetch it dynamically when labels matter and the snapshot is stale.

## Policy CRUD

```bash
# CREATE — --input holds the bare formData object (CLI wraps in { data: … } internally)
uip gov aops-policy create \
  --name <policyName> \
  --product-name <productIdentifier> \
  --input <path> \
  --description <text> --priority <n> --availability <n> \
  --output json
# Response: Data.identifier = the new policy GUID

# LIST — --order-direction now maps correctly (was producing 400s before)
uip gov aops-policy list [--product-name X] [--search Q] [--limit N] [--offset M] \
  [--order-by <field>] [--order-direction asc|desc] --output json

# GET — returns metadata + full form-data payload in one call
# (CLI fetches policyGetPolicyById + policyGetFormDataByPolicyId in parallel and merges into Data.data)
uip gov aops-policy get <policyIdentifier> --output json
# Response shape: { Data: { name, identifier, description, priority, availability, product, data: {...} } }

# UPDATE — ALL metadata flags required, see cli-known-issues.md #2
uip gov aops-policy update \
  --identifier <guid> \
  --name <policyName> \
  --product-name <productIdentifier> \
  --description <text> --priority <n> --availability <n> \
  --input <path> \
  --output json

# DELETE
uip gov aops-policy delete <policyIdentifier> --output json
```

> **`policy get` is the single read path.** It combines `policyGetPolicyById` (metadata) with `policyGetFormDataByPolicyId` (values) into one response. The `data` field is always populated — no separate `form-data` command needed.

### `--input` format

Bare `formData` object, NOT wrapped in `{ "data": ... }`. The CLI adds the wrapper internally.

## Deployment (tenant / group / user)

> **All `deployment * configure` commands are FULL REPLACE.** The submitted array rewrites the target's assignment list. Always read current state first, merge new entries in, then configure. See [policy-assign.md](policy-assign.md) for the merge-first pattern.
>
> **Why this matters:** the previous `assign-tenant` / `assign-group` / `assign-user` commands had a "last deploy wins" bug — sequential single-policy calls each did a full-replace at the API. The new `configure` commands fix this by taking the full assignment list in one atomic call.

### Tenant

```bash
# List tenants (paginated)
uip gov aops-policy deployment tenant list [--product-name <p>] [--limit N --offset M] --output json

# Get a specific tenant + all its assignments
uip gov aops-policy deployment tenant get <tenantIdentifier> --output json

# Configure — atomic: one call assigns ALL policies for a tenant
uip gov aops-policy deployment tenant configure <tenantIdentifier> \
  --tenant-name <name> \
  --input <path-to-assignment-array.json> \
  --output json

# Remove a single assignment by (tenant, product, licenseType)
uip gov aops-policy deployment tenant remove <tenantIdentifier> ...
```

`--input` JSON shape — pure array:
```json
[
  { "productIdentifier": "AITrustLayer", "licenseTypeIdentifier": "NoLicense", "policyIdentifier": "<guid>" },
  { "productIdentifier": "Robot",        "licenseTypeIdentifier": "Attended",  "policyIdentifier": "<guid>" },
  { "productIdentifier": "Development",  "licenseTypeIdentifier": "Development","policyIdentifier": null    }
]
```
- `policyIdentifier` = `null` → pin 'No Policy' (block inheritance).
- Omit a `(product, licenseType)` slot → falls through to inheritance.

### Group

```bash
uip gov aops-policy deployment group list --output json
uip gov aops-policy deployment group get <groupIdentifier> --output json
uip gov aops-policy deployment group configure <groupIdentifier> \
  --group-name <name> --input <path> --output json
uip gov aops-policy deployment group delete ...
```

### User

```bash
uip gov aops-policy deployment user list --output json
uip gov aops-policy deployment user get <userIdentifier> --output json
uip gov aops-policy deployment user configure <userIdentifier> \
  --user-name <name> --input <path> --output json
uip gov aops-policy deployment user delete ...
```

## Deployed Policy (effective-policy resolution)

Resolves the policy actually enforced at request time through `USER → GROUP → TENANT → GLOBAL` inheritance. Args are **positional**.

```bash
# Caller's own effective policy — no extra flags (runs under the user token from `uip login`)
uip gov aops-policy deployed-policy get <licenseType> <productName> <tenantIdentifier> --output json

# List effective policies for a subject across products
uip gov aops-policy deployed-policy list --tenant-identifier <tenantGuid> --output json
```

This skill uses only the default caller-own mode. The `--tenant-only` and `--user-id` modes require an S2S token and are intentionally out of scope — the authenticated admin typically has no user-level overrides, so the caller-own result matches tenant-scope semantics for the CHECK workflow.

## Error codes we react to

| HTTP | Meaning | Orchestrator response |
|---|---|---|
| `400` | Validation error. Newer CLI surfaces the real backend message via `extractErrorMessage`. | Halt. Read `Message` — usually names the offending field. |
| `401 / 403` | Session expired or insufficient perms. | Halt. Ask user to `uip login`. |
| `404` | Identifier not found. | Halt. Check IDs. (Missing `--input` paths now surface a clear filesystem error, not 404.) |
| `409` | Duplicate policy name on create. | Halt. V1 = do NOT retry-as-update. (Critical Rule in SKILL.md) |
| `500` | Often [missing metadata flags on update (known-issue #2)](cli-known-issues.md). | Halt. Re-read policy metadata, pass all flags. |
| `503` with transient `Instructions` text (`template upgrade`, `connection timeout`, `backend temporarily unavailable`) | AOPS is migrating the policy's Form.io template or a dependency is flapping — typically tens of seconds to minutes. | Do NOT use the default 3s retry. Wait 30s before first retry, 60s before second. Or surface to user and offer `retry now` / `cancel`. Only halt after a third failure or if the `Instructions` text shifts to a non-transient error. See [policy-crud.md UPDATE error map](policy-crud.md#update-recipe). |
| `5xx` other | Server-side. | Retry once after 3s. Halt on second failure. Surface `Instructions` verbatim. |

All halts write a deploy record (Apply) or patch record (Diagnose).

## Access policies — out of scope

`uip govern policy …` commands from branch `jianjunwang/governance-policy-tool` are not wired into this skill yet. Access-policy support is tracked as a follow-up.
