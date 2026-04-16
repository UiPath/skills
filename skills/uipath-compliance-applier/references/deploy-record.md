# Deploy Record

Single audit JSON written per apply run. Captures both phases.

## Schema

```jsonc
{
  "fileKind": "compliance-deploy-record",
  "schemaVersion": "2.0.0",

  "applyTimestamp": "2026-04-15T11:20:13Z",
  "appliedBy": "user-email",
  "organization": "procodeapps",
  "tenant": { "identifier": "<guid>", "name": "DefaultTenant" },

  "pack": {
    "packId": "iso-27001-2022",
    "packName": "ISO/IEC 27001:2022",
    "version": "1.0.0",
    "source": "file:///C:/..."
  },

  "mode": "full-apply",              // "full-apply" | "create-only" | "deploy-only"
  "scope": {
    "kind": "all",                   // "all" | "obligation" | "specific" | "nl"
    "detail": null,                  // "mandatory" | ["A.8.11", ...] | "data masking"
    "selectedClauseIds": [...]
  },

  // Phase 1 outcomes
  "created": [
    {
      "policyKind": "product",
      "identifier": "AITrustLayer",             // productIdentifier or accessPolicyType
      "policyName": "iso-27001-2022-AITrustLayer",
      "policyId": "<guid>",
      "pathMode": "subset",                     // "fast" | "subset" (AITL) — "atomic" reserved for future access support
      "contributingClauses": ["A.5.23", ...],
      "status": "success",                      // "success" | "failed" | "skipped"
      "reason": null,                           // skip reason when status == "skipped" (see table below)
      "error": null,                            // { step, code, message } when failed
      "warnings": []
    }
  ],

  // Phase 2 outcomes (empty if mode == "create-only")
  "deployed": [
    {
      "policyId": "<guid>",
      "policyName": "iso-27001-2022-AITrustLayer",
      "scope": {
        "level": "tenant",                       // "tenant" | "group" | "user"
        "targetId":   "<guid>",
        "targetName": "DefaultTenant"
      },
      "assignmentId": "<guid-or-null>",
      "status": "success",                       // "success" | "failed" | "skipped"
      "error": null,
      "warnings": []
    }
  ],

  "summary": {
    "createdSuccess": 3, "createdFailed": 1, "createdSkipped": 0,
    "deployedSuccess": 3, "deployedFailed": 0, "deployedSkipped": 1
  }
}
```

## Write rules

1. Write unconditionally — on total failure the file still exists with `created: []` + a `fatalError` field.
2. Default path: `./deploy-record-{packId}-{applyTs}.json`. Respect `--deploy-record-path` override.
3. Write **once** at the end of the run, not incrementally.
4. Do NOT commit / stage to git. Contains tenant identifiers.

## Status semantics

| Status | Meaning |
|---|---|
| `success` | CLI call returned 2xx and the expected identifier was captured. |
| `failed` | CLI call returned 4xx/5xx. `error` populated. Phase halted at this policy. |
| `skipped` | Policy was never attempted. Always paired with a `reason` field: |

### Skip reasons

| `reason` | When |
|---|---|
| `out-of-version-scope` | Non-AITL policy in the pack. V1 handles only `productIdentifier == "AITrustLayer"`. All other products and all access policies are recorded with this reason. |
| `out-of-clause-scope`  | Policy file's contributing clauses are all excluded by scope selection. |
| `prior-failure`        | A preceding policy in the same phase hit a 4xx (fail-fast). |
| `mode-skip`            | Mode is `create-only` (Phase 2 skipped) or `deploy-only` (Phase 1 skipped). |
| `user-halted`          | User did not confirm at the pre-flight gate. |

## Re-apply sanity

Because policy names are deterministic per `(packId, scenario, identifier)`, a naive re-run will 409 on the first create. The deploy record is how the operator reconciles: compare `created[].status == "success"` from a prior record against AOPS state before re-running, clean up conflicts manually (V1 has no rollback), then re-run.
