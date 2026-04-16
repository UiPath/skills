---
name: uipath-compliance-applier
description: "[PREVIEW · AITL-only] Apply AI Trust Layer compliance from .uipolicy packs to tenant/group/user via `uip admin aops-policy`. Two phases: create then deploy. Other products/access TBD. For authoring→uipath-compliance-pack-author."
allowed-tools: Bash, Read, Write, Edit, Glob, Grep
---

# UiPath Compliance Applier (AITL-only, V1)

Apply a compiled `.uipolicy` compliance pack to a UiPath tenant — **AI Trust Layer (AITrustLayer) policies only** in this version. Two phases: creation, then deployment. All other products and access policies in the pack are **skipped with a notice** and recorded in the deploy record.

## Current version scope

| In scope | Out of scope (skipped with notice) |
|---|---|
| `policyKind: "product"` with `productIdentifier: "AITrustLayer"` | `productIdentifier`: `Robot`, `Development`, `StudioWeb`, `StudioPro`, `Assistant`, `AssistantWeb`, `Automate`, `Business`, `IntegrationService` |
| Deployment levels: `tenant`, `group`, `user` | — |
| Creation CLI: `uip admin aops-policy create` | — |
| Assignment CLIs: `uip admin aops-policy assign-tenant` / `assign-group` / `assign-user` | — |
| | `policyKind: "access"` (ToolUsePolicy, AccessControlPolicy) — all skipped |

> **Non-AITL policies are not an error.** A pack containing AITL + three other products runs AITL end-to-end and lists the other three as `status: "skipped", reason: "out-of-version-scope"` in the deploy record. The run is considered successful if all AITL policies succeed.

## When to Use This Skill

- "Apply ISO 27001 AI Trust Layer policy to my tenant"
- "Apply the AITL portions of this compliance pack"
- "Deploy this already-created AITL policy to the Finance group"
- "Create AITL policies from the pack but don't deploy yet"

DO NOT use for:
- Non-AITL product policies (Robot, Studio, etc.) — out of scope in V1
- Access policies (ToolUse / AccessControl) — out of scope in V1
- Pack authoring
- Ad-hoc single-policy creation

## Invocation Modes

| Mode | Trigger | Runs |
|---|---|---|
| Full apply (default) | "apply ISO 27001" | Phase 1 (create AITL) + Phase 2 (deploy AITL) |
| Create-only | "just create", "--skip-deploy" | Phase 1 only |
| Deploy-only | "deploy this policy", "--skip-create" + policy ID | Phase 2 only (policy must be AITL — reject otherwise) |

## Critical Rules

1. **Process AITL policies only.** For every non-AITL policy file in the pack, skip it without calling any CLI. Record it as `status: "skipped", reason: "out-of-version-scope"` in the deploy record. Do NOT call `_shared.md` fallback — there is no fallback in V1.
2. **Scope defaults to ALL clauses.** Narrow only when the user's prompt explicitly signals it (obligation level, specific clause IDs, or NL phrase). Never ask for scenario choice.
3. **Deployment level defaults to `policy.deploymentLevel`.** Override if user prompt names a group or user. If level is `group`/`user` and no target named, call the [principals plugin](references/plugins/deployment/principals/impl.md) and prompt.
4. **Prompt only when necessary** — one pre-flight confirmation with scope + skip-list preview; one principal-selection prompt per group/user deployment; one confirmation per `ConditionalMandatory` clause. Nothing else.
5. **Dispatch rule is narrow.** `policyKind="product" AND productIdentifier="AITrustLayer"` → AITL plugin. Every other combination → skip.
6. **Fail-fast per phase.** A 4xx on an AITL policy halts that phase. Skipped (out-of-scope) policies never hit the CLI and never cause halts.
7. **No `update` fallback on 409.** Halt with the conflict surfaced.
8. **`--output json` on every `uip` call.** Parse `Data` / `Message`.
9. **Deploy-only mode rejects non-AITL `policyId`s.** Look up the policy via `uip admin aops-policy get <id>` first; if `product.name != "AITrustLayer"`, refuse and exit.
10. **Write the deploy record unconditionally**, including skipped non-AITL policies.

## Workflow

### Step 0 — Preflight

```bash
uip login status --output json
```
Require `Data.Status == "Logged in"`.

### Step 1 — Resolve the pack

[references/pack-resolution.md](references/pack-resolution.md). Accepts `--pack-file <path>` (V0), `--pack-url <url>`, or `--pack-id <id> [--pack-version <v>]`.

### Step 2 — Parse

[references/pack-format.md](references/pack-format.md). Read `manifest.json`, `clause-map.json`, every `policies/*.json`.

### Step 3 — Partition policies by AITL eligibility

Iterate `manifest.policies[]`. Two buckets:

```
applicable  = [ p for p in manifest.policies
                if p.product == "AITrustLayer" ]
skipped     = [ p for p in manifest.policies
                if p.product != "AITrustLayer" or p.accessPolicyType is not None ]
```

Log the split to the user:
```
Pack: iso-27001-2022 v1.0.0
Applicable (AITL, 1 file): policies/ai-trust-layer.json
Skipped (out of V1 scope, 3 files):
  - policies/development.json (Development)
  - policies/robot.json (Robot)
  - policies/studio-web.json (StudioWeb)
```

### Step 4 — Determine scope

[references/scope-selection.md](references/scope-selection.md). Default: all clauses. Narrow only on explicit signal.

Pre-flight confirmation:
```
Pack: iso-27001-2022 v1.0.0
Scope: all (9 clauses, AITL contributors: 7)
Will CREATE: 1 AITL policy
Will DEPLOY to: tenant DefaultTenant
Will SKIP (out of V1 scope): 3 non-AITL policies
Proceed? (y/n)
```

Require `y`. Anything else halts with no side effects.

### Step 5 — Synthesize

[references/synthesis-algorithm.md](references/synthesis-algorithm.md). Fast vs. subset path decided per AITL file.

### Step 6 — Phase 1: CREATE (AITL only)

For each `applicable` policy file:
- **Dispatch →** [references/plugins/creation/aops/ai-trust-layer/impl.md](references/plugins/creation/aops/ai-trust-layer/impl.md)
- Collect `{ policyId, status, warnings[] }` per file.

For each `skipped` policy file:
- Append to `deploy-record.created[]` with `status: "skipped", reason: "out-of-version-scope"`.
- No CLI call.

Halt on any AITL 4xx (remaining AITL files become `status: "skipped", reason: "prior-failure"`).

### Step 7 — Phase 2: DEPLOY (AITL only)

Skip if `--skip-deploy`. Otherwise for each AITL policy with `created.status == "success"`:

1. **Determine deployment level** — from user prompt override, or from `policy.deploymentLevel` in the pack file (default `tenant`).
2. **If level ∈ {group, user}** and no `targetId` supplied: call [deployment/principals/impl.md](references/plugins/deployment/principals/impl.md) to fetch candidates and prompt for selection.
3. **Dispatch →** [deployment/aops/impl.md](references/plugins/deployment/aops/impl.md). Use the tenant / group / user branch matching the resolved level.

Collect `{ assignmentId, scope, status, warnings[] }` per policy. Halt on 4xx (remaining become `status: "skipped", reason: "prior-failure"`).

Non-AITL policies from the pack never appear in `deployed[]` — they were dropped in Step 3.

### Dispatch Table

| Phase | `policyKind` | `productIdentifier` | Action |
|---|---|---|---|
| Creation | `product` | `AITrustLayer` | [creation/aops/ai-trust-layer/impl.md](references/plugins/creation/aops/ai-trust-layer/impl.md) |
| Creation | `product` | any other | **SKIP** (record `out-of-version-scope`) |
| Creation | `access` | any | **SKIP** (record `out-of-version-scope`) |
| Deployment | `product` | `AITrustLayer` | [deployment/aops/impl.md](references/plugins/deployment/aops/impl.md) — tenant / group / user branches |
| Deployment helper | — | — | [deployment/principals/impl.md](references/plugins/deployment/principals/impl.md) (groups & users lookup) |

### Step 8 — Deploy record

[references/deploy-record.md](references/deploy-record.md). Single JSON, `created[]` + `deployed[]` arrays. Include the skipped non-AITL policies.

### Step 9 — Report to user

```
AITL policy created: iso-27001-2022-AITrustLayer (<guid>)  →  deployed to tenant DefaultTenant
Skipped (V1 scope): Development, Robot, StudioWeb
Deploy record: ./deploy-record-iso-27001-2022-<ts>.json
```

## Anti-Patterns

- **Never attempt to create a non-AITL policy in V1.** Skip, don't fall back. `_shared.md` is authoritative reference material, not a fallback plugin in this version.
- **Never prompt the user for scenario choice.** Derive from their prompt.
- **Never run phases or policies in parallel.**
- **Never auto-pick a group / user.** Always surface candidates for selection.
- **Never hand-edit `formData`.** Pack is source of truth.
- **Never silently drop a skipped policy.** Always record it in `deploy-record.created[]` with `status: "skipped", reason: "out-of-version-scope"`.
- **Never commit the deploy record.** Contains tenant / principal identifiers.

## References

- **[Pack Format](references/pack-format.md)** · **[Pack Resolution](references/pack-resolution.md)** · **[Scope Selection](references/scope-selection.md)**
- **[Synthesis Algorithm](references/synthesis-algorithm.md)** · **[Deploy Record](references/deploy-record.md)** · **[CLI Cheat Sheet](references/cli-cheatsheet.md)**
- **Creation · AITL:** [aops/_shared.md](references/plugins/creation/aops/_shared.md) (base recipe) · [ai-trust-layer/impl.md](references/plugins/creation/aops/ai-trust-layer/impl.md) (product specifics)
- **Deployment:** [aops/impl.md](references/plugins/deployment/aops/impl.md) · [principals/impl.md](references/plugins/deployment/principals/impl.md)
