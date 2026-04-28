# Apply · Compliance Pack

Apply a compiled `.uipolicy` compliance pack to a UiPath tenant. Two phases: creation, then deployment.

> **Scope:** all `policyKind: "product"` entries for any AOPS product are processed through the shared CREATE recipe. Product-specific quirks (CLI value conventions, known error patterns) live in optional `products/<product>.md` files — only created when there's something real to document. `policyKind: "access"` entries are skipped (access policy CLI is on a separate branch, pending merge).

## Invocation modes

| Mode | Trigger | Runs |
|---|---|---|
| Full apply (default) | "apply ISO 27001" | Phase 1 (create) + Phase 2 (deploy) |
| Create-only | "just create", "--skip-deploy" | Phase 1 only |
| Deploy-only | "deploy this policy", "--skip-create" + policyId | Phase 2 only |

## Shared primitives used

- [../../auth-context.md](../../auth-context.md) — read `UIPATH_TENANT_ID`, etc.
- [../../policy-crud.md](../../policy-crud.md) — CREATE recipe (fetch defaults + merge + create)
- [../../policy-assign.md](../../policy-assign.md) — tenant / group / user binding
- [../../principals-lookup.md](../../principals-lookup.md) — when deployment level is group/user
- [../../property-labels.md](../../property-labels.md) — human labels for pre-flight and report output

## Workflow

### Step 0 — Preflight

Run the preflight check from [../../auth-context.md](../../auth-context.md). Require `Data.Status == "Logged in"` and `UIPATH_TENANT_ID` non-empty.

### Step 1 — Resolve the pack

[pack-resolution.md](pack-resolution.md). Accepts `--pack-file <path>` (V0), `--pack-url <url>`, or `--pack-id <id> [--pack-version <v>]`.

### Step 2 — Parse

[pack-format.md](pack-format.md). Read `manifest.json`, `clause-map.json`, every `policies/*.json`.

### Step 3 — Partition applicable vs. skipped

```
applicable = [ p for p in manifest.policies if p.policyKind == "product" (or absent) ]
skipped    = [ p for p in manifest.policies if p.policyKind == "access" ]
```

Access policy support is deferred — the `uip govern policy` CLI family lives on `jianjunwang/governance-policy-tool` and hasn't merged yet. When it does, add a `policyKind == "access"` branch.

Log the split to the user:
```
Pack: iso-27001-2022 v1.0.0
Applicable (product policies, 4 files):
  - policies/ai-trust-layer.json  (AITrustLayer)
  - policies/development.json     (Development)
  - policies/robot.json           (Robot)
  - policies/studio-web.json      (StudioWeb)
Skipped (access policies — out of scope, 0 files)
```

### Step 4 — Determine scope (both axes)

[scope-selection.md](scope-selection.md). Two independent axes, decided from the prompt:

- **Clause scope** — default is every clause; narrowed only on explicit signal (obligation level / clause IDs / NL phrase).
- **Deployment target** — default is tenant-only; narrower scopes trigger an automatic cascade (`group X` → `[tenant, group X]`; `user Y` → `[tenant, group(optional), user Y]`). Cascade turns off only when the user explicitly says "group-only" / "don't touch tenant" / similar.

Produce two outputs for the rest of the workflow:

```jsonc
{
  "clauseScope": {
    "inScopeClauseIds": ["HIPAA-01", "HIPAA-02", ...],
    "obligationNarrowing": "mandatory+conditional",   // "none" | "mandatory" | "mandatory-strict" | "mandatory+recommended" | "all-including-optional" | "explicit-ids" | "nl-match"
    "token": "mandatory"                               // for policy naming — null means "no narrowing"
  },
  "deploymentTargets": [                               // ordered ancestor → descendant
    { "level": "tenant", "targetId": "<tenantGuid>", "targetName": "DefaultTenant" },
    { "level": "group",  "targetId": "<groupGuid>",  "targetName": "engineering" }
  ],
  "cascadeEnabled": true,                              // false when user said "group-only"
  "narrowestNamedScope": "group"                        // for policy naming — "tenant" | "group" | "user"
}
```

### Step 4.5 — Resolve principals (if deployment target includes group or user)

Runs before pre-flight so the user sees concrete GUIDs and names in the preview. For every deployment target whose `level ∈ {group, user}`:

1. Call [../../principals-lookup.md](../../principals-lookup.md) with the name from the prompt (e.g., "engineering").
2. If multiple matches, surface candidates:
   ```
   Found 3 groups matching "engineering":
     [1]  engineering              (39 members) <guid>
     [2]  engineering-leadership   (6 members)  <guid>
     [3]  engineering-interns      (12 members) <guid>
   Pick the group to apply to (1/2/3) or type "all" to apply to each, or "n" to cancel.
   ```
3. On zero matches or user cancellation: halt with a clear error message and no side effects.
4. Write the resolved `targetId` + exact `targetName` back into the `deploymentTargets[]` entry.

Skip this step when the only target is tenant (already resolved from `~/.uipath/.auth`).

### Step 5 — Pre-flight confirmation

Full-scope, tenant-only apply — baseline:

```
Pack: hipaa-2024 v1.0.0
Clause scope: all (15 clauses, 4 product policies to apply)
Will CREATE (new policies, base = template defaults):
  - AITrustLayer → hipaa-2024-ai-trust-layer
  - Development  → hipaa-2024-development
  - Robot        → hipaa-2024-robot
  - StudioWeb    → hipaa-2024-studio-web
Will DEPLOY to (cascade):
  [TENANT]  DefaultTenant (<tenantGuid>)
Proceed? (y/n)
```

Narrowed deployment scope with cascade — SOC 2 on engineering group:

```
Pack: soc2-type2-2017 v1.0.3
Clause scope: all (17 clauses, 3 applicable product policies)
Will CREATE:
  - AITrustLayer → soc2-type2-2017-ai-trust-layer
  - Development  → soc2-type2-2017-development
  - Robot        → soc2-type2-2017-robot
Will DEPLOY to (cascade):
  [TENANT]  staging-tenant (<tenantGuid>)
  [GROUP]   engineering (<groupGuid>)  (39 members)
Proceed? (y/n)
```

Narrowed clause scope — note the informational line per affected file:

```
Pack: soc2-type2-2017 v1.0.3
Clause scope: Mandatory + ConditionalMandatory (12 of 17 clauses)
Will CREATE:
  - AITrustLayer → soc2-type2-2017-mandatory-ai-trust-layer
      Subset mode: 34/92 properties from pack; the other 58 use template defaults.
      To instead modify an existing policy in place, ask Advise/Diagnose (not Apply).
Will DEPLOY to (cascade):
  [TENANT]  DefaultTenant (<tenantGuid>)
Proceed? (y/n)
```

Cascade OFF (user said "group-only" / "don't touch tenant"):

```
Will DEPLOY to:
  [GROUP]  engineering (<groupGuid>)   (cascade disabled by prompt)
Proceed? (y/n)
```

Require `y`. Anything else halts with no side effects.

### Step 5.5 — Pre-apply 409 check + prior-deploy reuse

Before Phase 1, run `uip gov aops-policy list --search "<policyName>" --output json` for each planned policy. If a policy with the exact name already exists:

1. Pull the prior deploy record (search `$HOME/uipath-governance/audit/deploy-records/` for records that list this policy in `created[]`). If found, surface to the user:
   ```
   A policy with this name already exists — created by an earlier Apply run:
     policy:     hipaa-2024-ai-trust-layer (<guid>)
     created by: deploy-record-hipaa-2024-20260420T091301Z.json (user-email, pack v1.0.0)

   Reuse the existing policy and just add the new deployment binding?
     (y — reuse existing GUID, skip CREATE, proceed to DEPLOY)
     (n — halt so you can rename / delete / decide manually)
   ```
2. On `y`: record the entry as `reusedExisting: true` in the new deploy record with `priorDeployRecord: <path>`, skip Phase 1 CREATE for that entry, and route directly to Phase 2 DEPLOY with the existing GUID.
3. On `n` or no prior deploy record found: halt with a 409 conflict per Critical Rule #5.

This is the only carve-out from Critical Rule #5 (which forbids silent `create→update` fallback). Reuse is explicit, user-confirmed, and named in the audit trail — it is **not** an update.

### Step 6 — Synthesize

[synthesis-algorithm.md](synthesis-algorithm.md). Fast vs. subset path decided per policy file. Produces **override formData** (not a complete payload) — merged with product defaults in the CREATE recipe.

### Step 7 — Phase 1: CREATE

For each `applicable` policy file (sequential, fail-fast):

1. **Check for product-specific quirks** — look for `products/<normalized-product>.md` (e.g., AITL → `products/ai-trust-layer.md`). Normalize product name: lowercase, `PascalCase` → `kebab-case` (`AITrustLayer` → `ai-trust-layer`, `StudioWeb` → `studio-web`). Read the quirks file if it exists; otherwise proceed with the shared CREATE recipe only.
2. **Call the CREATE recipe** in [../../policy-crud.md](../../policy-crud.md) with `formData` = synthesized overrides.
3. **Collect** `{ policyId, status, warnings[] }`.

For each `skipped` (access) policy file:
- Append to `deploy-record.created[]` with `status: "skipped", reason: "access-policies-not-yet-supported"`.
- No CLI call.

Halt on any 4xx — remaining files become `status: "skipped", reason: "prior-failure"`.

### Step 8 — Phase 2: DEPLOY (one `configure` call per cascade target)

Skip if `--skip-deploy`. Otherwise, loop over every entry in `deploymentTargets[]` from Step 4. For each target (tenant, group, or user):

1. **Build the assignment array.** Every policy produced or reused in Phase 1 gets one `(productIdentifier, licenseTypeIdentifier, policyIdentifier)` entry, regardless of the policy's pack-declared `deploymentLevel` — the cascade reuses the same policies across every named scope.

2. **Delegate to [../../policy-assign.md](../../policy-assign.md).** That primitive handles the merge-first contract:
   - Read current scope state (`deployment tenant|group|user get <id>`).
   - Merge: `currentAssignments ∪ newAssignments` with new entries winning on conflict. **Every** existing `(product, licenseType)` slot the pack doesn't touch is preserved.
   - Write the merged array to a temp JSON file.
   - Call `deployment {tenant|group|user} configure <id>` with the level-specific name flag (`--tenant-name` / `--group` / `--user`) and `--input <file> --output json`. See [../../policy-assign.md](../../policy-assign.md) for the exact per-level invocation.

3. **Collect results** per target: `{ level, targetId, targetName, status, mergedAssignmentCount, addedAssignmentCount, replacedAssignmentCount, warnings[] }`. Halt on 4xx — remaining cascade targets become `status: "skipped", reason: "prior-failure"`.

**Count discipline.** Same pack, same set of policies, applied via the engineering-group cascade → **two** `configure` calls (one for tenant, one for the group). Same call count whether the pack has 1 or 20 product policies — the atomic configure API takes the full assignment list per target. If cascade is off (`"group-only"`), it's exactly one call (the named scope).

**Example — HIPAA tenant-wide (Act 2 UX path):**
```
Phase 2 (1 configure call):
  [TENANT] DefaultTenant ← 4 policies pinned (AITL, Development, Robot, StudioWeb)
```

**Example — SOC 2 to engineering group (Act 2 CLI path, cascade on):**
```
Phase 2 (2 configure calls):
  [TENANT] staging-tenant ← 3 policies pinned (AITL, Development, Robot)
  [GROUP]  engineering    ← 3 policies pinned (AITL, Development, Robot)
```

**Example — cascade off:**
```
Phase 2 (1 configure call):
  [GROUP] engineering ← 3 policies pinned (cascade disabled by prompt)
```

### Step 9 — Write deploy record

[deploy-record.md](deploy-record.md). Single JSON with `created[]` + `deployed[]` arrays. Always write — success, partial failure, or halt.

### Step 9.5 — Sync to Governance UI (best-effort, always runs)

After Phase 2 succeeds, mirror the result into the Governance UI server's local state so its pack-toggle reads "active" and the Policy Library page can chip-filter by pack. The UI server already does this work internally on its own PATCH toggle — but the skill does the AOPS create + assign over the CLI, so we just push the result instead of re-running it.

**Default URL: `http://localhost:3000/appsdev/portal_`** — the Experiences portal FE dev server (rsbuild port `3000`, account slug `appsdev`, gateway prefix `portal_`). The FE proxies `/api/*` through to the node server at `:8080`, and the node-server route mount uses a `.*` prefix regex (`apps/server/src/setup/baseUrl.ts`), so the same URL the FE calls reaches the sync handler. Override with `GOV_UI_SERVER_URL` only if running a non-default setup (different port, different account slug, or hitting the node server at `:8080` directly).

The pack-id mapping lives **on the server** in `apps/server/src/routes/CompliancePacks/CompliancePacks.ts` (`SKILL_PACK_ALIASES`). The skill always sends the pack's `manifest.json` packId from Step 2 — the server resolves it to the UI's canonical packId (e.g. `iso-42001-2023-aitl` → `iso-42001`).

Run when at least one `created[]` entry has `status` ∈ {`success`, `reused`}:

```bash
GOV_UI="${GOV_UI_SERVER_URL:-http://localhost:3000/appsdev/portal_}"
curl -fsS -X POST \
    -H "Content-Type: application/json" \
    -d '{
            "active": true,
            "externalPolicies": {
                "AITrustLayer": "<policyGuid>",
                "Development":  "<policyGuid>",
                "Robot":        "<policyGuid>"
            }
        }' \
    "$GOV_UI/api/compliancePacksSync/<manifestPackId>/sync"
```

`<manifestPackId>` = the `packId` field from `manifest.json` (NOT the filename, NOT a guess). The server's alias table covers every published pack; if the call returns 404 with `availablePacks` and `knownAliases` in the body, the alias is missing on the server — surface that to the user and stop. Do not try alternate IDs.

Build `externalPolicies` from `created[]`: key = `identifier` (productIdentifier), value = `policyId`. Include `reused` entries; skip `failed` and `skipped`.

On any other failure (connection refused — UI server not running, non-404 4xx, 5xx) — log a single warning and continue. The skill's primary contract is the AOPS apply + the deploy record; UI sync is decoration.

Surface a one-line confirmation in the report when sync ran:

```
Governance UI: synced pack iso-42001-2023-aitl → iso-42001 active (3 policies)
```

### Step 10 — Report

Group deployment with cascade (Act 2 CLI path):

```
Pack applied: soc2-type2-2017 v1.0.3 → cascade [tenant, group "engineering"] on staging-tenant

Created (3):
  ✓ AITrustLayer  → soc2-type2-2017-ai-trust-layer  (d0a68808-...)
  ✓ Development   → soc2-type2-2017-development     (f1b2c3d4-...)
  ✓ Robot         → soc2-type2-2017-robot           (7a8b9c0d-...)

Deployed (2 cascade targets, 3 policies each):
  ✓ [TENANT] staging-tenant    → +3 pinned, 0 replaced, 2 preserved
  ✓ [GROUP]  engineering (39 members) → +3 pinned, 0 replaced, 0 preserved

Deploy record: $HOME/uipath-governance/audit/deploy-records/deploy-record-soc2-type2-2017-20260423T200455Z.json
```

Tenant-only apply (Act 2 UX path):

```
Pack applied: hipaa-2024 v1.0.0 → tenant DefaultTenant

Created (4):
  ✓ AITrustLayer  → hipaa-2024-ai-trust-layer  (d0a68808-...)
  ✓ Development   → hipaa-2024-development     (f1b2c3d4-...)
  ✓ Robot         → hipaa-2024-robot           (7a8b9c0d-...)
  ✓ StudioWeb     → hipaa-2024-studio-web      (e5f6a7b8-...)

Deployed (1 target, 4 policies):
  ✓ [TENANT] DefaultTenant → +4 pinned, 0 replaced, 0 preserved

Deploy record: $HOME/uipath-governance/audit/deploy-records/deploy-record-hipaa-2024-20260423T201030Z.json
```

Reuse path (Critical Rule #5 carve-out, user confirmed):

```
Pack applied: soc2-type2-2017 v1.0.3 → cascade [tenant, group "engineering"]

Reused (3) — policies already existed from an earlier Apply run:
  ↻ AITrustLayer  → soc2-type2-2017-ai-trust-layer  (d0a68808-...)
      prior: deploy-record-soc2-type2-2017-20260420T091301Z.json
  ↻ Development   → soc2-type2-2017-development     (f1b2c3d4-...)
  ↻ Robot         → soc2-type2-2017-robot           (7a8b9c0d-...)

Deployed (2 targets — new scope added to existing policies):
  ✓ [TENANT] staging-tenant → 0 replaced, 3 preserved
  ✓ [GROUP]  engineering    → +3 pinned (first time this group gets SOC 2)

Deploy record: <path>
```

## Dispatch Table (within this capability)

| Phase | `policyKind` | `productIdentifier` | Action |
|---|---|---|---|
| Creation | `product` (or absent) | `AITrustLayer` | CREATE recipe + [products/ai-trust-layer.md](products/ai-trust-layer.md) |
| Creation | `product` (or absent) | `Assistant` | CREATE recipe + [products/assistant.md](products/assistant.md) |
| Creation | `product` (or absent) | `AssistantWeb` | CREATE recipe + [products/assistant-web.md](products/assistant-web.md) |
| Creation | `product` (or absent) | `Development` | CREATE recipe + [products/development.md](products/development.md) + shared [_studio-family.md](products/_studio-family.md) |
| Creation | `product` (or absent) | `Business` | CREATE recipe + [products/business.md](products/business.md) + shared [_studio-family.md](products/_studio-family.md) |
| Creation | `product` (or absent) | `Automate` | CREATE recipe + [products/automate.md](products/automate.md) + shared [_studio-family.md](products/_studio-family.md) |
| Creation | `product` (or absent) | `StudioPro` | CREATE recipe + [products/studio-pro.md](products/studio-pro.md) + shared [_studio-family.md](products/_studio-family.md) |
| Creation | `product` (or absent) | `Robot` / `StudioWeb` / `IntegrationService` | CREATE recipe only (no documented quirks — templates are minimal or not published) |
| Creation | `product` (or absent) | any unknown | CREATE recipe only; add a quirks file if you hit recurring errors |
| Creation | `access` | any | **SKIP** (access-policy CLI pending branch merge; record as `access-policies-not-yet-supported`) |
| Deployment | `product` (or absent) | any | [../../policy-assign.md](../../policy-assign.md) — tenant / group / user branch |

## Adding support for a new product's quirks

The shared CREATE recipe handles any AOPS product by default. Create a `products/<product>.md` file **only when you hit a real quirk worth documenting** — wrong-type CLI values, non-obvious enum constraints, conditional field dependencies, or recurring error patterns.

Template (follow [products/ai-trust-layer.md](products/ai-trust-layer.md) as the reference):

```markdown
# Compliance · <Product Label> — product quirks

Product-specific CLI value conventions and error patterns for `productIdentifier: "<Product>"`.
Follow the shared CREATE recipe in [../../../policy-crud.md](../../../policy-crud.md).

## Product identifiers
| Field | Value |
|---|---|
| `--product-name` | `<ExactProductIdentifier>` |
| Default license | `<NoLicense | Attended | Development | ...>` |

## CLI value quirks — will cause 400 if wrong
| Property | Expected type / values |
|---|---|
| ... | ... |

## Error triage
| Error message fragment | Likely cause | Action |
|---|---|---|
| ... | ... | ... |
```

Do NOT pre-create stub files for products without documented quirks. An empty file adds noise and no signal.

## Anti-Patterns

- **Never invent product quirks.** If the shared CREATE recipe works, no product file is needed.
- **Never prompt for scenario choice.** Derive from the user's prompt per [scope-selection.md](scope-selection.md).
- **Never run phases or policies in parallel.** Sequential = predictable fail-fast boundary.
- **Never auto-pick a group / user.** Always surface candidates for explicit selection at Step 4.5.
- **Never silently skip cascade.** If the user named a group or user, the default is tenant + that scope (defense in depth). Cascade turns off only on explicit opt-out phrasing — if the user didn't say "group-only" / "don't touch tenant", include tenant.
- **Never silently fall back to `update` on 409.** The only carve-out is the user-confirmed reuse path in [Step 5.5](#step-55--pre-apply-409-check--prior-deploy-reuse) — and that reuse never modifies the existing policy's content, only adds new deployment bindings.
- **Never create the same policy twice across cascade targets.** One synthesized policy per `(pack, clauseScope, product)` binds to every cascade target via separate `configure` calls — not duplicated.
- **Never hand-edit `formData`.** Pack is the source of truth; `policy-crud` handles the defaults merge via `merge-overrides.mjs`.
- **Never silently drop a skipped policy.** Always record in `deploy-record.created[]` with a reason.
- **Never skip tenant-intent validation** when the user's prompt names a tenant — see [auth-context.md#tenant-intent-validation](../../auth-context.md#tenant-intent-validation-apply--advise--diagnose). Wrong-tenant applies are catastrophic; one-second check prevents one-hour cleanup.
