# Pack Format Reference

A compliance pack is a ZIP archive with the `.uipolicy` extension. Inside are JSON files only.

## Structure

```
pack.uipolicy                 (ZIP)
├── manifest.json             pack metadata + policy index
├── clause-map.json           clause → policy properties mapping
└── policies/
    ├── <product>.json        one per distinct AOPS product (policyKind: "product")
    └── <name>.json           one per access policy   (policyKind: "access")
```

> **V1 scope note:** Only `policyKind: "product"` with `productIdentifier: "AITrustLayer"` is processed. Other product files and all access files are parsed (so the orchestrator can report them) but not sent to any plugin — they are recorded as `skipped / out-of-version-scope` in the deploy record.

## manifest.json

```jsonc
{
  "fileKind": "compliance-pack-manifest",
  "schemaVersion": "1.0.0",
  "packId": "iso-27001-2022",         // kebab-case
  "packName": "ISO/IEC 27001:2022",
  "version": "1.0.0",                 // semver
  "publishedAt": "2026-04-13T14:30:00Z",
  "clauseMapFile": "clause-map.json",
  "policies": [
    { "file": "policies/ai-trust-layer.json", "product": "AITrustLayer" },
    { "file": "policies/robot.json",          "product": "Robot" }
    // access entries have "accessPolicyType" instead of "product":
    // { "file": "policies/restrict-tools.json", "accessPolicyType": "ToolUsePolicy" }
  ]
}
```

## clause-map.json

```jsonc
{
  "fileKind": "compliance-clause-map",
  "schemaVersion": "1.0.0",
  "standardId": "iso-27001-2022",
  "standardName": "ISO/IEC 27001:2022",
  "clauses": [
    {
      "id": "A.8.11",
      "name": "Data Masking",
      "category": "A.8 – Technological Controls",
      "description": "...",
      "obligationLevel": "Mandatory",  // "Mandatory" | "ConditionalMandatory" | "Recommended" | "Optional"
      // "condition": "...",            // required when obligationLevel == "ConditionalMandatory"
      "contributions": [
        {
          "uipolicyFile": "policies/ai-trust-layer.json",
          "properties": [               // dot-separated leaf paths; empty [] for access (atomic)
            "pii-processing-mode",
            "container.pii-in-flight-agents"
          ]
        }
      ]
    }
  ]
}
```

### Legacy `mandatory` flag

The v0 reference pack at `C:\Work\compliance-pack-compiler\` predates the `obligationLevel` field. If a clause has `"mandatory": true`, treat it as `"obligationLevel": "Mandatory"`. If `"mandatory": false`, treat it as `"Optional"`.

## policies/<file>.json — Product

```jsonc
{
  "fileKind": "uipolicy",
  "fileVersion": "1.0.0",
  "policyKind": "product",                // default — may be omitted in legacy packs
  "policy": {
    "name": "iso-27001-2022-ai-trust-layer",
    "description": "...",
    "productIdentifier": "AITrustLayer",  // MUST match manifest.policies[].product
    "licenseTypeIdentifier": "NoLicense",
    "priority": 1,
    "availability": 365
  },
  "formData": {
    // Arbitrary product-specific shape. Deeply nested. Leaf paths are owned by clauses.
  },
  "deploymentLevel": "tenant"             // V1: always "tenant"
}
```

## policies/<file>.json — Access

```jsonc
{
  "fileKind": "uipolicy",
  "fileVersion": "1.0.0",
  "policyKind": "access",
  "accessPolicy": {
    "accessPolicyType": "ToolUsePolicy",  // or "AccessControlPolicy"
    "name": "restrict-agent-tools",
    "selectors": [ /* ... */ ],
    "executableRule": { /* ... */ },
    "actorRule": { /* ... */ },
    "enforcement": "Allow",
    "status": "Active"
  }
}
```

## Validation rules (defensive checks the orchestrator performs)

| Check | On fail |
|---|---|
| Archive contains `manifest.json` and `clause-map.json` | Stop, report malformed pack |
| Every `manifest.policies[].file` exists in the archive | Stop, report broken reference |
| `policyKind` ∈ `{"product", "access"}` (absent → `"product"`) | Stop, report unknown kind |
| Every clause contribution's `uipolicyFile` exists in `manifest.policies[]` | Stop, report dangling reference |
| `obligationLevel` ∈ the four enum values (or legacy `mandatory` present) | Stop, report schema drift |
| For `ConditionalMandatory`, `condition` is a non-empty string | Stop, report missing condition |
