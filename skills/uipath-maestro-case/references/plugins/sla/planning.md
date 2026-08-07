# sla — Planning

## When to Use

Use for an sdd.md deadline, time-to-complete expectation, conditional duration, at-risk notification, or breach escalation.

## Three Sub-Operations

| Sub-operation | Contract |
|---|---|
| **Default SLA** | One `expression: "=js:true"` catch-all per target. |
| **Conditional SLA rule** | A condition-driven root or stage override evaluated before the default. |
| **Escalation rule** | An at-risk or breach notification in a rule's `escalationRule[]`; its ID may drive an `sla-status-change` response. |

## Targets and Rule Order

- **Root:** target `"root"`; implementation writes `metadata.slaRules[]`.
- **Stage:** target `"<stage-name>"`; write the `case-management:Stage` node's `data.slaRules[]`. Secondary stages are supported; stage SLA overrides root while active.

Set root before stage SLAs. Persist conditional rules in SDD priority order before the trailing default; either kind may own escalations. See [target resolution](impl-json.md#target-resolution).

## Required Fields from sdd.md

### Default SLA

- Positive integer `count`; `unit`: `min` | `h` | `d` | `w` | `m`; `target`: `"root"` or a stage name.
- Preserve `display-name` from the case-metadata or Stage SLA title; if absent, ask or use and record `SLA Rule {N}`.
- Preserve `rationale` for the target, duration, threshold, and escalation behavior.

### Conditional SLA rule

Carry the default fields plus the SDD `expression` as natural-language `condition`; do not invent executable syntax. First truthy rule wins, then the default.

### Escalation rule

- `trigger-type`: `at-risk` or `sla-breached`; preserve `at-risk-percentage` whenever type is `at-risk` (frontend validates presence, not its numeric range here).
- `recipient-scope`: `User` or `UserGroup`; `recipient-target`: resolved UUID or established unresolved sentinel; `recipient-value`: original display value.
- Preserve the escalation-table `display-name`; if absent, use and record `Escalation Rule {N}`.
- `target`: root or stage; `attach-to`: `default` or the conditional rule's `T<m>`.
- `rationale`: preserve reviewer context and, when applicable, the secondary response lane and why it is global or interrupting.

## Identity Resolution

Resolve only in Phase 1 while authoring an escalation T-entry; Phase 0 retains the SDD string. Recipient-free SLAs load no recipient guide.

If a recipient value matches `^[0-9A-Fa-f]{8}-[0-9A-Fa-f]{4}-[0-9A-Fa-f]{4}-[0-9A-Fa-f]{4}-[0-9A-Fa-f]{12}$`, preserve its spelling, make no directory call, and do not load the conditional guide. Write `<uuid> / <uuid>` in `tasks.md`, then append the ordinary audit object described below with rationale `uuid-pass-through`.

For a non-UUID `User` email or `UserGroup` name, read [SLA Recipient Resolution](recipient-resolution-guide.md) directly before that recipient's T-entry; it owns lookup, candidates, cache, failure, and non-UUID audit.

### Audit — `tasks/recipients-resolved.json`

For UUID pass-through, initialize `[]` if absent, then Read and incrementally Edit-append exactly these six keys:

```json
{
  "sddInput": "A1B2C3D4-0000-0000-0000-000000000000",
  "kind": "user",
  "searchTerm": "A1B2C3D4-0000-0000-0000-000000000000",
  "allCandidates": [],
  "selected": "A1B2C3D4-0000-0000-0000-000000000000",
  "rationale": "uuid-pass-through"
}
```

Map scope to `kind` (`User` → `user`, `UserGroup` → `group`); fabricate no candidate.

## Planning Order

SLA is the last `tasks.md` category, after conditions. For each target, plan:

1. Default SLA T-entry
2. Conditional SLA T-entries
3. Escalation T-entries, one per rule

## `tasks.md` Entry Shapes

### Default SLA

```markdown
## T<n>: Set default SLA for "<target>" to <duration>
- target: "root" | "<stage-name>"
- display-name: "SLA Rule 1"
- rationale: "<why this target and duration fit>"
- count: 5
- unit: d
- order: after T<m>
- verify: Confirm Result: Success
```

### Conditional SLA rule

```markdown
## T<n>: Add conditional SLA rule for "<target>" — <condition summary>
- target: "root" | "<stage-name>"
- display-name: "Urgent SLA"
- rationale: "<why this condition changes the SLA>"
- condition: "<natural-language condition from sdd.md>"
- count: 30
- unit: min
- order: after T<m>
- verify: Confirm Result: Success
```

### Escalation rule

```markdown
## T<n>: Add escalation rule for "<target>" — <trigger summary>
- target: "root" | "<stage-name>"
- attach-to: default | T<m>
- rationale: "<why this threshold, recipient, and response fit>"
- trigger-type: at-risk
- at-risk-percentage: 80
- recipients:
  - User: a1b2c3d4-0000-0000-0000-000000000000 / manager@corp.com
  - UserGroup: <UNRESOLVED: group-uuid for "Order Management Team"> / "Order Management Team"
- display-name: "Notify Manager"
- order: after T<m>
- verify: Confirm Result: Success, capture EscalationRuleId
```

Recipient syntax is `<target> / <value>`. Preserve a resolved UUID or unresolved sentinel as `target` and the original display string as `value`; unresolved recipients survive execution and appear in the completion report. `attach-to: default` is the default; use `T<m>` for a specific conditional parent.

## Frontend Validation Parity

Before emitting SLA entries, require:

- non-empty, target-unique, colon-free SLA and escalation display names;
- positive SLA counts, with minute values from 15 through 1000 inclusive;
- a condition for every non-default rule;
- at least one recipient per escalation; and
- `at-risk-percentage` on every `at-risk` escalation.

## Anti-Patterns

- Do not fabricate condition syntax during planning.
- Do not lose root-versus-stage target or invert conditional priority.
- Do not bypass the direct non-UUID resolver route, except after its session-wide skip state is active.
- Do not fabricate or first-pick a UUID; only the exact gates or an explicit user selection resolve a recipient.
- Do not replace a failed or declined resolution with anything other than the established unresolved sentinel.
