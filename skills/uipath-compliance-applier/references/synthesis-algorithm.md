# Synthesis Algorithm

Given `inScopeClauseIds` and `inScopePolicyFiles`, produce per-file `formData` blobs ready for `uip admin aops-policy create --data-file`.

## Fast path vs. subset path

For each `policyFile` ∈ `inScopePolicyFiles`:

```
contributingClauses = { c : c ∈ clauses
                          ∧ any(contrib.uipolicyFile == policyFile
                                for contrib in c.contributions) }

if contributingClauses ⊆ inScopeClauseIds:
    # FAST PATH
    formData = policyFile.formData   # use as-is
else:
    # SUBSET PATH
    formData = extractSubset(policyFile, inScopeClauseIds)
```

## Fast path

Every clause that contributes to this file is selected. The pack's `formData` already reflects the merged, clause-aware values. Use it literally — no modification.

## Subset path

Only some contributing clauses are in scope. Extract just the owned leaf paths.

```python
def extractSubset(policyFile, inScopeClauseIds):
    ownedPaths = set()
    for clause in clauses:
        if clause.id not in inScopeClauseIds:
            continue
        for contrib in clause.contributions:
            if contrib.uipolicyFile == policyFile:
                ownedPaths.update(contrib.properties)

    result = {}
    for path in ownedPaths:
        value = getNested(policyFile.formData, path)  # "container.pii-in-flight-agents"
        setNested(result, path, value)
    return result
```

### Leaf-path semantics

Paths are **explicit, dot-separated leaves**. No wildcards. Examples:

- `pii-processing-mode` → top-level scalar
- `container.pii-in-flight-agents` → nested boolean
- `allowed-llm-regions.united-states` → nested boolean

`getNested("container.pii-in-flight-agents", formData)` walks the path; `setNested(...)` creates intermediate objects as needed.

### If a path is missing in `formData`

Pack compiler should guarantee every declared leaf exists. If you encounter a missing path:
- Log a warning
- Skip that leaf (don't insert `undefined`)
- Include the missing path in the policy's `warnings[]` in the deploy record

## Access policies — out of V1 scope

`policyKind: "access"` files are **skipped entirely** in V1 with `reason: "out-of-version-scope"`. Do not run synthesis on them. When access support lands, the rule will be: access is atomic — whole file included if any contributing clause is in scope, else skipped.

## Naming convention

The synthesized policy needs a deterministic name so re-applies collide predictably (V1 treats collisions as errors per Critical Rule #4).

| Scenario | Policy name |
|---|---|
| Apply all | `{packId}-{product}` |
| Apply by obligation level | `{packId}-{level}-{product}` (e.g. `iso-27001-2022-mandatory-AITrustLayer`) |
| Apply specific clauses | `{packId}-{clauseId1}-{clauseId2}-{product}` (truncate if >4 clauses; append `-{hash8}` then) |
| Apply by NL | `{packId}-{hash8}-{product}` where `hash8` is the first 8 chars of SHA-256 of the sorted clause-id list |

`{level}` is `mandatory`, `mandatory-recommended`, `all`.
`{product}` is the `productIdentifier` exactly as it appears in the policy file (e.g. `AITrustLayer`, not `ai-trust-layer`).

For **access policies**, use the `accessPolicy.name` field from the policy file directly; do not synthesize. Access policy files are atomic and already carry an author-chosen name.

## Output shape handed to plugins (AITL only in V1)

Per AITL policy file, the orchestrator hands the creation plugin:

```jsonc
{
  "policyKind": "product",
  "productIdentifier": "AITrustLayer",
  "policyName": "iso-27001-2022-mandatory-AITrustLayer",
  "formData":      { /* synthesized */ },
  "priority":      1,        // from policy.priority — copy through
  "availability":  365,      // from policy.availability — copy through
  "description":   "...",    // from policy.description — copy through
  "licenseTypeIdentifier": "NoLicense",  // from policy.licenseTypeIdentifier
  "pathMode":      "fast"    // "fast" | "subset" — for telemetry / deploy record
}
```

Non-AITL product files and all access files do not reach synthesis — they are partitioned out in SKILL.md Step 3 and recorded directly as `status: "skipped", reason: "out-of-version-scope"`.
