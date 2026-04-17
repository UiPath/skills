# sla — Planning

SLA duration settings, escalation rules, and conditional SLA overrides. Applied at either root (whole case) or stage level.

## When to Use

Pick this plugin whenever the sdd.md mentions deadlines, service-level agreements, time-to-complete expectations, or escalation notifications:

- "This case must resolve within 5 days"
- "Notify the manager when the SLA is at 80% risk"
- "If the case is flagged Urgent, use a 30-minute SLA"
- "Escalate to the group when the SLA breaches"

## Three Sub-Operations (one plugin, three workflows)

| Sub-op | CLI | Purpose |
|--------|-----|---------|
| **Default SLA** | `sla set` | The time-based catch-all SLA. One per target (root or stage). |
| **Conditional SLA rules** | `sla rules add` | Expression-driven SLA overrides. Root-only. |
| **Escalation rules** | `sla escalation add` | Notifications triggered at-risk or on breach. |

## Applying SLA at Root vs Stage

- **Root** — the default SLA for the whole case. Omit `--stage-id`.
- **Stage** — stage-specific SLA. Pass `--stage-id <id>`. Overrides the root default while the stage is active.

Set root SLA first, then stage SLAs. This mirrors the schema precedence: stage > root.

> **Conditional SLA rules are root-only.** `sla rules add` does not accept `--stage-id`. If the sdd.md describes a per-stage conditional SLA, that semantics is not supported by the CLI — flag to the user.

## Required Fields from sdd.md

### Default SLA (`sla set`)

| Field | Source | Notes |
|-------|--------|-------|
| `count` | sdd.md duration number | Positive integer |
| `unit` | sdd.md duration unit | `h` \| `d` \| `w` \| `m` |
| `stage-id` | sdd.md target (root vs stage) | Omit for root |

### Conditional SLA rule (`sla rules add`)

| Field | Source | Notes |
|-------|--------|-------|
| `expression` | sdd.md condition | Natural-language in planning; the execution phase translates. **Do not fabricate syntax during planning.** |
| `count`, `unit` | sdd.md duration for this condition | Same units as default |

Rules are evaluated in insertion order — first truthy expression wins. The default SLA (set via `sla set`) acts as the fallback.

### Escalation rule (`sla escalation add`)

| Field | Source | Notes |
|-------|--------|-------|
| `trigger-type` | sdd.md | `at-risk` \| `sla-breached` |
| `at-risk-percentage` | sdd.md | Required when `trigger-type: at-risk` (1–99) |
| `recipient-scope` | sdd.md | `User` \| `UserGroup` |
| `recipient-target` | sdd.md | Identifier for the recipient |
| `recipient-value` | sdd.md | Display value for the recipient |
| `display-name` | sdd.md (optional) | |
| `stage-id` | sdd.md target (root vs stage) | Omit for root |

## Ordering

SLA is the **last** category in `tasks.md` (§4.8), after conditions. For each target, order within the target:

1. `sla set` — default SLA
2. `sla rules add` — conditional rules (root only)
3. `sla escalation add` — one call per escalation rule

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
- unit: m
- order: after T<m>
- verify: Confirm Result: Success
```

### Escalation rule

```markdown
## T<n>: Add escalation rule for "<target>" — <trigger summary>
- target: "<root>" | "<stage-name>"
- trigger-type: at-risk
- at-risk-percentage: 80
- recipients:
  - User: manager@corp.com
  - UserGroup: "Order Management Team"
- display-name: "Notify Manager"
- order: after T<m>
- verify: Confirm Result: Success, capture EscalationRuleId
```

## Anti-Patterns

- **Do not fabricate expression syntax.** Describe conditional SLA rules in natural language during planning; the execution phase handles the exact syntax.
- **Do not put conditional SLA rules on stages.** The CLI does not support `sla rules add --stage-id`. Flag to the user if the sdd.md describes one.
- **Do not invert rule order.** Conditional rules are evaluated in insertion order — insert them in the priority order the sdd.md specifies.
