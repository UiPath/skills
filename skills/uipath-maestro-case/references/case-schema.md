# Case Management JSON Schema — Cross-Cutting Reference

Structural reference for case-definition JSON. Shared fields are here; per-task and per-condition shapes are in each plugin's `impl-json.md`.

## Top-level shape

A case contains `id`, `version`, `name`, optional `description`, `metadata`, `bindings`, `variables`, `nodes`, `edges`, and `layout`:

```json
{"id":"case-aBcDeFgHiJ","version":"32.0.3","name":"<case name>","description":"<optional>","metadata":{"caseIdentifier":"<MORT>","caseIdentifierType":"constant","caseAppEnabled":false,"publishVersion":2,"caseUnifiedSchemaEnabled":true,"intsvcActivityConfig":"v2","slaRules":[],"caseExitRules":[]},"bindings":[],"variables":{"inputs":[],"outputs":[],"inputOutputs":[]},"nodes":[],"edges":[],"layout":{}}
```

### Layout-strip (Rule 19)

`transformCaseInMemoryJsonToDiskJson.ts` strips canvas layout. Emit clean nodes and `layout: {}`; FE auto-layouts on load and the skill is not a layout authority. Never emit node `position`, `style`, `measured`, `width`, `height`, or `zIndex`, or edge `data.waypoints`. The FE lifts these to `layout.nodes[<nodeId>] = { position, style, measured, width, height }` and `layout.edges[<edgeId>] = { waypoints }`; the skill never writes them (emit `layout: {}`).

**ID format (cross-cutting).** Use CLI `prefixedId(prefix, count)`: fixed prefix plus `count` random `[A-Za-z0-9]` characters. Direct JSON writes must match frontend `generateNextId(prefix, count)`:

| Entity | Prefix | Suffix |
|---|---|---:|
| Stage (primary + secondary) | `Stage_` | 6 |
| Trigger (added after initial) | `trigger_` | 6 |
| Task | `t` | 8 |
| Task entry condition | `c` | 8 |
| Task entry rule | `r` | 8 |
| Stage/case/task condition | `Condition_` | 6 |
| Rule inside those conditions | `Rule_` | 6 |
| Sticky note | `StickyNote_` | 6 |
| SLA rule entry | `sla` | 8 |
| SLA escalation | `esc_` | 6 |
| Binding | `b` | 8 |

## 1. Top-level + metadata

Top-level `id` is `case-` plus 10 random characters; `version` is literal `"32.0.3"`, emitted by the `case` plugin at T01; `name` is human-readable; `description` is optional. Metadata:

- `caseIdentifier`: runtime identifier; `constant` is a literal prefix, `external` is a `=` expression.
- `caseIdentifierType`: `"constant"` | `"external"`, default `constant`.
- `caseAppEnabled`: boolean.
- `publishVersion`: optional number, `2` for the current schema.
- `caseUnifiedSchemaEnabled`: optional boolean, `true`.
- `caseDirectlyPassTaskOutputs`: retired since PO.Frontend `15cd541e9` (2026-06-16); do not write it. Existing plans may retain it harmlessly; Case Designer drops it.
- `intsvcActivityConfig`: optional string payload.
- `slaRules`: optional `SlaRuleEntry[]`; each rule has a non-empty target-unique `displayName` without `:`; trailing `expression: "=js:true"` is the default and escalations are nested in `escalationRule[]`. See §6.
- `caseExitRules`: optional `CaseExitCondition[]`; a valid case has at least one root entry with `marksCaseComplete: true`, normally `required-stages-completed`; `false` entries are non-completing exits and cannot be the only exits.

### Case identifier (constant vs external)

`caseIdentifierType` selects runtime resolution. `constant` (default) uses a literal 2–4 character prefix such as `"LOAN"`; runtime emits `<prefix>-<generated>`. `external` requires a `=`-prefixed bare `=vars.<id>` or `=js:<expr>`; its result is the case external id verbatim, with no prefix. Use the convention in [bindings-and-expressions.md](bindings-and-expressions.md), with no other engine. The field is under `metadata`. Authoring and variable eligibility: [`plugins/case/planning.md` § External identifier value](plugins/case/planning.md).

### CaseExitCondition

Fields are `id`, `displayName`, `rules`, and `marksCaseComplete`; rules use DNF (§4). `marksCaseComplete` closes the case, not a stage.

## 2. nodes (three types, discriminated on `type`)

### a) Trigger Node — `"uipath.case.trigger"`

The triggers plugin writes exactly one initial trigger at T02; additional triggers use `trigger_` IDs. Its data is:

```json
{"typeVersion":"1.0.0","display":{"label":"Start"},"inputs":{"serviceType":"None","entryPointId":"<entry-points.json uniqueId>"}}
```

Do not put `position`, `style`, `measured`, `width`, `zIndex`, or `parentElement` on it. `data.typeVersion` is literally `"1.0.0"`; `display` may contain `label` and `icon`; `display.label` is the name (pre-v24 `data.label` moved here); optional `description` remains at `data.description`; `inputs` is the passthrough runtime bag and must always be written, including manual triggers. It contains `serviceType`, `entryPointId`, and, as applicable, per-kind `timerType`, `timeCycle`, `context[]`, `inputs[]`, `outputs[]`, and `bindings[]`. Older manual triggers may omit `inputs` when reading.

`data.inputs.entryPointId` must equal this trigger's `entry-points.json` `uniqueId`; the Case Designer pairs them. If absent, first open mints and rewrites one. `validate --strict` reports missing/mismatched values as `STRICT_TRIGGER_ENTRY_POINT_ID`. `uip maestro case init` scaffolds `trigger_1` with the value: preserve it when rewriting `trigger_1`; for a new trigger mint one `uniqueId` and write the same GUID to both files.

`serviceType` is one of `"None"`, `"Intsvc.EventTrigger"`, or `"timer"`. Kind-specific shape is in the trigger plugin's `impl-json.md`. For unresolved `Intsvc.EventTrigger`, retain `serviceType`, `entryPointId`, and one `context[]` entry with `objectName` (the SDD Source emitted by `sdd convert`); omit `metadata`, `inputs[]`, `outputs[]`, and `bindings[]`. See [`triggers/event/impl-json.md` § Placeholder fallback](plugins/triggers/event/impl-json.md).

### b) Stage Node — `"case-management:Stage"`

A primary or secondary workflow stage. Common `data` fields are `label`, optional `description`, optional `stageType`, optional `isRequired`, `parentElement`, `isInvalidDropTarget`, `isPendingParent`, `tasks`, optional `slaRules`, optional `entryConditions`, optional `exitConditions`, and optional `instanceIdPrefix` (prefix for instance IDs).

- `stageType` is `"primary"` | `"secondary"`; omit it for primary and put `"secondary"` first in secondary `data`.
- `label` is required, unique across all node labels, and must not contain `:`.
- `parentElement` is always `{ "id": "root", "type": "case-management:root" }`; `root` is canvas-side, not a disk node.
- `isInvalidDropTarget` and `isPendingParent` are always `false`.
- `tasks` is a 2D structural array preserving frontend order. A strict chain is consecutive singleton sets `[[A], [B], [C]]`, with `runs-sequentially` on each task. Parallel siblings share a set, at the start (`[[A, B], [C]]`) or after a predecessor (`[[A], [B, C], [D]]`), with `runs-sequentially` on B and C. Use `[]` when empty.
- When writing a primary stage, do not emit empty `entryConditions`/`exitConditions` arrays; condition plugins add them later. Secondary creation initializes both to `[]`.
- `slaRules` may be present on either stage type; see §6 and [`plugins/sla/impl-json.md`](plugins/sla/impl-json.md).

Do not emit node-level `position`, `style`, `measured`, `width`, `height`, or `zIndex`.

### c) Secondary (Exception) Stage — `case-management:Stage` with `data.stageType: "secondary"`

This is not a distinct node type; never emit `case-management:ExceptionStage` (removed at schema v22). Use the primary Stage shape, set `data.stageType: "secondary"` first, and initialize `entryConditions: []` and `exitConditions: []`. Secondary-stage SLA is accepted like primary-stage SLA.

### d) Sticky Note Node — `"case-management:StickyNote"`

A non-executable canvas annotation. Data fields are `parentElement` (always `{ "id": "root", "type": "case-management:root" }`), optional `color`, and optional `content`. `color`, when present, is one of `blue`, `green`, `yellow`, `pink`, `white`; omit it for the designer default. Never emit `position`, `style`, `width`, `height`, or `measured`; the designer places and sizes it.

## 3. Conditions (cross-cutting)

All conditions use the same DNF shape and attach at stage entry/exit, task entry, or case exit. Per-level fields and `--rule-type` semantics are in the relevant condition plugin's `impl-json.md`.

<a id="condition-name-uniqueness"></a>

### Condition name uniqueness

Every condition `displayName` shares one case-wide pool across stage `data.entryConditions[]`, stage `data.exitConditions[]`, task `entryConditions[]`, and `metadata.caseExitRules[]`. `validate` makes duplicates a hard error: `Rule name '<displayName>' is not unique`, reported once per owning node (`nodes[<stageId>]` or `nodes[root]`).

Exact, case-sensitive, trimmed frontend defaults are exempt and may repeat: `Entry rule <N>`, `Exit rule <N>`, `Completion rule <N>`, `Stage complete`, `Stage exit`, `Tasks completed rule`, and `Previous task completed`. This is only a commonly written subset of 472 locale templates; `validate` is authoritative. Preserve exact spelling: `Entry Rule 1` and `Complete rule 1` are near-misses, not defaults.

Leave an SDD `Display Name` unchanged when it exactly matches a default pattern such as `Entry rule 1`, `Completion rule 1`, or `Stage complete`. Normalize case-insensitive near-misses such as `Entry Rule 1`, `Complete Rule 1`, or `EXIT RULE 2` to exact exempt spelling. Nothing else is a default: authored names such as `Approved`, `Order Second Opinion`, and `Case complete rule` must be unique and must not be rewritten; repair their duplicates in the SDD.

Number authored names with a case-wide counter per label kind: highest authored number plus 1, never an array-local counter. Count authored names only; exempt defaults do not count. Never repair collisions by deleting a condition. Emptying task `entryConditions[]` only downgrades validation to warning `CASE_MGMT_STAGE_TASK_ENTRY_CONDITION_MISSING` and destroys behavior, including making an `adhoc` task unreachable or a gated task ungated.

### EntryCondition (stage-level)

Fields: optional `id`, optional globally unique `displayName`, `rules`, and optional `isInterrupting`.

### ExitCondition (stage-level)

Fields: optional `id`, optional globally unique `displayName`, `rules`, optional `type` (`"exit-only"` | `"wait-for-user"` | `"return-to-origin"`), optional `exitToStageId`, and optional `marksStageComplete`.

### TaskEntryCondition (task-level)

Fields: optional `id`, optional globally unique `displayName`, and `rules`.

### CaseExitCondition (case-level)

See `metadata.caseExitRules` in §1.

## 4. edges — retired, always `[]`

The skill never authors edges (Rule 21); keep `schema.edges` as `[]` for frontend compatibility. Stage transitions derive only from conditions; case start derives from the first stage's `case-entered` entry condition, not a `TriggerEdge`. FE derives canvas connectors. Treat round-tripped FE edges as read-only: never copy, adapt, or author them. Stray-edge removal: [case-editing-operations.md § Delete an edge](case-editing-operations.md#delete-an-edge--defensive-only). Read-only shapes: [Appendix — Edge shapes](#appendix--edge-shapes-read-only--never-author).

## 5. Rules (DNF — OR of AND-clauses)

Every condition's `rules` is `Rule[][]`: the outer array is OR groups; each inner array is AND conditions.

| `rule` | Fields / meaning |
|---|---|
| `wait-for-connector` | optional `id`, required `uipath`, optional `conditionExpression`; unresolved connectors require a stub placeholder, not bare form ([connector-trigger-impl.md § Placeholder fallback](connector-trigger-impl.md#placeholder-fallback)); rule shape in § Connector-bound rule |
| `case-entered` | optional `id`, optional `conditionExpression`; first case entry |
| `selected-stage-completed` | optional `id`, `selectedStageIds?`, `conditionExpression?`; selected stages completed |
| `selected-stage-exited` | optional `id`, `selectedStageIds?`, `conditionExpression?`; one or more specific stages have been exited |
| `selected-tasks-completed` | optional `id`, `selectedTasksIds?`, `conditionExpression?`; selected tasks completed |
| `required-tasks-completed` | optional `id`, optional `conditionExpression`; all required tasks in the stage completed |
| `required-stages-completed` | optional `id`, optional `conditionExpression`; all required stages completed |
| `current-stage-entered` | optional `id`, optional `conditionExpression`; current stage just entered |
| `user-selected-stage` | optional `id`, optional `conditionExpression`; user manually routes to this stage |
| `sla-status-change` | optional `id`, `slaId?`, `escalationId?`, `conditionExpression?`; breach uses `slaId` alone, at-risk uses `slaId` plus the at-risk escalation ID; valid in `enter-stage` and `start-task` scopes |
| `adhoc` | optional `id`, optional `conditionExpression`; ad-hoc expression |
| `runs-sequentially` | optional `id`, optional `conditionExpression`; tasks run declaration order top-to-bottom |

Allowed rule types vary by level; use each condition plugin's `impl-json.md`. Task manually-triggered/adhoc mode is an `adhoc`-only entry condition plus `isRequired: false`, not an event rule. External event mode requires an explicit event rule such as `wait-for-connector`.

Selected-stage rules always use array `selectedStageIds`, even for one stage, in all four scopes; singular `selectedStageId` is rejected with `selectedStageId is deprecated, it should be a stage in selectedStageIds instead`.

A `selected-stage-exited` reference requires the named stage to have an `exitConditions[]` entry with `marksStageComplete: false`. If all exits complete, validation reports `CASE_MGMT_ROOT_CASE_EXIT_CONDITION_RULE_SELECTED_STAGE_ID_NOT_FOUND` against the referencing rule; adding more completing exits does not satisfy it. `selected-stage-completed` reads exits that mark complete. Resolve a design asking for a non-completing exit with only completing exits in the SDD; do not invent one. `exit-only` plus `marksStageComplete: true` is legal but cannot satisfy `selected-stage-exited`.

An interrupting secondary-stage `sla-status-change` entry is global to its referenced SLA scope and can exit whichever covered stage is active; do not duplicate it as per-stage exits.

### Connector-bound `wait-for-connector` rule

Bind the IS connector under `uipath`, using the same block as an in-stage `wait-for-connector` task. A bare rule is rejected by Studio Web because the FE validator requires the connector activity. Author it from a `case spec --type trigger` scaffold; the CLI does not bind it (`buildRule` emits the bare form). `conditionExpression`, when present, is an optional `=js:` gate on case state (`vars.X` / `metadata`), never event payload and never an `event` namespace.

```json
{"rule":"wait-for-connector","id":"<ruleId>","uipath":{"serviceType":"Intsvc.WaitForEvent","context":[{"name":"connectorKey","value":"<key>","type":"string"},{"name":"connection","value":"=bindings.<id>","type":"string"},{"name":"resourceKey","value":"<connection-id>","type":"string"},{"name":"folderKey","value":"=bindings.<id>","type":"string"},{"name":"method","value":"<httpMethod>","type":"string"},{"name":"path","value":"<path>","type":"string"},{"name":"objectName","value":"<object>","type":"string"},{"name":"operation","value":"<eventOperation>","type":"string"},{"name":"metadata","type":"json","body":{}}],"inputs":[],"outputs":[],"bindings":[]},"conditionExpression":"=js:<optional case-state gate, e.g. vars.X — NOT the event payload>"}
```

Full `validate` requires `rule.uipath` and `context`; absence yields `connector activity missing`. `context` entries named `connectorKey` and `operation` satisfy the check; internals are not inspected, so a wrong `serviceType` passes. Confirm resolution in Studio Web. Splice the exact context emitted by `case spec`; its fields vary by connector. Full recipe: [connector-trigger-impl.md § Target: connector-bound condition rule](connector-trigger-impl.md#target-connector-bound-condition-rule).

## 6. SLA and Escalation

All root/stage SLA data is one `slaRules[]`; evaluate in array order and use the first truthy expression. Conditional overrides precede the trailing default entry with `expression: "=js:true"`; escalations nest in each rule's `escalationRule[]`. A rule may be escalation-only and omit `count`/`unit`; escalation rules may attach to any SLA, including secondary stages.

`SlaRuleEntry` fields: stable `sla_` `id` (required when a `sla-status-change` rule references this SLA), required target-unique `displayName` without `:`, required `expression`, optional `count`, optional `unit`, and optional `escalationRule[]`. Non-default expressions are non-empty. `unit` is `"min"` | `"h"` | `"d"` | `"w"` | `"m"`.

Each escalation requires `id`, target-unique non-empty `displayName` without `:`, `triggerInfo`, `action`, and at least one recipient. Default format is `Escalation rule <N> - <sla displayName>`. `triggerInfo.type` is `"at-risk"` or `"sla-breached"`; `atRiskPercentage` is required only for `"at-risk"`. `action.recipients[]` may contain multiple recipients; each `scope` is `"User"` or `"UserGroup"`, `target` is the user/group UUID, and `value` is the display email/group name. See [`plugins/sla/impl-json.md`](plugins/sla/impl-json.md).

## 7. Tasks — BaseTask shape (shared)

Every stage task has top-level `id`, `elementId`, optional `displayName`, `type`, `data`, optional `skipCondition`, optional `entryConditions`, optional `shouldRunOnlyOnce`, optional deprecated `shouldRunOnReEntry`, optional `isRequired`, and optional `description`.

- `id` is `t` plus 8 random characters; `elementId` is `${stageId}-${taskId}`.
- `displayName` is case-wide unique, must not contain `:`, and if omitted resolves to the bound resource name, which shares the same pool.
- `data` is type-specific; connector task `data.bindings` references root `bindings`.
- `skipCondition` is a `=js:` expression; skip when truthy and use strict equality ([`bindings-and-expressions.md`](bindings-and-expressions.md#equality-operators)).
- `entryConditions` are written by the task-entry-conditions plugin from SDD authored Entry Condition rows, uniformly for all task types; task type does not auto-inject them.
- `shouldRunOnlyOnce` limits execution to once per case even on stage re-entry. `shouldRunOnReEntry` is deprecated; use `shouldRunOnlyOnce`.
- `isRequired` controls whether completion is required for stage completion.

All envelope fields are siblings of `data`, never inside it. Misplaced fields pass `validate` silently but are dead configuration. Tasks have no `x`/`y`; use the stage `data.tasks` 2D array. Do not infer order from lane sharing. For a strict chain use consecutive singleton sets and `runs-sequentially` as the only entry rule on each task; after one predecessor, put independent siblings in the same next set and put `runs-sequentially` on each sibling.

Task types and plugins:

| Type | Plugin |
|---|---|
| `process` | `plugins/tasks/process/` |
| `action` | `plugins/tasks/action/` |
| `agent` | `plugins/tasks/agent/` |
| `rpa` | `plugins/tasks/rpa/` |
| `api-workflow` | `plugins/tasks/api-workflow/` |
| `function` | `plugins/tasks/function/` |
| `business-rule` | `plugins/tasks/business-rule/` |
| `case-management` | `plugins/tasks/case-management/` |
| `execute-connector-activity` | `plugins/tasks/connector-activity/` |
| `flow-process` | `plugins/tasks/flow-process/` |
| `http-request` | `plugins/tasks/http-request/` |
| `document-extraction` | `plugins/tasks/document-extraction/` |
| `wait-for-connector` | `plugins/tasks/connector-trigger/` |
| `external-agent` | `plugins/tasks/connector-activity/` (External agents and automations) |
| `external-workflow` | `plugins/tasks/connector-activity/` (External agents and automations) |
| `wait-for-timer` | `plugins/tasks/wait-for-timer/` |

## 8. Minimal example

A minimal plan has top-level `id`, `version: "32.0.3"`, `name`, metadata (`caseIdentifier`, `caseIdentifierType`, `caseAppEnabled`, `publishVersion`, `caseUnifiedSchemaEnabled`, `intsvcActivityConfig`), empty `bindings`, `variables` with `inputs`, `outputs`, `inputOutputs`, one `uipath.case.trigger` node with `data.typeVersion: "1.0.0"` and `data.display.label`, one primary `case-management:Stage` with `label`, `parentElement`, `isInvalidDropTarget: false`, `isPendingParent: false`, and `tasks: []`, and `edges: []`. The trigger's `data.inputs.entryPointId` must still match `entry-points.json` when applicable.

## Appendix — Edge shapes (read-only — never author)

> **Read-only reference (Rule 21 — edges retired).** Documented only so canvas-round-tripped files remain readable. Never copy these into a build or write an edge object into `caseplan.case`; see §4.

A trigger edge has type `"case-management:TriggerEdge"`, `id`, `source`, `target`, `sourceHandle`, `targetHandle`, and `data.label`; it connects Trigger → Stage and has no rules. A stage edge has type `"case-management:Edge"`, `id`, `source`, `target`, `sourceHandle`, `targetHandle`, and `data.label`; it connects Stage → Stage, while transition conditions remain on the source stage's `exitConditions`. Optional `zIndex` (number) may appear.

Handle format is `<nodeId>____source____<direction>` or `<nodeId>____target____<direction>` with exactly four underscores on each side of `source`/`target`; directions are `right`, `left`, `top`, `bottom`. Trigger source means `TriggerEdge`; Stage source means `Edge`. `edges` remains empty: the case starts through the first stage's `case-entered` entry condition, not a `TriggerEdge`.

<!-- END: case-schema.md -->