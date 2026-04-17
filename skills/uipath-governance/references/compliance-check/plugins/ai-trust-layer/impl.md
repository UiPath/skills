# Check · AITL Plugin

Product-specific logic for checking AITrustLayer policies against the live tenant. Called by the workflow orchestrator for each applicable AITL policy file.

## Input (from orchestrator)

```jsonc
{
  "policyFile": "policies/ai-trust-layer.json",
  "productIdentifier": "AITrustLayer",
  "licenseTypeIdentifier": "NoLicense",
  "expectedFormData": { /* from the pack's policy file */ },
  "policyName": "iso-27001-2022-ai-trust-layer",
  "deploymentLevel": "tenant",
  "tenantId": "<UIPATH_TENANT_ID from ~/.uipath/.auth>",
  "tenantName": "DefaultTenant"
}
```

`licenseTypeIdentifier` and `productIdentifier` come from the pack's `policy` block. `tenantId` comes from `~/.uipath/.auth`. The plugin always resolves the effective policy for the **currently authenticated user** — it does not target a specific group/user principal.

## Step 1 — Resolve the effective policy

```bash
uip admin aops-policy deployment get-by-user \
  <LICENSE_TYPE> <PRODUCT_IDENTIFIER> <TENANT_GUID> \
  --output json
```

Example:

```bash
uip admin aops-policy deployment get-by-user NoLicense AITrustLayer 22986e36-8b04-4593-b82f-aae4c14bb2dc --output json
```

This returns the effective policy after the full USER → GROUP → TENANT → GLOBAL inheritance chain.

Parse the response:

| Path | Meaning |
|---|---|
| `Data.data` | Live effective `formData` — compare against `expectedFormData` |
| `Data.policy-name` | Name of the policy that ended up applying |
| `Data.deployment.type` | Which layer applied: `USER` / `GROUP` / `TENANT` / `GLOBAL` |
| `Data.deployment.name` | Principal or tenant name at that layer |
| `Data.availability` | Days remaining until re-evaluation |

### Response shortcuts

| Situation | Response | Action |
|---|---|---|
| No policy in chain | `204` / `Data.Message == "No policy applies to this user."` | Return `not-deployed` result (see below). |
| Invalid license / product / tenant | `404 Not Found` | Halt. Surface the invalid input; do not fall back to `not-deployed`. |
| Auth expired | `401 / 403` | Halt. Ask user to `uip login`. |

## Step 2 — Deep diff

Walk every leaf property in `expectedFormData` and compare against the live `formData` returned in `Data.data`.

### Comparison rules

| Type | Comparison |
|---|---|
| Boolean | Exact match (`true` vs `false`) |
| String / Enum | Exact match (case-sensitive) |
| Number | Exact match |
| Nested object (e.g. `container`) | Recursive walk — compare each leaf |
| Array (e.g. `pii-entity-table`) | Order-independent. Match items by `identifier` key. Compare `pii-entity-is-enabled` and `pii-entity-confidence-threshold` per item. |

### AITL-specific value quirks

These properties have non-obvious types. Compare using the actual type, not a string cast:

| Property | Type | Values |
|---|---|---|
| `allow-llm-model-auto-routing` | String | `"yes"` or `"no"` (NOT boolean) |
| `traces-ttl`, `traces-ttl-effective` | String | Duration like `"90d"`, `"30d"` |
| `pii-processing-mode` | Enum | `"DetectionAndMasking"` / `"DetectionOnly"` / `"Disabled"` |
| `pii-execution-stage` | Enum | `"Both"` / `"InFlight"` / `"AtRest"` / `"Disabled"` |
| `container.*` | Nested booleans | Walk each leaf |
| `allowed-llm-regions.*` | Nested booleans | Walk each leaf |

### Handling missing paths

If a path exists in the pack but not in the live policy:
- Record it as a mismatch: `{ "path": "...", "expected": <value>, "actual": null, "match": false }`
- This can happen if the tenant's policy was created from an older template.

If a path exists in the live policy but not in the pack:
- Ignore it. The pack defines what should be checked. Extra tenant-side properties are not drift.

## Return to orchestrator

### Success (policy effectively applied, diff complete)

```jsonc
{
  "status": "checked",
  "effectivePolicyName": "<Data.policy-name>",
  "effectiveDeployment": { "type": "TENANT", "name": "<tenant or principal name>" },
  "properties": [
    { "path": "pii-processing-mode", "expected": "DetectionAndMasking", "actual": "DetectionAndMasking", "match": true },
    { "path": "container.pii-in-flight-agents", "expected": true, "actual": false, "match": false }
  ]
}
```

### Not deployed (no policy in inheritance chain, i.e. 204)

```jsonc
{
  "status": "not-deployed",
  "effectivePolicyName": null,
  "effectiveDeployment": null,
  "properties": []
}
```

## Error handling

| Error | Action |
|---|---|
| `401 / 403` on `get-by-user` | Halt. Ask user to `uip login`. |
| `404` on `get-by-user` | Halt. License, product, or tenant identifier is invalid — this is a pack or auth-context problem, not drift. |
| `204` on `get-by-user` | Treat as `not-deployed`. |
| `5xx` | Retry once after 3s. On second failure, halt and surface. |

## What this plugin does NOT do

- No clause mapping (orchestrator's job via `clause-map.json`)
- No terminal output or reporting
- No remediation or mutation
- No scope selection (orchestrator determines which properties to check)

## Adding a new product

Create a sibling folder (e.g. `plugins/development/impl.md`) with the same interface: receive expected formData, fetch live state, diff, return results. The orchestrator's dispatch table gets a new row.
