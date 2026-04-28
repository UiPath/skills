# Compliance Check Report Format

The walker writes one JSON file per check run. The HTML renderer reads it to produce the auditor-facing report. Both files are co-located in `--out-dir`.

## Schema

```jsonc
{
  "reportKind": "compliance-check",
  "schemaVersion": "1.0.0",

  "generatedAt": "2026-04-23T11:30:00Z",

  "pack": {
    "packId":   "iso-42001-2023-aitl",
    "packName": "ISO/IEC 42001:2023 — AI Trust Layer Controls",
    "version":  "1.0.0",
    "source":   "assets/packs/iso-42001-aitl-v1.0.0.uipolicy"
  },

  "target": {
    "tenantId":             "<guid>",
    "tenantName":           "DefaultTenant",
    "runScope":             "caller-own",     // uses the authenticated admin's effective-policy view (no S2S)
    "effectivePolicyName":  "iso-42001-2023-aitl-ai-trust-layer",
    "effectiveDeployment":  { "type": "TENANT", "name": "DefaultTenant" }
  },

  "overall": "Compliant" | "Non-Compliant" | "Partially Compliant",

  "summary": {
    "totalClauses":       21,
    "compliant":          17,
    "drifted":             4,
    "skipped":             0,
    "skippedPolicyFiles":  2
  },

  "clauses": [
    {
      "clauseId":        "M06",
      "name":            "Block unvetted third-party AI models",
      "category":        "Operational Risk Controls",
      "obligationLevel": "Mandatory",
      "status":          "compliant" | "drifted" | "skipped",
      "contributions": [
        {
          "policyFile":          "policies/ai-trust-layer.json",
          "product":             "AITrustLayer",
          "status":              "checked" | "skipped",
          "reason":              "group-scope-check-not-supported",  // only when status == "skipped"
          "effectivePolicyName": "iso-42001-2023-aitl-ai-trust-layer",
          "effectiveDeployment": { "type": "TENANT", "name": "DefaultTenant" },
          "properties": [
            { "path": "azure-openai-control-toggle", "expected": true, "actual": true, "match": true },
            { "path": "allowed-llm-regions.europe",   "expected": true, "actual": false, "match": false }
          ]
        }
      ]
    }
  ],

  "skippedPolicies": [
    { "file": "policies/ai-trust-layer-group.json", "product": "AITrustLayer", "reason": "group-scope-check-not-supported" },
    { "file": "policies/ai-trust-layer-user.json",  "product": "AITrustLayer", "reason": "user-scope-check-not-supported" }
  ]
}
```

## Aggregate rules

Applied by the walker after each clause's contributions are resolved:

1. Any `checked` contribution has `properties[].match == false` → clause status = `drifted`
2. At least one `checked` contribution, all match → `compliant`
3. All contributions `skipped` → clause status = `skipped`

## Overall status

1. Zero clauses or all `compliant` → `Compliant` (`badge-pass`)
2. Any `Mandatory` / `ConditionalMandatory` clause `drifted` → `Non-Compliant` (`badge-fail`)
3. All clauses `drifted` → `Non-Compliant` (`badge-fail`)
4. Otherwise → `Partially Compliant` (`badge-partial`)

## Skip reasons

| reason | When |
|---|---|
| `access-policies-not-yet-supported` | `policyKind: "access"` — CLI does not yet support access-policy reads |
| `group-scope-check-not-supported` | Manifest / policy file specifies `deploymentLevel: "group"` |
| `user-scope-check-not-supported` | Manifest / policy file specifies `deploymentLevel: "user"` |

Skipped contributions still appear in the clause's `contributions[]` so readers can see what was expected but not verified. The top-level `skippedPolicies[]` is a deduplicated list of policy files skipped at least once.

## Write rules

1. Write the JSON unconditionally at the end of every run.
2. Default filename: `compliance-report-<packId>-<compactTimestamp>.json` (HTML gets the same base name).
3. Default location: the `--out-dir` passed to the walker — typically `./` (current working directory).
4. Drift is a finding, not a failure. Walker exits 0 regardless.
5. Never commit the reports. They contain tenant identifiers and live policy values.
