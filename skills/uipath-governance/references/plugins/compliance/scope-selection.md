# Scope Selection

Two **independent** axes control what gets applied and where it lands:

1. **Clause scope** — which clauses from the pack are in play (filters the pack's content). Obligation-level narrowing, specific clause IDs, NL phrase.
2. **Deployment target** — where the synthesized policies get bound (tenant / group / user). Derived from the user's prompt; cascades automatically when a narrower scope is named.

Both default to "everything tenant-wide" unless the user's prompt signals otherwise.

---

## Axis 1 — Clause scope

**Default: ALL clauses in the pack are in scope.** Do not ask the user to pick a scenario. Only narrow scope if the user's prompt explicitly signals it.

### Signal detection (text match on the user's prompt)

| Signal in prompt | Resulting `inScopeClauseIds` |
|---|---|
| (none) | Every clause in `clause-map.json`. Default. |
| "mandatory", "required" | Clauses where `obligationLevel ∈ {Mandatory, ConditionalMandatory}`. Legacy `mandatory: true` counts as `Mandatory`. |
| "only strict mandatory", "exclude conditional" | `{Mandatory}` only — policy name tokened with `-mandatory-strict-` for auditability. |
| "mandatory + recommended", "recommended" (with "mandatory") | `{Mandatory, ConditionalMandatory, Recommended}` |
| "all including optional", "everything" | All four levels (same as default) |
| Clause ID mentioned ("A.8.11", "A.5.23 and A.8.15") | Exactly those IDs. Validate each exists; unknown IDs halt. |
| Descriptive phrase ("data masking", "encryption controls") | NL match across `clause.name + clause.description`. Surface matches, require user confirmation before proceeding. |

### Confirmation rules

1. **Scope itself** — never ask. Derive from signals above and show a one-line preview at the pre-flight gate.
2. **NL match** — always confirm the matched clause list before proceeding (fuzzy matching is unreliable).
3. **`ConditionalMandatory` clauses** — for each one in scope, show the `condition` string and require explicit user approval before including it.
4. **Pre-flight** — one final "proceed?" before any CLI side effects. That's the only global confirmation.

### Filter to policy files

Only policy files with at least one in-scope contributing clause are passed to Phase 1. A file whose every contributor is out of scope is **skipped** and recorded as `status: "skipped"` in the deploy record.

```python
inScopePolicyFiles = { contrib.uipolicyFile
                       for clause in clauses if clause.id in inScopeClauseIds
                       for contrib in clause.contributions }
```

---

## Axis 2 — Deployment target (the *where* — with automatic cascade)

The deployment target determines where the synthesized policies get bound. The user names the **narrowest** scope they intend to apply to; the skill automatically cascades upward so the policy is enforced at every layer above. Defense-in-depth by default: a policy pinned at a user scope is also pinned at the group and tenant scopes, so every request path is covered.

### Signal detection + resulting bindings

| Signal in prompt | Named scope | Resulting bindings |
|---|---|---|
| (none) / "apply to tenant" / "tenant-wide" | tenant | `[tenant]` |
| "apply to the engineering group" / "on the Finance group" / "for the data-science team" | group X | `[tenant, group X]` |
| "apply to user priya@medcore.com" / "for Jane Doe only" | user Y | `[tenant, group(optional), user Y]` |

**Why cascade.** AOPS resolves the effective policy at request time via `USER → GROUP → TENANT → GLOBAL`. A policy pinned only at a group leaves that group's members **still** inheriting whatever is pinned at the tenant scope for the same `(product, licenseType)` slot — which may be global defaults (nothing pinned). Cascading the same policy to tenant guarantees uniform enforcement regardless of which layer the request resolves through first. The caller can opt out explicitly (see "narrow binding only" below).

### User-scope cascade — group layer is optional

For a user-scope override, the group layer is included **only if the user's prompt also names a group** (e.g., *"apply to user jane in the engineering group"*). If the prompt names only a user, the cascade skips the group layer (we don't infer group memberships from IDM — multi-group users would be ambiguous). The preview calls out the skipped layer.

```
Will DEPLOY to:
  [TENANT]         DefaultTenant
  [USER]           jane@medcore.com
                   (group layer skipped — prompt did not name a group)
```

### Narrow binding only — opt-out phrasing

When the user says *"just the engineering group, not tenant-wide"* / *"group-only"* / *"without touching tenant scope"*, disable the cascade and bind only at the named scope. Cascading is the default because defense-in-depth is the safe answer; opt-out exists because explicit narrow scope is occasionally required (e.g., piloting a stricter policy on one group without changing tenant posture).

| Prompt phrasing | Cascade behavior |
|---|---|
| "apply to engineering group" (default) | `[tenant, group engineering]` — cascade on |
| "apply ONLY to engineering group" / "group-only" / "don't touch tenant" | `[group engineering]` — cascade off |

### Principal resolution — happens before pre-flight

When the target names a group or user, the orchestrator resolves the principal GUID via [../../principals-lookup.md](../../principals-lookup.md) **before** pre-flight so the preview shows the concrete GUID and display name. If resolution fails (ambiguous match, no match, or the user declines the offered candidate), halt with an error.

### Pack-declared `deploymentLevel` — defaults, not constraints

The pack's `manifest.policies[].deploymentLevel` (or the policy file's top-level `deploymentLevel`) is the **default** deployment target for that entry — used only when the user's prompt gives no override. When the user provides a deployment target override, it **wins globally** — every applicable entry in the pack lands at the user's named cascade. Pack-declared group/user entries without a concrete principal GUID in the user's prompt are recorded as `skipped` with reason `pack-declared-non-tenant-needs-prompt-override` — they cannot be applied without explicit user intent.

### Composition example

*"apply SOC 2 Mandatory clauses to the engineering group on staging tenant"* → both axes active:

```
inScopeClauseIds          = every SOC 2 clause where obligationLevel ∈ {Mandatory, ConditionalMandatory}
inScopeDeploymentTargets  = [tenant, group "engineering"]     (cascade on by default)
inScopePolicyFiles        = pack entries whose contributing clauses intersect the clause filter
```

Present the selection at pre-flight so the user knows exactly what will happen:

```
Scope narrowed:
  By obligation level:  12/17 clauses (Mandatory + ConditionalMandatory)
  Deployment target:    tenant DefaultTenant + group "engineering" (<guid>)
  Policy files applied: 3  (ai-trust-layer, development, robot)
  Policy files skipped: 1  (studio-web — no in-scope contributing clauses)
```
