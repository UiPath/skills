# Check · AITL Plugin

Product-specific logic for checking AITrustLayer policies against the live tenant. Called by the workflow orchestrator for each applicable AITL policy file.

## Input (from orchestrator)

```jsonc
{
  "policyFile": "policies/ai-trust-layer.json",
  "productIdentifier": "AITrustLayer",
  "expectedFormData": { /* from the pack's policy file */ },
  "policyName": "iso-27001-2022-ai-trust-layer",
  "deploymentLevel": "tenant",
  "targetId": "<TENANT_GUID>",
  "targetName": "DefaultTenant"
}
```

## Step 1 — Find the deployed policy

```bash
uip admin aops-policy list --product-name AITrustLayer --search "<POLICY_NAME>" --output json
```

Parse `Data` array. Match by `name` field (exact, case-sensitive).

If no match is found, try listing all AITL policies:

```bash
uip admin aops-policy list --product-name AITrustLayer --output json
```

If still no match, return `not-deployed` result (see below).

## Step 2 — Fetch the full policy

```bash
uip admin aops-policy get <POLICY_IDENTIFIER> --output json
```

Parse `Data.policyFormData` — this is the live `formData`.

## Step 3 — Deep diff

Walk every leaf property in `expectedFormData` and compare against the live `formData`.

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

### Success (policy found, diff complete)

```jsonc
{
  "status": "checked",
  "policyId": "<GUID>",
  "properties": [
    { "path": "pii-processing-mode", "expected": "DetectionAndMasking", "actual": "DetectionAndMasking", "match": true },
    { "path": "container.pii-in-flight-agents", "expected": true, "actual": false, "match": false }
  ]
}
```

### Not deployed

```jsonc
{
  "status": "not-deployed",
  "policyId": null,
  "properties": []
}
```

## Error handling

| Error | Action |
|---|---|
| `401 / 403` on `list` or `get` | Halt. Ask user to `uip login`. |
| `404` on `get` (policy deleted between list and get) | Treat as `not-deployed`. |
| `5xx` | Retry once after 3s. On second failure, halt and surface. |

## What this plugin does NOT do

- No clause mapping (orchestrator's job via `clause-map.json`)
- No terminal output or reporting
- No remediation or mutation
- No scope selection (orchestrator determines which properties to check)

## Adding a new product

Create a sibling folder (e.g. `plugins/development/impl.md`) with the same interface: receive expected formData, fetch live state, diff, return results. The orchestrator's dispatch table gets a new row.
