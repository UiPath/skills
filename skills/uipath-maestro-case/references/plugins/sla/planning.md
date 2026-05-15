# sla — Planning

SLA duration settings, escalation rules, and conditional SLA overrides. Applied at either root (whole case) or stage level.

## When to Use

Pick this plugin whenever the sdd.md mentions deadlines, service-level agreements, time-to-complete expectations, or escalation notifications:

- "This case must resolve within 5 days"
- "Notify the manager when the SLA is at 80% risk"
- "If the case is flagged Urgent, use a 30-minute SLA"
- "Escalate to the group when the SLA breaches"

## Three Sub-Operations (one plugin, three workflows)

| Sub-op | Purpose |
|--------|---------|
| **Default SLA** | The time-based catch-all SLA. One per target (root or stage). Written into the SLA rules array with `expression: "=js:true"`. Path schema-dependent — see [impl-json.md § Target resolution](impl-json.md). |
| **Conditional SLA rules** | Expression-driven SLA overrides. Root-only. Prepended to the root SLA rules array ahead of the default. |
| **Escalation rules** | Notifications triggered at-risk or on breach. Attached to a specific rule via `escalationRule[]`. |

## Applying SLA at Root vs Stage

- **Root** — the default SLA for the whole case. Target `"root"`; written to the root SLA rules array (v19: `root.data.slaRules[]`; v20: `metadata.slaRules[]` — see Rule 18).
- **Stage** — stage-specific SLA. Target `"<stage-name>"`; written to the stage node's `data.slaRules[]` (unchanged across schemas). Overrides the root default while the stage is active.

Set root SLA first, then stage SLAs. This mirrors the schema precedence: stage > root.

> **Conditional SLA rules are root-only.** They live in the root SLA rules array (v19: `root.data.slaRules[]`; v20: `metadata.slaRules[]`); per-stage conditional SLA is not supported. If the sdd.md describes one, flag to the user.

> **ExceptionStage SLA is supported.** Author it the same way as a regular Stage SLA — write `data.slaRules[]` on the `case-management:ExceptionStage` node. See [`impl-json.md`](impl-json.md).

> **Per-conditional-rule escalations are supported.** Attach an escalation rule to any entry in `slaRules[]`, not only the default `"=js:true"` rule.

## Required Fields from sdd.md

### Default SLA

| Field | Source | Notes |
|-------|--------|-------|
| `count` | sdd.md duration number | Positive integer |
| `unit` | sdd.md duration unit | `min` \| `h` \| `d` \| `w` \| `m` |
| `target` | sdd.md target (root vs stage) | `"root"` or `"<stage-name>"` |

### Conditional SLA rule

| Field | Source | Notes |
|-------|--------|-------|
| `expression` | sdd.md condition | Natural-language in planning; the execution phase translates. **Do not fabricate syntax during planning.** |
| `count`, `unit` | sdd.md duration for this condition | Same units as default |

Rules are evaluated in insertion order — first truthy expression wins. The default SLA acts as the fallback.

### Escalation rule

| Field | Source | Notes |
|-------|--------|-------|
| `trigger-type` | sdd.md | `at-risk` \| `sla-breached` |
| `at-risk-percentage` | sdd.md | Required when `trigger-type: at-risk` (1–99) |
| `recipient-scope` | sdd.md | `User` \| `UserGroup` |
| `recipient-target` | sdd.md → resolver | Recipient UUID. When sdd gives an email or group name, run [§ Identity Resolution](#identity-resolution) — resolved UUID written inline. On resolver failure or user decline, mark `<UNRESOLVED: user-uuid for <email>>` / `<UNRESOLVED: group-uuid for <name>>`. |
| `recipient-value` | sdd.md | Display value (typically the email for User, group name for UserGroup). |
| `display-name` | sdd.md (optional) | |
| `target` | sdd.md target (root vs stage) | `"root"` or `"<stage-name>"` |
| `attach-to` | sdd.md | `default` (attach to the `=js:true` rule) or `T<m>` pointing to the conditional-rule T-entry the escalation fires under. |

## Identity Resolution

When sdd gives an escalation recipient as an email (`User: manager@corp.com`) or group name (`UserGroup: "Order Management Team"`), resolve to a directory UUID via `uip admin` while authoring the T-entry. Resolved UUIDs land inline in `tasks.md`; [`impl-json.md`](impl-json.md) writes them straight into `escalationRule[].action.recipients[].target` — no sentinel needed. Resolution runs **Phase 1 only** — Phase 0 still records email / group name as a string in sdd.md.

### Skip — UUID pass-through

Recipient value already matches `^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$` → skip CLI. Write `<uuid> / <uuid>` in tasks.md. Audit rationale: `uuid-pass-through`.

### Resolve `User`

1. `uip admin users list --search "<email>" --output json`
2. **Auto-accept** when response has exactly 1 entry AND `entry.email` equals sdd's email case-insensitively. Write `User: <id> / <email>`. Rationale: `auto-exact-email`.
3. **Fallback** on any other shape (0, >1, partial). If sdd carries a display name, retry `--search "<display-name>"`. Merge results, dedupe by `id`.
4. **Ask** via AskUserQuestion with up to 3 candidates. Each option: label `<displayName>`, description `<email> · id=<uuid-first-8>...`. Final option: `Keep as <UNRESOLVED>`. Rationale: `user-picked-from-N` or `user-declined-keep-unresolved`.

### Resolve `UserGroup`

`uip admin groups list` has **no `--search` flag**. Filter client-side.

1. **Pull once.** First group lookup in the planning session: `uip admin groups list --output json`. Cache the array in memory for the rest of Phase 1.
2. **Exact match** — entries where `name` OR `displayName` equals sdd's group name case-insensitively. Exactly 1 match → write `UserGroup: <id> / "<group-name>"`. Rationale: `auto-exact-name`.
3. **Substring fallback** — case-insensitive substring on `name` / `displayName`. Any hits → AskUserQuestion with top 3 (alphabetical by `name`) + `Keep as <UNRESOLVED>`.
4. **Empty** — both filters return 0 → AskUserQuestion: `No matching group found for "<group-name>". Keep as <UNRESOLVED>?` with a single `Keep as <UNRESOLVED>` option. Do NOT fabricate "fuzzy candidates"; the user patches the UUID externally per the standard decline path. Rationale: `user-declined-keep-unresolved`.

### Session cache

In-memory, scoped to the Phase 1 run. Key: lowercased sdd input. **Positive resolutions only** — auto-accept results and user-picked UUIDs. Do NOT cache `Keep as <UNRESOLVED>` decisions; same recipient appearing in a later T-entry re-asks.

### CLI failure (auth / network / 403)

Non-zero exit from `uip admin ...` → AskUserQuestion:

```
Question: Identity resolution failed (<stderr first line>). How should we proceed?
Header:   Resolver failed
Options:
  - Retry (max 2 attempts)
      → re-run the same `uip admin ...`. Continue on success. After 2 failed retries the resolver auto-routes to "Skip resolution for this build" — do not loop further.
  - Skip resolution for this build
      → leave every recipient as <UNRESOLVED: ...>, log to tasks/build-issues.md, surface in completion report. Subsequent recipient lookups in this Phase 1 skip the CLI.
  - Abort planning
      → halt Phase 1.
```

### Audit — `tasks/recipients-resolved.json`

Append one object per resolution attempt (incremental Edit, mirroring `registry-resolved.json` discipline):

```json
{
  "sddInput": "manager@corp.com",
  "kind": "user",
  "searchTerm": "manager@corp.com",
  "allCandidates": [
    {"id": "a1b2c3d4-0000-0000-0000-000000000000", "email": "manager@corp.com", "displayName": "Anne Manager"}
  ],
  "selected": "a1b2c3d4-0000-0000-0000-000000000000",
  "rationale": "auto-exact-email"
}
```

Rationale values: `auto-exact-email`, `auto-exact-name`, `user-picked-from-N`, `user-declined-keep-unresolved`, `uuid-pass-through`, `cli-failed-skipped`.

## Ordering

SLA is the **last** category in `tasks.md` (§4.8), after conditions. For each target, order within the target:

1. Default SLA T-entry
2. Conditional SLA rule T-entries (root only)
3. Escalation rule T-entries (one per rule)

## tasks.md Entry Format

### Default SLA

```markdown
## T<n>: Set default SLA for "<target>" to <duration>
- target: "<root>" | "<stage-name>"
- count: 5
- unit: d
- order: after T<m>
- verify: Confirm Result: Success
```

### Conditional SLA rule

```markdown
## T<n>: Add conditional SLA rule for root case — <condition summary>
- condition: "<natural-language condition from sdd.md>"
- count: 30
- unit: min
- order: after T<m>
- verify: Confirm Result: Success
```

### Escalation rule

```markdown
## T<n>: Add escalation rule for "<target>" — <trigger summary>
- target: "<root>" | "<stage-name>"
- attach-to: default | T<m>
- trigger-type: at-risk
- at-risk-percentage: 80
- recipients:
  - User: a1b2c3d4-0000-0000-0000-000000000000 / manager@corp.com
  - UserGroup: <UNRESOLVED: group-uuid for "Order Management Team"> / "Order Management Team"
- display-name: "Notify Manager"
- order: after T<m>
- verify: Confirm Result: Success, capture EscalationRuleId
```

**Recipient format:** `<target> / <value>` where `<target>` is the resolved UUID (per [§ Identity Resolution](#identity-resolution)) — or `<UNRESOLVED: …>` sentinel when the resolver failed or the user declined — and `<value>` is the display string. Unresolved recipients survive into execution; the user patches the UUID externally after the build and the completion report lists every unresolved recipient.

**`attach-to: default`** is the default. Use `T<m>` when sdd.md attaches an escalation to a specific conditional SLA rule.

## Anti-Patterns

- **Do not fabricate expression syntax.** Describe conditional SLA rules in natural language during planning; the execution phase handles the exact syntax.
- **Do not put conditional SLA rules on stages.** Conditional SLA rules live in the root SLA rules array only (v19: `root.data.slaRules[]`; v20: `metadata.slaRules[]`). Flag to the user if the sdd.md describes a per-stage conditional SLA.
- **Do not invert rule order.** Conditional rules are evaluated in insertion order — insert them in the priority order the sdd.md specifies.
- **Do not skip the resolver to save a CLI call.** Email / group-name recipients MUST go through [§ Identity Resolution](#identity-resolution). Writing `<UNRESOLVED: ...>` directly without attempting `uip admin users/groups list` is a planning bug.
- **Do not fabricate UUIDs.** When the resolver returns 0 / multi / partial matches, AskUserQuestion or keep `<UNRESOLVED>` — never guess a UUID, never auto-pick the first candidate without the exact-email / exact-name gate.
- **Do not cache user declines.** Session cache holds positive resolutions only. Re-ask on each T-entry occurrence of the same unresolved recipient.
