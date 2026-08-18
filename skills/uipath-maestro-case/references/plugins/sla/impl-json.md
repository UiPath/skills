---
direct-json: supported
---

# sla — JSON Implementation

> **Phase split.** Phase 2 Step 11 writes SLA and escalation objects before conditions. Phase 3 does not revisit them except for whole-file `$xref` resolution. See [`../../phased-execution.md`](../../phased-execution.md).

Cross-cutting direct-JSON rules live in [`case-editing-operations.md`](../../case-editing-operations.md).

## Purpose

Compose the `slaRules[]` array for each target (root or stage) in one write. Group normalized SDD SLA rows by target and emit the full array in a single mutation.

## Input spec (from normalized SDD SLA rows)

| SDD row kind | Required fields | Notes |
|---|---|---|
| Default SLA | `target`, `count`, `unit`, `display-name` | One per target. Emitted as the `=js:true` entry, always last. |
| Conditional rule | `target: "root"` \| `"<stage-name>"`, `condition` (natural-language), `count`, `unit`, `display-name` | Translated to `=js:<expr>` at execution and prepended to the target's default; see Expression Translation below. |
| Escalation | `target`, `attach-to: "<exact parent SLA title>"` \| `default`, `trigger-type`, `at-risk-percentage?`, `recipients[]`, `display-name` | `attach-to` names the parent rule semantically (or the default). |

## ID generation

- SLA rule (default and conditional): `sla_` + 8 chars. **Required** on every entry.
- Escalation: `esc_` + 6 chars. Per [`case-editing-operations.md § ID Generation`](../../case-editing-operations.md#id-generation).

Mint these IDs while composing the objects, check them against existing caseplan/id-map IDs, and record semantic keys immediately: `sla:<target>/<title>` and `escalation:<target>/<sla title>/<title>`. Write the object and map entry in the same section. There is no preallocation-only pass.

## Target resolution

- `target: "root"` → **`metadata.slaRules`** (top-level `metadata` block — there is no `root` key on disk)
- `target: "<stage-name>"` → locate node by `data.label === <stage-name>`; write to `node.data.slaRules`
- Accepted node types: `case-management:Stage` (a secondary/exception stage is the same node with `data.stageType === "secondary"`).
- If the stage node isn't found, halt and AskUserQuestion with candidate stage labels + "Something else".

> **Stage conditional rules are direct JSON only.** `uip maestro case sla rules add` exposes a root-only CLI surface; do not use it for a stage target. Compose the stage's complete conditional + default array here and write `node.data.slaRules`.

## Recipe — one target

After grouping SDD rows by target, compose the `slaRules` array and write it into the target's location per the rules above.

### Composed array

```json
[
  {
    "id": "sla_aB3kL9Qx",
    "displayName": "SLA Rule 1",
    "expression": "=js:<translated-condition-1>",
    "count": <n>, "unit": "<min|h|d|w|m>",
    "escalationRule": [ <escalations whose attach-to equals this SLA title> ]
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

### Root-target shape

```json
{
  "id": "case-aBcDeFgHiJ",
  "version": "27.0.0",
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

1. **Conditional rules first, in SDD order.** Priority = top-most wins.
2. **Default rule (`=js:true`) last.** Always emitted when any SLA row targets this node — even escalation-only cases.
3. **Escalation-only default rule is legal, but it still needs an ID and title.** If a target has escalations but no default SLA row, emit `{id:"sla_...", displayName:"SLA Rule 1", expression:"=js:true", escalationRule:[…]}` with no `count` / `unit`, and record that semantic ID.
4. **Always emit `escalationRule` on every rule.** Use `"escalationRule": []` when a rule has no attached escalations. Never omit the key.
5. **Omit `slaRules` key entirely** on targets with no SDD SLA rows.
6. **Emit a unique `id` on every SlaRuleEntry.** `sla_` + 8 chars — **required** (schema v26). `displayName` is optional (`"Default"` for the trailing `=js:true` entry).

## Recipe — one escalation entry

```json
{
  "id": "esc_xxxxxx",
  "displayName": "<from SDD, or generated: Escalation rule <N> - <parent SLA displayName>>",
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

- `displayName` is **required** (schema v27). Use the SDD value when supplied; otherwise generate `Escalation rule <N> - <parent SLA displayName>` (N = 1-based index within the parent rule's `escalationRule[]`).
- `atRiskPercentage` included only when `triggerInfo.type === "at-risk"`.
- `recipients` is an array — **one entry per sdd-declared recipient**.

## Unresolved recipients (placeholder-style)

Phase 2 resolution normally writes a UUID into `case-build/registry-resolved.json`. When the evidence carries an `<UNRESOLVED: ...>` recipient (resolver failed, user declined, or SDD input was unresolvable), emit the recipient with a sentinel `target`:

```json
{ "scope": "User", "target": "<UNRESOLVED: user-uuid for manager@corp.com>", "value": "manager@corp.com" }
```

List every unresolved recipient in the completion report so the user can patch externally. Do not call an identity service from the JSON lowering path; transcribe the reviewed resolution evidence.

## Expression translation

The SDD carries natural-language conditions. Translate during lowering using [`bindings-and-expressions.md`](../../bindings-and-expressions.md). SLA `expression` is a boolean sink: use bare `=js:<expr>`. Use `vars` for business data and reserve `metadata` for the closed structural set in [case-schema.md](../../case-schema.md). Ambiguity is an SDD mismatch; do not guess.

## The clock is not the response

This file writes the SLA **clock** and its escalation notifications. The **response** to an at-risk / breach event is a separate decision, read off the requirement and never off the SLA's scope:

- **notify-only** — an escalation entry here, and nothing else. Absent a stated response, both at-risk and breached are notify-only. Do NOT mint a stage, task, or condition for a requirement that only asks to notify someone.
- **start-task / enter-stage** — the escalation (if any) still lives here; the behavior change is an `sla-status-change` rule on the follow-up **task** (`start-task`) or on the destination **stage** (`enter-stage`). Shapes, interrupting semantics, and the four defects `validate` cannot see: [sla-response-shapes.md](../../sla-response-shapes.md).
- **exit-stage / exit-case** — a stage-exit or `metadata.caseExitRules[]` row.

A breach rule references the SLA alone (`slaId`, no `escalationId`), so a breach response does **not** require an escalation to exist here. An at-risk response does: it needs a concrete at-risk escalation on that same SLA.

## Post-write validation

- Confirm `metadata.slaRules` (root) or `node.data.slaRules` (stage) exists with the expected entries. Verify the root-target uses `metadata` — not `root.data` (which doesn't exist on disk).
- Confirm the trailing entry's `expression === "=js:true"` when any SDD SLA row targeted this node.
- Confirm every emitted `sla_` and `esc_` ID appears in `id-map.json`. Step 10 must resolve every `sla-status-change` rule against IDs already emitted on the declared target.
- Run the section-boundary validation after all SLA targets have been written (not per-target); the Phase 2 preview profile runs later after conditions.

<!-- END: impl-json.md -->
