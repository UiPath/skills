---
direct-json: supported
---

# sla — JSON Implementation

Authoritative when the matrix in [`case-editing-operations.md`](../../case-editing-operations.md) lists `sla = JSON`. Cross-cutting direct-JSON rules live in [`case-editing-operations-json.md`](../../case-editing-operations-json.md). For the CLI fallback, see [`impl-cli.md`](impl-cli.md).

## Purpose

Compose the `slaRules[]` array for each target (root or stage) in one write. Unlike the CLI's `sla set` / `sla rules add` / `sla escalation add` split, the JSON path groups all SLA T-entries by target and emits the full array in a single mutation.

## Input spec (from `tasks.md §4.8`)

| T-entry kind | Required fields | Notes |
|---|---|---|
| Default SLA | `target`, `count`, `unit` | One per target. Emitted as the `=js:true` entry, always last. |
| Conditional rule | `target: "root"`, `condition` (natural-language), `count`, `unit` | Root-only. Translated to `=js:<expr>` at execution; see Expression Translation below. |
| Escalation | `target`, `attach-to: T<m>` \| `default`, `trigger-type`, `at-risk-percentage?`, `recipients[]`, `display-name?` | `attach-to` points to the T-number of the parent rule (or the default). |

## ID generation

- Escalation: `esc_` + 6 chars. Per [`case-editing-operations-json.md § ID Generation`](../../case-editing-operations-json.md#id-generation).
- Conditional SlaRuleEntry: **no `id` field**. CLI never emits one; removal is by array index.

Record every `T<n> → esc_xxxxxx` in `id-map.json` under `{kind: "escalation", ruleExpression: "<parent rule expression>", target: "root" | "<stageId>"}`.

## Target resolution

- `target: "root"` → `schema.root.data.slaRules`
- `target: "<stage-name>"` → locate node by `data.label === <stage-name>`; write to `node.data.slaRules`
- Accepted node types: `case-management:Stage` **and `case-management:ExceptionStage`** (gap-fill, see Known CLI divergences)
- If the stage node isn't found, halt and AskUserQuestion with candidate stage labels + "Something else".

## Recipe — one target

After grouping T-entries by target, compose:

```json
"slaRules": [
  {
    "expression": "=js:<translated-condition-1>",
    "count": <n>, "unit": "<min|h|d|w|m>",
    "escalationRule": [ <escalations with attach-to == conditional-1-T-number> ]
  },
  { "...additional conditional rules in sdd order..." },
  {
    "expression": "=js:true",
    "count": <default.count>, "unit": "<default.unit>",
    "escalationRule": [ <escalations with attach-to == default> ]
  }
]
```

Emission rules:

1. **Conditional rules first, in T-entry order.** Priority = sdd order (top-most wins). Matches CLI's final-array semantics.
2. **Default rule (`=js:true`) last.** Always emitted when any SLA T-entry targets this node — even escalation-only cases.
3. **Bare default rule is legal.** If a target has escalations but no `sla set` T-entry, emit `{expression:"=js:true", escalationRule:[…]}` with no `count` / `unit`. Matches CLI's `getOrCreateDefaultRule` behavior.
4. **Omit `escalationRule` entirely** (don't emit `[]`) when a rule has no attached escalations.
5. **Omit `slaRules` key entirely** on targets with no SLA T-entries.

## Recipe — one escalation entry

```json
{
  "id": "esc_xxxxxx",
  "displayName": "<from T-entry, optional>",
  "action": {
    "type": "notification",
    "recipients": [
      { "scope": "User" | "UserGroup", "target": "<UUID>", "value": "<display>" }
    ]
  },
  "triggerInfo": {
    "type": "at-risk" | "sla-breached",
    "atRiskPercentage": <1-99>
  }
}
```

- `displayName` omitted entirely when T-entry doesn't supply one (don't emit `undefined`).
- `atRiskPercentage` included only when `triggerInfo.type === "at-risk"`.
- `recipients` is an array — **one entry per sdd-declared recipient**. See Known CLI divergences.

## Unresolved recipients (skeleton-style)

When sdd gives an email but no UUID, emit the recipient with a sentinel `target`:

```json
{ "scope": "User", "target": "<UNRESOLVED: user-uuid for manager@corp.com>", "value": "manager@corp.com" }
```

List every unresolved recipient in the completion report (per SKILL.md § Completion Output step 4) so the user can patch externally. Do not call an identity service from the JSON path — that capability is out of scope for this milestone.

## Expression translation

`tasks.md` entries carry natural-language conditions. Translate at execution using the table in [`impl-cli.md § Expression Translation`](impl-cli.md#expression-translation). If ambiguous, AskUserQuestion with 2–3 candidates + "Something else" per SKILL.md rule #19.

## Post-write validation

- Confirm `schema.root.data.slaRules` or `node.data.slaRules` exists with the expected entries.
- Confirm the trailing entry's `expression === "=js:true"` when any SLA T-entry targeted this node.
- Confirm every generated `esc_` ID appears in `id-map.json`.
- Run `uip maestro case validate <file> --output json` after all SLA targets have been written (not per-target).

## Known CLI divergences

JSON is a superset of the CLI path. Each divergence is deliberate:

- **Per-conditional-rule escalations.** CLI's `escalation add` always attaches to the default `=js:true` rule. JSON attaches to any `slaRules[]` entry via the T-entry's `attach-to` field. Studio Web-authored caseplan.json files already use this pattern.
- **ExceptionStage SLA.** CLI's `requireStageForSla` rejects `case-management:ExceptionStage`. JSON writes SLA to both `Stage` and `ExceptionStage`. Runtime accepts both.
- **Multi-recipient single rule.** CLI emits one `EscalationRule` per recipient. JSON emits one rule with `recipients: [r1, r2, …]` when sdd declares multiple recipients on the same escalation. Matches sdd intent; the `EscalationRuleRecipient[]` type supports it.
- **Co-authorship is asymmetric.** CLI can append escalations to our default rule (`getOrCreateDefaultRule` finds the `=js:true` entry). CLI cannot edit per-conditional-rule escalations — those are JSON-only territory.

## Compatibility

- [ ] **CLI-parity:** structural equivalence between CLI output (`sla set` + `rules add` + `escalation add`) and direct-JSON-write, modulo random `esc_xxxxxx` IDs
- [ ] **Validation parity:** both outputs produce the same `uip maestro case validate` result
- [ ] **Gap-fill:** per-conditional-rule escalations, ExceptionStage `slaRules[]`, and multi-recipient single-rule variants each pass `uip maestro case validate`
- [ ] **Studio Web render:** per-conditional-rule escalations display correctly
- [ ] **Co-authorship forward:** CLI `sla escalation add` against JSON-written default rule appends successfully
