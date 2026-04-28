# Synthesis Algorithm

Given `inScopeClauseIds` and `inScopePolicyFiles`, produce per-file `formData` blobs ready for `uip gov aops-policy create --input`.

## Apply always creates new policies — base is always template defaults

Apply is a CREATE operation. Every policy synthesized from a pack becomes a **new** policy on the tenant with a deterministic, scope-encoded name (e.g., `soc2-type2-2017-mandatory-AITrustLayer`). It never mutates an existing policy. Consequence: the base layer for the merge is always template defaults. Subset mode's "out-of-scope paths come from template defaults" is therefore the correct behavior — the new policy is named after the narrowed scope and reflects exactly that scope.

If a policy with the target name already exists, the CREATE returns `409` and the run halts (Critical Rule #5). The user decides whether to delete/rename or narrow further; the skill does not silently fall back.

### Pre-flight preview — informational, one line

Show the user what Apply is about to create, so subset mode doesn't surprise them, but do not add a question:

```
Creating new policy "soc2-type2-2017-mandatory-AITrustLayer" on AITrustLayer (base: template defaults).
Subset mode: 34/92 properties set from the pack (in-scope clauses); the other 58 use template defaults.
If you want to instead modify an existing policy in place, use Advise or Diagnose — not Apply.
```

The only approval remains the single pre-flight "Proceed? (y/n)" from Step 5.

### Opt-in: "merge onto existing policy" phrasing (non-default)

If the user explicitly requests it in the prompt — e.g., *"apply SOC 2 Mandatory and merge onto my existing AITL policy"* / *"don't create a new policy, update `<name>` with the pack's Mandatory values"* — hand off to the UPDATE path:

- Target policy resolved by name from the user's prompt (fail if ambiguous — show candidates via `policy list`).
- Base layer = that policy's current `data`, fetched via `uip gov aops-policy get <id>`.
- Overrides = subset formData (in-scope leaves only).
- Call the UPDATE recipe in [../../policy-crud.md](../../policy-crud.md#update-recipe), not CREATE.
- Patch record goes out instead of a deploy record.

This is a second-class path — Apply is for CREATE, and this phrasing simply routes the user to the UPDATE primitive with the pack's subset as input. Document it in the deploy record with `mode: "apply-merge-existing"` so the audit trail is distinct.

### Base-layer semantics for OTHER modes

Advise and Diagnose compute a proposed `formData` on top of live deployed-policy data by default — that's the update flow they already use. The merge script's `--base` flag accepts any JSON object; Advise/Diagnose pass the live policy's `data`, Apply passes the template defaults. Same script, same contract, different caller.

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

`policyKind: "access"` files are **skipped entirely** with `reason: "access-policies-not-yet-supported"` until the `uip govern policy` CLI family merges. Do not run synthesis on them. When access support lands, the rule will be: access is atomic — whole file included if any contributing clause is in scope, else skipped (no subset path for access).

## Naming convention

The synthesized policy needs a deterministic name so re-applies collide predictably (Critical Rule #5 treats collisions as errors — with one explicit carve-out for [prior-deploy reuse](impl.md#step-55--pre-apply-409-check--prior-deploy-reuse)).

| Scenario | Policy name |
|---|---|
| Apply all | `{packId}-{product}` |
| Apply by obligation level | `{packId}-{level}-{product}` (e.g. `iso-27001-2022-mandatory-ai-trust-layer`) |
| Apply specific clauses | `{packId}-{clauseId1}-{clauseId2}-{product}` (truncate if >4 clauses; append `-{hash8}` then) |
| Apply by NL | `{packId}-{hash8}-{product}` where `hash8` is the first 8 chars of SHA-256 of the sorted clause-id list |

`{level}` is `mandatory`, `mandatory-strict`, `mandatory-recommended`, `all`.

### Deployment target is NOT in the name

Names intentionally omit deployment target (tenant / group / user). The same synthesized policy is pinned at every level of the cascade in Phase 2 — one policy object, N `configure` bindings. This means:

- Applying HIPAA tenant-wide creates `hipaa-2024-ai-trust-layer`. Later applying the same pack to the engineering group (cascade on) does NOT create a second policy; it reuses the existing one and adds a group binding. This uses the prior-deploy-reuse path (user-confirmed — [impl.md Step 5.5](impl.md#step-55--pre-apply-409-check--prior-deploy-reuse)).
- Different **clause scope** (mandatory-only vs. all) → different policy name → different policy object, because the content is different.
- Different **deployment target** (tenant vs. group) → same policy name → same policy object, because the content is identical. Only the `configure` bindings differ.

### Obligation-level vocabulary — what each level actually selects

The pack's `clause-map.json` uses four levels: `Mandatory`, `ConditionalMandatory`, `Recommended`, `Optional`. Scope narrowing maps to clause sets as follows:

| `{level}` token in policy name | `obligationLevel` values included | Notes |
|---|---|---|
| `mandatory` | `Mandatory`, `ConditionalMandatory` | `ConditionalMandatory` is INCLUDED by default because the condition has already been accepted at the scope-selection gate. Skipping it would make a "mandatory" policy silently non-mandatory for some tenants. |
| `mandatory-recommended` | `Mandatory`, `ConditionalMandatory`, `Recommended` | |
| `all` | all four levels | Same as default (no narrowing). |

If the user's prompt says `"only strict mandatory"` / `"exclude conditional"`, explicitly exclude `ConditionalMandatory` and name the policy `{packId}-mandatory-strict-{product}` so the scope is auditable from the name alone.

`{product}` is the `productIdentifier` exactly as it appears in the policy file (e.g. `AITrustLayer`, not `ai-trust-layer`).

For **access policies**, use the `accessPolicy.name` field from the policy file directly; do not synthesize. Access policy files are atomic and already carry an author-chosen name.

## Output shape handed to the CREATE recipe

Per product policy file (any AOPS product), the orchestrator hands the CREATE recipe:

```jsonc
{
  "policyKind": "product",
  "productIdentifier": "<e.g. AITrustLayer, Robot, Development, StudioWeb, ...>",
  "policyName": "<e.g. iso-27001-2022-mandatory-AITrustLayer>",
  "formData":      { /* synthesized OVERRIDES — not a complete payload */ },
  "priority":      1,        // from policy.priority — copy through
  "availability":  365,      // from policy.availability — copy through
  "description":   "...",    // from policy.description — copy through
  "licenseTypeIdentifier": "<e.g. NoLicense, Attended, Development>",  // from pack
  "pathMode":      "fast"    // "fast" | "subset" — for telemetry / deploy record
}
```

**Important:** The `formData` here is the pack's compliance-relevant values only — not a complete template payload. The CREATE recipe fetches the product's default data via `uip gov aops-policy template get <productIdentifier> --output-form-data <path>`, then deep-merges these overrides on top using the **deterministic merge script** at `assets/scripts/merge-overrides.mjs`:

```bash
node "$SKILL_DIR/assets/scripts/merge-overrides.mjs" \
  --defaults  "$TMP/defaults.json" \
  --overrides "$TMP/overrides.json" \
  --out       "$TMP/formData.json" \
  --summary
```

Do NOT write inline merge logic per invocation. The script encodes the merge contract (objects recurse, arrays replace wholesale, explicit `null` clears, defaults fill everything else) and is the single source of truth. See the CREATE recipe in [../../policy-crud.md](../../policy-crud.md#create-recipe) for the full sequence. This works uniformly for every AOPS product.

Access policy files (`policyKind: "access"`) do not reach synthesis — they are partitioned out in the compliance plugin's Step 3 and recorded directly as `status: "skipped", reason: "access-policies-not-yet-supported"`.
