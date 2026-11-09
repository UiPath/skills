# sla — JSON Implementation

> **Phase split.** Phase 2 Step 11 writes SLA and escalation objects before conditions. Phase 3 does not revisit them except for whole-file `$xref` resolution. See [`../../phased-execution.md`](../../phased-execution.md).

Cross-cutting direct-JSON rules live in [`case-editing-operations.md`](../../case-editing-operations.md).

## Purpose

Compose and write one complete `slaRules[]` array per target (root or stage), grouping all SLA rows by target.

## Input spec (from the SDD's SLA tables)

- **Default SLA:** `target`, `count`, `unit`, `display-name`; one per target, emitted as the final `=js:true` entry.
- **Conditional rule:** `target: "root"` or `"<stage-name>"`, `condition` (natural-language), `count`, `unit`, `display-name`; translate to `=js:<expr>` at execution and prepend in SDD order.
- **Escalation:** `target`, `attach-to: T<m>` or `default`, `trigger-type`, optional `at-risk-percentage`, `recipients[]`, and `display-name`.

## ID generation

Default and conditional rules require `sla_` + 8 chars; escalations require `esc_` + 6 chars, per [`case-editing-operations.md § ID Generation`](../../case-editing-operations.md#id-generation). Mint IDs while composing Phase 2 objects, check existing caseplan/id-map IDs, record each immediately beside its object, and do not preallocate IDs without writing their objects. Use `{kind: "sla-rule", displayName: "<title>", target: "root" | "<stageId>"}` for SLA entries and `{kind: "escalation", displayName: "<title>", parentSlaTask: "T<m>", target: "root" | "<stageId>"}` for escalations.

## Target resolution

- `target: "root"` writes top-level **`metadata.slaRules`**; no `root` key exists on disk.
- `target: "<stage-name>"` finds `data.label === <stage-name>` and writes `node.data.slaRules`.
- Accept only `case-management:Stage`; a secondary/exception stage is the same node with `data.stageType === "secondary"`.
- If the stage is absent, halt and AskUserQuestion with candidate stage labels plus "Something else".

> **Stage conditional rules are direct JSON only.** `uip maestro case sla rules add` exposes a root-only CLI surface; do not use it for a stage target. Compose and write the stage's complete conditional + default array at `node.data.slaRules`.

## Recipe — one target

Group by target, resolve its location, compose one complete array, and write it there. Put conditional entries first in SDD element order (top-most wins) and the default `=js:true` entry last. Emit that default whenever any SLA element targets the node, including escalation-only targets; omit `slaRules` when the target has no SLA elements. Every rule has a unique required `id` (`sla_` + 8 chars), `displayName` as applicable, and its expression.

### Composed array

```json
[
  {
    "id": "sla_aB3kL9Qx",
    "displayName": "SLA Rule 1",
    "expression": "=js:<translated-condition-1>",
    "count": <n>, "unit": "<min|h|d|w|m>",
    "escalationRule": [ <escalations with attach-to == conditional-1-T-number> ]
  },
  { "...additional conditional rules in sdd order..." },
  {
    "id": "sla_Np4rT7Vz",
    "displayName": "SLA Rule 2",
    "expression": "=js:true",
    "count": <default.count>, "unit": "<default.unit>",
    "escalationRule": [ <escalations with attach-to == default> ]
  }
]
```

> **`unit` is the sdd.md token verbatim**: `min` (minutes), `h` (hours), `d` (days), `w` (weeks), `m` (**months**). Never map `m` onto `min`, and never rewrite a unit or clamp a count to clear the 15–1000 floor — that floor applies to `min` only.

### Root-target shape

```json
{
  "id": "case-aBcDeFgHiJ",
  "version": "32.0.3",
  "metadata": {
    "caseIdentifier": "<...>",
    "caseUnifiedSchemaEnabled": true,
    "intsvcActivityConfig": "v2",
    "slaRules": [ <composed array above> ]
  },
  "...": "..."
}
```

For a stage target, the same `slaRules` array is written under `node.data.slaRules` (sibling of `label`, `tasks`, `parentElement`).

> **Common failures:**
> - Emitting `slaRules` under a non-existent `root` key. Wrong — must nest under top-level `metadata`. There is no `root` key on disk.
> - Writing `slaRules` to a stage's top level (sibling of `id`/`type`). Stage SLA always lives under `node.data.slaRules`.

Emission rules:

1. **Conditional rules first, in element order.** Priority = sdd order (top-most wins).
2. **Default rule (`=js:true`) last.** Always emitted when any SLA element targets this node — even escalation-only cases.
3. **Escalation-only default rule is legal, but it still needs an ID and title.** If a target has escalations but no default SLA row, Step 11 directly emits `{id:"sla_...", displayName:"SLA Rule 1", expression:"=js:true", escalationRule:[…]}` with no `count` / `unit`, and records that synthetic ID.
4. **Always emit `escalationRule` on every rule.** Use `"escalationRule": []` when a rule has no attached escalations. Never omit the key.
5. **Omit `slaRules` key entirely** on targets with no SLA elements.
6. **Emit a unique `id` on every SlaRuleEntry.** `sla_` + 8 chars — **required** (schema v26). `displayName` is optional (`"Default"` for the trailing `=js:true` entry).

## Recipe — one escalation entry

```json
{
  "id": "esc_xxxxxx",
  "displayName": "<from element, or generated: Escalation rule <N> - <parent SLA displayName>>",
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

- `displayName` is **required** (schema v27). Use the SDD row's display name when supplied; otherwise generate `Escalation rule <N> - <parent SLA displayName>` (N = 1-based index within the parent rule's `escalationRule[]`).
- `atRiskPercentage` included only when `triggerInfo.type === "at-risk"`.
- `recipients` is an array — **one entry per sdd-declared recipient**.

## Unresolved recipients (placeholder-style)

Phase 1 runs the identity resolver (see [`planning.md` § Identity Resolution](planning.md#identity-resolution)) and normally writes a UUID into `registry-resolved.json`. When it still carries an `<UNRESOLVED: ...>` sentinel for a recipient (resolver failed, user declined, or sdd input was unresolvable), emit the recipient with a sentinel `target`:

```json
{ "scope": "User", "target": "<UNRESOLVED: user-uuid for manager@corp.com>", "value": "manager@corp.com" }
```

List every unresolved recipient in the completion report (per SKILL.md § Completion Output step 4) so the user can patch externally. Do not call an identity service from the JSON path — resolution is Phase 1's responsibility; Phase 2 just transcribes whatever the SDD carries.

## Expression translation

SDD SLA rows carry natural-language conditions. Translate at execution using the expression prefixes documented in [`bindings-and-expressions.md`](../../bindings-and-expressions.md). SLA rule `expression` is a boolean-condition sink — use `=js:<expr>` with no outer parentheses per [§ Canonical form per sink](../../bindings-and-expressions.md#canonical-form-per-sink).

> **A business field is a case variable, never `metadata`.** Write `=js:vars.<variableName> === "<literal>"` — the variable's `name`, never its formal-arg `id`, and never a bare identifier ([bindings-and-expressions.md § Canonical form per sink](../../bindings-and-expressions.md#canonical-form-per-sink)). This holds for every SDD-declared field, **including the ones the SDD's "Case Metadata" table lists for readability** — that table is a human-facing grouping, not a runtime namespace. `Priority` is authored as a case variable and referenced `=js:vars.priority === 'Urgent'`.
>
> **Never write `=js:metadata.<businessField>`.** The `metadata` namespace is a closed set of structural fields (see [case-schema.md § 1](../../case-schema.md#1-top-level--metadata)); anything else reads `undefined` at run time. `=js:metadata.priority` resolves to nothing, `validate` returns `Valid` on either spelling, and the rule silently never fires.

Remaining patterns:

- `=js:true` — the default rule.
- `=js:(vars.X === 'foo') && (vars.Y > 5)` — combined boolean; parenthesize each sub-clause for operator precedence.

If ambiguous, AskUserQuestion with 2–3 candidates + "Something else" per SKILL.md Rule 2.

## The clock is not the response

This file writes the SLA **clock** and its escalation notifications. The **response** to an at-risk / breach event is a separate decision, read off the requirement and never off the SLA's scope:

- **notify-only** — an escalation entry here, and nothing else. Absent a stated response, both at-risk and breached are notify-only. Do NOT mint a stage, task, or condition for a requirement that only asks to notify someone.
- **start-task / enter-stage** — the escalation (if any) still lives here; the behavior change is an `sla-status-change` rule on the follow-up **task** (`start-task`) or on the destination **stage** (`enter-stage`). Shapes, interrupting semantics, and the four defects `validate` cannot see: [sla-response-shapes.md](../../sla-response-shapes.md).
- **exit-stage / exit-case** — a stage-exit or `metadata.caseExitRules[]` row.

A breach rule references the SLA alone (`slaId`, no `escalationId`), so a breach response does **not** require an escalation to exist here. An at-risk response does: it needs a concrete at-risk escalation on that same SLA.

## Post-write validation

- Confirm `metadata.slaRules` (root) or `node.data.slaRules` (stage) exists with the expected entries. Verify the root-target uses `metadata` — not `root.data` (which doesn't exist on disk).
- Confirm the trailing entry's `expression === "=js:true"` when any SLA element targeted this node.
- Confirm every emitted `sla_` and `esc_` ID appears in `id-map.json`. Step 10 must resolve every `sla-status-change` rule against IDs already emitted on the declared target.
- Run the section-boundary validation after all SLA targets have been written (not per-target); the Phase 2 preview profile runs later after conditions.

<!-- END: impl-json.md -->