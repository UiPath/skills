# Compliance Report Format

Single audit JSON written per compliance check run.

## Schema

```jsonc
{
  "reportKind": "compliance-check",
  "schemaVersion": "1.0.0",
  "generatedAt": "2026-04-16T14:30:00Z",

  "pack": {
    "packId": "iso-27001-2022",
    "packName": "ISO/IEC 27001:2022",
    "version": "1.0.0",
    "source": "file:///path/to/pack.uipolicy"
  },

  "target": {
    "tenantUrl": "https://alpha.uipath.com/my_org/my_tenant",
    "tenantName": "DefaultTenant",
    "deploymentLevel": "tenant",
    "principalId": null,
    "principalName": null
  },

  "summary": {
    "totalClauses": 9,
    "compliant": 7,
    "drifted": 1,
    "notDeployed": 1,
    "skippedPolicies": 3
  },

  "clauses": [
    {
      "clauseId": "A.8.11",
      "name": "Data Masking",
      "category": "A.8 – Technological Controls",
      "obligationLevel": "Mandatory",
      "status": "compliant",
      "contributions": [
        {
          "product": "AITrustLayer",
          "properties": [
            {
              "path": "pii-processing-mode",
              "expected": "DetectionAndMasking",
              "actual": "DetectionAndMasking",
              "match": true
            }
          ]
        }
      ]
    },
    {
      "clauseId": "A.8.12",
      "name": "Data Leakage Prevention",
      "category": "A.8 – Technological Controls",
      "obligationLevel": "Mandatory",
      "status": "drifted",
      "contributions": [
        {
          "product": "AITrustLayer",
          "properties": [
            {
              "path": "container.pii-in-flight-agents",
              "expected": true,
              "actual": false,
              "match": false,
              "classificationType": "Content Safety"
            }
          ]
        }
      ]
    },
    {
      "clauseId": "A.5.3",
      "name": "Segregation of Duties",
      "category": "A.5 – Organizational Controls",
      "obligationLevel": "Mandatory",
      "status": "not-deployed",
      "contributions": [
        {
          "product": "AITrustLayer",
          "properties": []
        }
      ]
    }
  ],

  "skippedPolicies": [
    { "file": "policies/development.json", "product": "Development", "reason": "out-of-version-scope" },
    { "file": "policies/robot.json", "product": "Robot", "reason": "out-of-version-scope" },
    { "file": "policies/studio-web.json", "product": "StudioWeb", "reason": "out-of-version-scope" }
  ]
}
```

## Field reference

### Top-level

| Field | Type | Description |
|---|---|---|
| `reportKind` | string | Always `"compliance-check"` |
| `schemaVersion` | string | Semver. Current: `"1.0.0"` |
| `generatedAt` | string | ISO 8601 timestamp |

### `pack`

| Field | Type | Description |
|---|---|---|
| `packId` | string | From `manifest.json` |
| `packName` | string | Human-readable name |
| `version` | string | Semver from manifest |
| `source` | string | How the pack was resolved (`file://`, `https://`, or `pack-id:version`) |

### `target`

| Field | Type | Description |
|---|---|---|
| `tenantUrl` | string | Full tenant URL |
| `tenantName` | string | From `~/.uipath/.auth` |
| `deploymentLevel` | string | `"tenant"` / `"group"` / `"user"` |
| `principalId` | string/null | Group or user GUID (null for tenant) |
| `principalName` | string/null | Group or user display name (null for tenant) |

### `clauses[]`

| Field | Type | Description |
|---|---|---|
| `clauseId` | string | From `clause-map.json` |
| `name` | string | Clause display name |
| `category` | string | Clause category |
| `obligationLevel` | string | `"Mandatory"` / `"ConditionalMandatory"` / `"Recommended"` / `"Optional"` |
| `status` | string | `"compliant"` / `"drifted"` / `"not-deployed"` |
| `contributions[]` | array | Per-product property comparisons |

### `contributions[].properties[]`

| Field | Type | Description |
|---|---|---|
| `path` | string | Dot-separated property path in `formData` |
| `expected` | any | Value from the pack |
| `actual` | any | Value from the live tenant (null if not-deployed) |
| `match` | boolean | Whether expected equals actual |
| `classificationType` | string | Present only on mismatched properties. From the policy reference classification. |

### `skippedPolicies[]`

| Field | Type | Description |
|---|---|---|
| `file` | string | Policy file path within the pack |
| `product` | string | Product identifier |
| `reason` | string | Always `"out-of-version-scope"` in V1 |

## Status semantics

| Status | Meaning |
|---|---|
| `compliant` | All contributing properties match between pack and tenant |
| `drifted` | One or more properties differ |
| `not-deployed` | No matching policy found on the tenant for this product |

## Write rules

1. Write unconditionally — even if everything is compliant.
2. Default path: `./compliance-report-{packId}-{timestamp}.json`.
3. Write once at the end of the check, not incrementally.
4. Do NOT commit or stage to git. Contains tenant identifiers.
