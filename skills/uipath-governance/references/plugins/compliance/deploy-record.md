# Deploy Record

Single audit JSON written per apply run. Captures both phases.

## File location — mandatory

**Default path:** `$HOME/uipath-governance/audit/deploy-records/deploy-record-<packId>[-<scopeTag>]-<timestampCompact>.json`.

- Persistent (survives OS temp-dir wipes and reboots).
- Located under `~/uipath-governance/`, a directory owned by this skill — distinct from `~/.uipath/`, which the UiPath CLI owns. Keeps audit artifacts separate from CLI state.
- Not inside a user's git repo by construction — satisfies the "never commit to git" rule automatically.
- Mirrors the patch-record convention (`$HOME/uipath-governance/audit/patch-records/`), so both audit artifact families live side by side.

```
$HOME/uipath-governance/audit/deploy-records/deploy-record-iso-27001-2022-20260423T144500Z.json
$HOME/uipath-governance/audit/deploy-records/deploy-record-soc2-type2-2017-mandatory-AITrustLayer-20260420T093012Z.json
```

`<timestampCompact>` is UTC ISO-8601 with colons and dashes stripped (matches `compliance-report-*.json` from Check mode). If the scope was narrowed (obligation level, deployment level, or specific clauses), encode it in the filename so parallel runs don't collide: `<scopeTag>` is the token used in the synthesized policy name (e.g., `mandatory`, `mandatory-AITrustLayer`, clauseId hash).

**Never write deploy records to**:
- the current working directory (CWD may be a git repo — the contents hold tenant + principal identifiers);
- `$TMP_ROOT/uipath-governance/...` (scratch dir — OS can wipe it anytime);
- any path the user explicitly calls out as tracked.

Honor an explicit user override (`--record-out <dir>`) if given — but warn loudly if that dir is inside a repo. Always remind the user at the end of the report where the record landed (absolute path).

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

  "mode": "full-apply",              // "full-apply" | "create-only" | "deploy-only" | "apply-merge-existing"
  "clauseScope": {
    "kind": "all",                   // "all" | "obligation" | "specific" | "nl"
    "obligationNarrowing": null,     // "mandatory" | "mandatory-strict" | "mandatory+recommended" | null
    "detail": null,                  // ["A.8.11", ...] | "data masking" | null
    "selectedClauseIds": [...]
  },

  "deploymentTargets": [             // ordered ancestor → descendant; length 1 means tenant-only
    { "level": "tenant", "targetId": "<tenantGuid>", "targetName": "DefaultTenant" },
    { "level": "group",  "targetId": "<groupGuid>",  "targetName": "engineering", "memberCount": 39 }
  ],
  "cascadeEnabled": true,             // false when user said "group-only" / "don't touch tenant"
  "narrowestNamedScope": "group",     // "tenant" | "group" | "user"

  // Phase 1 outcomes
  "created": [
    {
      "policyKind": "product",
      "identifier": "AITrustLayer",             // productIdentifier or accessPolicyType
      "policyName": "soc2-type2-2017-ai-trust-layer",
      "policyId": "<guid>",
      "pathMode": "fast",                       // "fast" | "subset" — "atomic" reserved for future access support
      "baseLayer": "template-defaults",         // always for CREATE path
      "contributingClauses": ["SC01", ...],
      "overriddenPathCount": 42,
      "reusedExisting": false,                   // true when Step 5.5 reuse path was taken
      "priorDeployRecord": null,                 // path to prior deploy record when reusedExisting == true
      "status": "success",                      // "success" | "failed" | "skipped" | "reused"
      "reason": null,                           // skip reason when status == "skipped"
      "error": null,                            // { step, code, message } when failed
      "warnings": []
    }
  ],

  // Phase 2 outcomes — one entry per (policy, deployment target) pair
  "deployed": [
    {
      "policyId": "<guid>",
      "policyName": "soc2-type2-2017-ai-trust-layer",
      "scope": {
        "level": "tenant",                       // "tenant" | "group" | "user"
        "targetId":   "<tenantGuid>",
        "targetName": "staging-tenant"
      },
      "addedAssignmentCount": 1,                 // new (product, license) slot added at this scope
      "replacedAssignmentCount": 0,              // existing slot whose policyIdentifier changed
      "preservedAssignmentCount": 2,             // existing slots left untouched by the merge
      "status": "success",                       // "success" | "failed" | "skipped"
      "error": null,
      "warnings": []
    }
    // Same policy often repeats across cascade — a second entry with scope.level: "group" follows
  ],

  "summary": {
    "createdSuccess": 3, "createdFailed": 0, "createdSkipped": 0, "createdReused": 0,
    "deployedSuccess": 6, "deployedFailed": 0, "deployedSkipped": 0,   // 3 policies × 2 cascade targets
    "cascadeTargetCount": 2
  }
}
```

## Write rules

1. Write unconditionally — on total failure the file still exists with `created: []` + a `fatalError` field.
2. Default path: see the "File location — mandatory" section at the top of this file (`$HOME/uipath-governance/audit/deploy-records/...`). Respect `--record-out <dir>` if the user passed one.
3. Write **once** at the end of the run, not incrementally.
4. Do NOT commit / stage to git. Default location is outside any repo; if a user override points inside one, warn loudly before writing.

## Status semantics

| Status | Meaning |
|---|---|
| `success` | CLI call returned 2xx and the expected identifier was captured. |
| `failed` | CLI call returned 4xx/5xx. `error` populated. Phase halted at this policy. |
| `skipped` | Policy was never attempted. Always paired with a `reason` field: |

### Skip reasons

| `reason` | When |
|---|---|
| `access-policies-not-yet-supported` | `policyKind: "access"` entry in the pack. Access-policy CLI lives on `jianjunwang/governance-policy-tool` and hasn't merged. |
| `out-of-clause-scope`  | Policy file's contributing clauses are all excluded by scope selection. |
| `prior-failure`        | A preceding policy in the same phase hit a 4xx (fail-fast). |
| `mode-skip`            | Mode is `create-only` (Phase 2 skipped) or `deploy-only` (Phase 1 skipped). |
| `user-halted`          | User did not confirm at the pre-flight gate. |

## Re-apply sanity

Because policy names are deterministic per `(packId, scenario, identifier)`, a naive re-run will 409 on the first create. The deploy record is how the operator reconciles: compare `created[].status == "success"` from a prior record against AOPS state before re-running, clean up conflicts manually (V1 has no rollback), then re-run.
