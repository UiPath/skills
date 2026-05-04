---
direct-json: supported
---

# sla — JSON Implementation

> **Phase split.** Phase 3 only. Phase 2 does not write SLA or escalation rules. See [`../../phased-execution.md`](../../phased-execution.md).

Cross-cutting direct-JSON rules live in [`case-editing-operations.md`](../../case-editing-operations.md).

## Purpose

Compose the `slaRules[]` array for each target (root or stage) in one write. Group all SLA T-entries by target and emit the full array in a single mutation.

## Input spec (from `tasks.md §4.8`)

| T-entry kind | Required fields | Notes |
|---|---|---|
| Default SLA | `target`, `count`, `unit` | One per target. Emitted as the `=js:true` entry, always last. |
| Conditional rule | `target: "root"`, `condition` (natural-language), `count`, `unit` | Root-only. Translated to `=js:<expr>` at execution; see Expression Translation below. |
| Escalation | `target`, `attach-to: T<m>` \| `default`, `trigger-type`, `at-risk-percentage?`, `recipients[]`, `display-name?` | `attach-to` points to the T-number of the parent rule (or the default). |

## ID generation

- Escalation: `esc_` + 6 chars. Per [`case-editing-operations.md § ID Generation`](../../case-editing-operations.md#id-generation).
- Conditional SlaRuleEntry: **no `id` field**. Removal is by array index.

Record every `T<n> → esc_xxxxxx` in `id-map.json` under `{kind: "escalation", ruleExpression: "<parent rule expression>", target: "root" | "<stageId>"}`.

## Target resolution

Read the `Schema:` header from `tasks.md` to pick the root-target path. Stage-target path is identical across schemas.

### v19

- `target: "root"` → `root.data.slaRules` (**inside `root.data`** — sibling of `intsvcActivityConfig` and `uipath`, NOT a top-level key and NOT a direct child of `root`)
- `target: "<stage-name>"` → locate node by `data.label === <stage-name>`; write to `node.data.slaRules` (inside the stage node's `data`)

### v20

- `target: "root"` → **`metadata.slaRules`** (top-level `metadata` block, NOT `root.data.slaRules` — there is no `root` in v20)
- `target: "<stage-name>"` → locate node by `data.label === <stage-name>`; write to `node.data.slaRules` (unchanged from v19 — node internals are identical)

### Common

- Accepted node types: `case-management:Stage` and `case-management:ExceptionStage`.
- If the stage node isn't found, halt and AskUserQuestion with candidate stage labels + "Something else".

## Recipe — one target

After grouping T-entries by target, compose the `slaRules` array and write it into the target's location per the table above. The composed array shape is **identical** across v19 and v20 — only the destination path differs.

### Composed array (both schemas)

```json
[
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

### v19 root-target shape

```json
{
  "root": {
    "id": "root",
    "name": "<name>",
    "type": "case-management:root",
    "...": "...",
    "data": {
      "intsvcActivityConfig": "v2",
      "uipath": { "...": "..." },
      "slaRules": [ <composed array above> ]
    }
  }
}
```

### v20 root-target shape

```json
{
  "id": "case-aBcDeFgHiJ",
  "version": "20.0.0",
  "metadata": {
    "caseIdentifier": "<...>",
    "caseUnifiedSchemaEnabled": true,
    "slaRules": [ <composed array above> ]
  },
  "...": "..."
}
```

For a stage target (both schemas), the same `slaRules` array is written under `node.data.slaRules` (sibling of `label`, `tasks`, `parentElement`).

> **Common failures:**
> - **v19:** emitting `slaRules` at the caseplan top level or directly on `root` (sibling of `data`). Both wrong — must nest inside `data`.
> - **v20:** emitting `slaRules` under a non-existent `root` key, or under `root.data.slaRules`. Both wrong — must nest under top-level `metadata`. There is no `root` key in v20.
> - **Either:** writing `slaRules` to a stage's top level (sibling of `id`/`type`). Stage SLA always lives under `node.data.slaRules` regardless of schema.

Emission rules:

1. **Conditional rules first, in T-entry order.** Priority = sdd order (top-most wins).
2. **Default rule (`=js:true`) last.** Always emitted when any SLA T-entry targets this node — even escalation-only cases.
3. **Bare default rule is legal.** If a target has escalations but no default SLA T-entry, emit `{expression:"=js:true", escalationRule:[…]}` with no `count` / `unit`.
4. **Always emit `escalationRule` on every rule.** Use `"escalationRule": []` when a rule has no attached escalations. Never omit the key.
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
- `recipients` is an array — **one entry per sdd-declared recipient**.

## Unresolved recipients (skeleton-style)

When sdd gives an email but no UUID, emit the recipient with a sentinel `target`:

```json
{ "scope": "User", "target": "<UNRESOLVED: user-uuid for manager@corp.com>", "value": "manager@corp.com" }
```

List every unresolved recipient in the completion report (per SKILL.md § Completion Output step 4) so the user can patch externally. Do not call an identity service from the JSON path — that capability is out of scope for this milestone.

## Expression translation

`tasks.md` entries carry natural-language conditions. Translate at execution using the expression prefixes in [SKILL.md Rule #14](../../../SKILL.md) and the helpers in [`bindings-and-expressions.md`](../../bindings-and-expressions.md). Common patterns: `=js:<javascript>` for arbitrary boolean, `=vars.<id> === "<literal>"` for variable comparison, `=metadata.<field>` for case metadata. If ambiguous, AskUserQuestion with 2–3 candidates + "Something else" per SKILL.md rule #19.

## Post-write validation

- **v19:** confirm `root.data.slaRules` or `node.data.slaRules` exists with the expected entries. Verify the key is nested under `data`.
- **v20:** confirm `metadata.slaRules` (top-level) or `node.data.slaRules` (stage) exists. Verify v20's root-target uses `metadata` — not `root.data` (which doesn't exist in v20).
- Confirm the trailing entry's `expression === "=js:true"` when any SLA T-entry targeted this node.
- Confirm every generated `esc_` ID appears in `id-map.json`.
- Run `uip maestro case validate <file> --output json` after all SLA targets have been written (not per-target). In v20 mode, validate may reject due to CLI lag — capture output to build-issues.md, do not retry-loop (Rule 17).

