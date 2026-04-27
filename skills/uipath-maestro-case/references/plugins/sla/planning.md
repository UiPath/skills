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
| **Default SLA** | The time-based catch-all SLA. One per target (root or stage). Written into `data.slaRules[]` with `expression: "=js:true"`. |
| **Conditional SLA rules** | Expression-driven SLA overrides. Root-only. Prepended to `root.data.slaRules[]` ahead of the default. |
| **Escalation rules** | Notifications triggered at-risk or on breach. Attached to a specific rule via `escalationRule[]`. |

## Applying SLA at Root vs Stage

- **Root** — the default SLA for the whole case. Target `"root"`; written to `root.data.slaRules[]`.
- **Stage** — stage-specific SLA. Target `"<stage-name>"`; written to the stage node's `data.slaRules[]`. Overrides the root default while the stage is active.

Set root SLA first, then stage SLAs. This mirrors the schema precedence: stage > root.

> **Conditional SLA rules are root-only.** They live in `root.data.slaRules[]`; per-stage conditional SLA is not supported. If the sdd.md describes one, flag to the user.

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
| `recipient-target` | sdd.md | Recipient UUID. Mark `<UNRESOLVED: user-uuid for <email>>` / `<UNRESOLVED: group-uuid for <name>>` when sdd gives an email / group name but no UUID. |
| `recipient-value` | sdd.md | Display value (typically the email for User, group name for UserGroup). |
| `display-name` | sdd.md (optional) | |
| `target` | sdd.md target (root vs stage) | `"root"` or `"<stage-name>"` |
| `attach-to` | sdd.md | `default` (attach to the `=js:true` rule) or `T<m>` pointing to the conditional-rule T-entry the escalation fires under. |

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
  - User: <UNRESOLVED: user-uuid for manager@corp.com> / manager@corp.com
  - UserGroup: <UNRESOLVED: group-uuid for "Order Management Team"> / "Order Management Team"
- display-name: "Notify Manager"
- order: after T<m>
- verify: Confirm Result: Success, capture EscalationRuleId
```

**Recipient format:** `<target> / <value>` where `<target>` is the UUID (or `<UNRESOLVED: …>` sentinel when sdd only has an email / group name) and `<value>` is the display string. Skeleton recipients stay in `tasks.md` through execution; the user patches the UUID externally after the build and the completion report lists every unresolved recipient.

**`attach-to: default`** is the default. Use `T<m>` when sdd.md attaches an escalation to a specific conditional SLA rule.

## Anti-Patterns

- **Do not fabricate expression syntax.** Describe conditional SLA rules in natural language during planning; the execution phase handles the exact syntax.
- **Do not put conditional SLA rules on stages.** Conditional SLA rules live in `root.data.slaRules[]` only. Flag to the user if the sdd.md describes a per-stage conditional SLA.
- **Do not invert rule order.** Conditional rules are evaluated in insertion order — insert them in the priority order the sdd.md specifies.
