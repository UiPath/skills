# Variables — Implementation

No CLI command exists for variable declaration. Edit `caseplan.case` directly (Read → reason → Write/Edit).

## § Terminology + Resolution Semantics (read this first)

`VariablesService.findVariableByVariableId` resolves by direct, case-sensitive `Variable.id` equality:

```ts
const variableId = strip("=vars.", lookupExpression);
return allVariables.find(v => v.id === variableId);
```

| Field | Meaning | Resolver use |
|---|---|---|
| `id` | Sole resolver key | YES |
| `name` | Human-readable/FE label | No |
| `var` | Wire pointer: Out target, trigger output, or reassigned task output; mirrors `id` on bare declarations and trigger auto-emits | Only if `id` absent; FE fallback synthesizes `Variable.id = "=vars.<var>"` (partial, non-resolvable) |
| `elementId` | FE picker scope; `validate` requires non-empty | Not runtime-resolved |
| `source` | Runtime extraction expression | No — read by BPMN engine at runtime |
| `target` | Runtime write expression | No |
| `value` | Bound input or output mirror of `var` | No |
| `default` | Design-time / runtime fallback when slot is unwritten | Returned at design time when non-empty |
| `body` | JSON schema for `type: "jsonSchema"` | No |

`=vars.X` resolves in `variables.inputOutputs[]` when `id` exists; top-level `variables.inputs[]` by random `id` (picker-invisible, target through companion); top-level `variables.outputs[]` as formal entries (`var` points elsewhere); `task.data.outputs[]` when `id` exists; `task.data.inputs[]` by random `id`; and `triggerNode.data.inputs.outputs[]` when `id` exists, but not when only `var` exists. Trigger Pattern A (`id === var`) self-resolves; Pattern C (`var` only) requires a root companion.

A **companion** is the `inputOutputs[]` entry whose `id` equals the lookup name. It is required for trigger outputs lacking `id`, load-bearing for Out-args with a `Default`, and optional when a task output self-declares.

### Validator contract — `validate` is stricter than the resolver

| Check | Match | Reported at |
|---|---|---|
| `CASE_MGMT_REFERENCE_UNBOUND` | `id` or `name` or `var` | Referencing expression path |
| `VARIABLE_DOES_NOT_EXIST` | `id` plus non-empty `elementId` | `nodes[<stageId>]` |

`VARIABLE_DOES_NOT_EXIST` fails the default profile and `--strict` identically; `--strict` adds nothing. Skeleton profiles alone may miss it. Matching `id` still fails with missing or `""` `elementId`; only truthiness is tested, so `"root"`, a stage id, or trigger id passes. Write `elementId` on every `inputOutputs[]`; use `"root"` for case state. `--skeleton-v2` misses the defect when only consumers are task-scoped (`task` entry conditions or `skipCondition`); green output is not evidence of correct declarations. `validate` emits at most one `VARIABLE_DOES_NOT_EXIST` per node, so audit all declarations.

## Scope of this plugin

Under refactor B this plugin owns only top-level `variables.inputs[]`, `variables.outputs[]`, `variables.inputOutputs[]`, and `triggerNode.data.inputs.outputs[]`. Task plugins own `task.data.outputs[]`; io-binding owns `task.data.inputs[].value`; connector/trigger plugins own top-level `bindings[]`.

## Target Paths

| What | Path |
|---|---|
| In formal inputs | `variables.inputs[]` |
| Out formal outputs | `variables.outputs[]` |
| Internal variables | `variables.inputOutputs[]` |
| Trigger mappings | `nodes[<triggerIndex>].data.inputs.outputs[]` |

## Uniqueness Rule

Every independently minted `var`/`id` is globally unique across the case, except the single root-companion alias for equal-name `->` extraction. On collision append a counter from 2 (`decision`, `decision2`, `decision3`; `error`, `error2`, `error3`). Preserve original `source` and `name`; suffix allocated `var`/`id` and `target`; on reassignment suffix `originalVar` with allocated `id`.

A normal `field -> caseVar` output independently mints its source-side `id` although `var` points to the existing Case variable. Deduplicate that `id` globally, set `target` and `originalVar` to it, and never suffix pointer `var`. See [io-binding § Output Binding Shapes](../io-binding/impl-json.md#output-binding-shapes).

Equal-name reassignment (`baseId == target case-variable id`) is a wire, not an independent declaration. Exclude exactly the matching root companion (`id == target`, `elementId == "root"`) from source allocation; exclude nothing else. First `greeting -> greeting` may use `id == var == originalVar == "greeting"`; with another owner use `id`, `originalVar`, `target` = `greeting2`, while `var` and `value` remain `greeting`. Never suffix root companion or pointer `var`. `originalVar` marks both forms as reassigned so `mutateRootVariables` retains the companion.

### Pool composition

Scan every `var`/`id` in `caseplan.case`: root `variables.{inputs,outputs,inputOutputs}[]`; every task `nodes[<stage>].data.tasks[<lane>][].data.outputs[]`; every trigger `nodes[<trigger>].data.inputs.outputs[]`; stage entry/exit `nodes[<stage>].data.entryConditions[].rules[][].uipath.outputs[]` and `nodes[<stage>].data.exitConditions[].rules[][].uipath.outputs[]`; case-exit `metadata.caseExitRules[].rules[][].uipath.outputs[]`; and task-entry `nodes[<stage>].data.tasks[<lane>][].entryConditions[].rules[][].uipath.outputs[]`.

Rule outputs use `elementId = <stageId>-<ruleId>`; case-exit outputs use `elementId = root-<ruleId>`. Dedupe every producer against tasks, triggers, rules, and root in both directions. Shared `FPSFormServiceTypeFields` registers all through `getAllVariables()`; duplicates collapse in `allInputOutputsByElementMap`, causing round-trip cross-wiring. Skip rules without `uipath.outputs[]` (unresolved connector configuration; see [`connector-trigger-impl.md § Placeholder fallback`](../../../connector-trigger-impl.md#placeholder-fallback)); use the same skip as placeholder tasks (`data:{}`).

## Formal-arg slot ID format

In/Out formal `variables.inputs[].id` and `variables.outputs[].id` MUST be `v` + 8 chars from `[A-Za-z0-9]` (for example `vK3mNp9Qx`), as in task-input slots ([io-binding](../io-binding/impl-json.md)); never use a bare random id. BPMN exposes the id as `<uipath:input id="...">` and `=vars.<id>`; digit-leading ids break the BPMN parser (`illegal ID <5AinMKBDm>`), C# identifiers, and XML NCName rules.

The formal slot has readable `name` and `var`; its synthetic `id` differs. The companion uses the readable name as `id`:

```json
{ "name": "literalResult", "var": "literalResult", "id": "vK3mNp9Qx", "type": "string" }
{ "id": "literalResult", "name": "literalResult", "type": "string", "default": "" }
```

When re-minting a `sdd convert` formal entry, set `var` to the name in the same edit replacing `id`; synthetic `id` plus null `var` loses the binding name. Never copy the companion name into formal `id`.

## Inputs the plugin reads at Phase 3 Step 6.2

1. `sdd.md` Case Variables rows: category, type, default, sourceTrigger(s), sourceField(s). `Category=In` has one `sourceTriggers` T-number; blank means primary trigger.
2. `tasks/trigger-spec-cache.json`: each trigger’s un-minted `caseShape.outputs[]`, keyed by T-number; values contain `context`, `inputs`, `outputs`, with no synthesized `var`/`id`/`elementId`. Written at Step 6.1; see [`../../triggers/event/impl-json.md` § Step 8](../../triggers/event/impl-json.md) for writer schema.
3. `id-map.json`: `T<N> → trigger_xxxxxx` for trigger outputs and In binding; blank In source trigger uses `id-map["T02"].id`.
4. `caseplan.case`: trigger nodes and existing root arrays.

## Dispatcher — two loops

Both loops run at Phase 3 Step 6.2 and write the same root arrays.

### Loop A — Trigger spec output dispatch

For each cached trigger, look up `id-map.json[T<N>].id`, find its node, and process each `caseShape.outputs[]`:

- **Unreferenced:** write trigger output `{name: <spec.name>, var: <spec.name>, type: <spec.type>, source: <spec.source>, value: <spec.name>}` without `id`/`elementId`; write companion `{id: <spec.name>, name: <spec.name>, type: <spec.type>, elementId: <triggerId>, body: <spec.body>}`. `jsonSchema` companions retain full body for FE sub-field picking.
- **`Category=Variable` reference:** match by the row's `sourceField` path (sub-fields such as `response.Title` included); write Pattern C `{name: <last segment of sourceField>, var: <sdd-name>, type: <sdd-row.type>, source: "=<raw sourceField>", value: <sdd-name>}` without `id`/`elementId`, plus `{id: <sdd-name>, name: <sdd-name>, type: <sdd-row.type>, elementId: "root", custom: true}`. SDD type wins.
- **`Category=In`:** skip; Loop B handles it by category regardless of name or trigger.
- **`Category=Out`:** reject direction mismatch; Out flows case→caller.

Matching is top-level, byte-for-byte, and case-sensitive (`response` differs from `Response`); never re-case or alias. A matching SDD name replaces only that exact top-level auto-emit. A sub-field (`response.Title`) adds Pattern C and does not replace top-level `response`; auto-emit remains. Multiple rows may write separate trigger entries but share one companion, first-write-wins on type/default; Phase 2 rejects conflicts.

Worked example for SDD `calendarTitle ← response.Title` (Variable, type=string) on a trigger whose spec returns two top-level `jsonSchema` outputs `response` and `Error`:

```jsonc
triggerNode.outputs[]: [
  { name: "Title",    var: "calendarTitle", type: "string",     source: "=response.Title", value: "calendarTitle" },  // Pattern C — SDD; name = spec sub-field segment
  { name: "response", var: "response",      type: "jsonSchema", source: "=response",       value: "response" },        // auto-emit — coexists
  { name: "Error",    var: "Error",         type: "jsonSchema", source: "=Error",          value: "Error" }            // auto-emit — unreferenced
]
// No `id`, no `elementId` on trigger output entries — FE auto-emit convention.

root.inputOutputs[]: [
  { id: "calendarTitle", name: "calendarTitle", type: "string",     elementId: "root", custom: true },                    // Pattern C companion → Case Variables panel
  { id: "response",      name: "response",      type: "jsonSchema", elementId: "<triggerId>", body: <full schema from spec> },  // auto-emit companion (REQUIRED — body drives sub-field picker)
  { id: "Error",         name: "Error",         type: "jsonSchema", elementId: "<triggerId>", body: <error schema from spec> }
]
```

Six entries total: 3 trigger outputs (no id) + 3 companions (with id — resolution surface). The auto-emit companions carry the full body schemas so the FE picker can navigate sub-fields. The Pattern C companion has no body (its type is the primitive `string`).

For spec type `"file"` or `"octet-stream"` (normalize to `"file"`), add `target: "=orchestrator.JobAttachments"` to trigger output and `body: <FILE_TYPE_JSON_SCHEMA>` to root companion; body is required for FE sub-fields and JobAttachment widget.

### Loop B — non-extraction rows

Process every `Category=In` (any trigger, including sourceTriggers), `Category=Out`, and `Category=Variable` without `sourceTrigger`/`sourceTriggers`. `Category=In` never enters Loop A.

| Row | Root inputs | Root outputs | Root inputOutputs |
|---|---|---|---|
| Variable, no trigger | — | — | `{id: <name>, name: <name>, type: <type>, elementId: "root", default: <value if Default set>, custom: true}` |
| In | `{id: v<random8>, name: <name>, type: <type>, default: <value>, elementId: <triggerId>}` | — | `{id: <name>, name: <name>, type: <type>, elementId: <triggerId>}`; no `custom`; also bridge below |
| Out | — | `{id: v<random8>, name: <name>, type: <type>, var: <name>}` | `{id: <name>, name: <name>, type: <type>, default: <value or "">, elementId: "root"}`; no `custom` |
| InOut | unsupported in v1 | unsupported in v1 | unsupported in v1 |

For In, `<triggerId>` is `id-map.json[T<N>].id`, or primary `id-map["T02"].id` when blank. Formal, companion, and bridge use that trigger. If Loop A created the same Variable companion, dedupe by `id`; do not rewrite. In rows never straddle loops.

## Pattern shapes by category

### Pure state Variable (no trigger source)

`Category=Variable` with no `sourceTriggers` emits only a root companion with `custom: true`, `elementId: "root"`, and optional default. A `jsonSchema` entry also requires `body` and `_jsonSchema` (see [`## jsonSchema type`](#jsonschema-type)).

### Trigger-sourced Variable (Pattern C)

For a triggered `Category=Variable`, emit on each referenced trigger:

```json
{ "name": "<last sourceField segment>", "var": "<sdd-name>", "source": "=<sourceField>", "type": "<sdd-type>", "value": "<sdd-name>" }
```

Do not add `id` or `elementId`. Emit one root companion `{id: <sdd-name>, name: <sdd-name>, type: <type>, elementId: "root", custom: true}`. Multi-trigger rows emit one trigger entry per trigger and one shared companion; last writer wins at runtime and only one trigger fires per lifecycle.

### In argument

`Category=In` has empty `sourceFields`, may bind one manual, timer, or event trigger, and always emits:

```json
// root.inputs[]
{ "id": "v<random8>", "name": "applicantName", "type": "string", "default": "", "elementId": "<triggerId>" }
// root.inputOutputs[]
{ "id": "applicantName", "name": "applicantName", "type": "string", "elementId": "<triggerId>" }
// triggerNode.data.inputs.outputs[]
{ "name": "applicantName", "type": "string", "source": "=vars.v<random8>", "var": "applicantName" }
```

The bridge has `source`, never `value`, and no `id`/`elementId`; source is the formal slot id, not argument name. It copies caller/event value into the readable companion. A manual trigger is `data.inputs.serviceType: "None"`; older plans may omit `inputs`, but never assume absence. Preserve existing `"None"`; append to existing `data.inputs.outputs`, creating that array on existing `data.inputs` if missing. For a bound placeholder trigger, emit formal plus companion only and skip bridge; formal default will not reach companion by design. Re-generate from scratch (Rule 7) after resolution.

For `type === "file"`, formal and companion each carry `body: <FILE_TYPE_JSON_SCHEMA>`; bridge is unchanged, has no `target`, and formal `default` MUST be `""` (`InputOutputArgumentsDialog.tsx:148`).

### Out argument

Always emit the companion, regardless of Default. Formal output points through `var`:

```json
{ "id": "v<random8>", "name": "finalDecision", "type": "string", "var": "finalDecision" }
{ "id": "finalDecision", "name": "finalDecision", "type": "string", "default": "<value or empty string>", "elementId": "root" }
```

A producer overwrites the companion; if it does not fire, its default is returned. Empty default plus no producer is a pure orphan: the end-of-Phase-3 producer validator asks the user to (a) add producer, (b) add Default, (c) recategorize, or (d) continue best-effort; see [`io-binding/impl-json.md` § Check 2](../io-binding/impl-json.md).

### InOut argument

**NOT supported in v1.** The enum is `In | Out | Variable`; validators reject `Category=InOut` in Phase 2. If revived, trigger resolution is `id-map[<sourceTriggers T-number>].id`, blank → `id-map["T02"].id`, and FE shape is formal In `v<random8-in>`, shared companion, formal Out `v<random8-out>` with `var` pointing to companion, plus the In bridge.

## `default` encoding — EVERY type, MANDATORY

`default` is always a JSON string, never object, array, number, or boolean: JSON schemas use string-encoded JSON such as `"{\"amount\":125.5}"`; integers `"5"`; booleans `"true"`; dates `"2029-10-12"`; files/no default `""`.

Non-primitive defaults are silently deleted by the caseplan→BPMN converter’s [`bpmn-moddle.ts` `onlyPrimitiveVariableFields`](https://github.com/UiPath/PO.Frontend/blob/develop/src/services/serialization/bpmn-moddle.ts#L323-L331):

```ts
if (value === null || typeof value !== "object") { result[key] = value; }
```

The variable becomes null while string-defaulted neighbors retain `default=""`; a first task read can fail as `AGENT_STARTUP.INPUT_VALIDATION_ERROR / <input> Field required`. `uip maestro case validate` remains `Valid`, FE Zod uses `z.any()`, and serializer alone drops it. Step 12 Check 14 is the enforcement backstop.

## Phase 3 Spec-dependent Validation

Run these during dispatcher loop; log all at [`../../logging/impl-json.md`](../../logging/impl-json.md):

| Condition | Severity/action |
|---|---|
| `sourceField` top-level or nested path missing in referenced `caseShape.outputs[]` | ERROR: halt; AskUserQuestion with available keys (e.g. `Title`, `Description`, `Location`, …), update SDD; never preserve a runtime-fallback note such as `"if extraction fails, switch source to =response.Title"` |
| Existing sourceField type differs from SDD Type | WARNING: proceed and log to `build-issues.md` |
| Multi-trigger `sourceFields` T-number absent from `sourceTriggers`, or vice versa | ERROR: reject |

Do not repeat Phase 2 checks: missing/empty Category; Out with sourceTriggers; In with >1 CSV T-number; In with sourceFields; Same-Name pair mismatch; missing In/Out Type; nonexistent source trigger. Phase 3 checks source path, spec type, and multi-trigger cache correspondence; Out producer presence is Phase 3 io-binding validation at phase end. `Category=In` on event triggers is allowed; its three-entry emission is identical to manual/timer, with default propagating through the bridge at fire time. The bound trigger is `sourceTriggers` or primary.

## Custom Outputs (`custom: true` on task.data.outputs[])

Task plugins own custom outputs; this plugin only ensures a referenced variable exists in root `inputOutputs[]`. Custom outputs write constants, not task responses:

| Field | Standard | Custom |
|---|---|---|
| `source` | `"=<runtime-path>"` (SDD left side verbatim) | omitted |
| `value` | mirrors var | `"=<literal>"` or `"=js:<expr>"` |
| `custom` | omitted/`false` | `true` |
| `target` | `"=<varId>"` | omitted |

For SDD `=` rows (set/compute/copy; see [`../io-binding/planning.md`](../io-binding/planning.md)), task plugins emit `custom: true`, `var: <caseVar.id>`, `value: <expression>`, `source: <same as value>`, `elementId: "root"`; no root mirror is created because FE `isUpdateExistingOutput` filters it (`VariableMutationUtils.ts:49-64`). `->` performs extraction/renaming; `=` performs literal/computed/variable-reference writes.

## jsonSchema type

A `jsonSchema` variable MUST carry `body` and `_jsonSchema`, identical schema objects from the SDD Description (`Body schema: {"type": "object"}`). `body: null` prevents FE sub-field selection and is still `Valid`; `sdd convert` emits this incomplete form and omits it from `Data.Unresolved[]`, so fill both after conversion. This is the named exception to SKILL.md Rule 4’s settled-shape clause. `default` remains a string; body fields are objects and survive through CDATA.

```json
{ "id": "caseData", "name": "caseData", "type": "jsonSchema", "default": "{\"status\":\"Open\"}", "body": { "type": "object", "properties": { "status": { "type": "string" } } }, "_jsonSchema": { "type": "object", "properties": { "status": { "type": "string" } } } }
```

Empty default is `""` or `"{}"`, never object `{}` (Step 12 Check 14).

## file type

File Variables hold a JobAttachment record `{ID, FullName, MimeType, Metadata}`, not bytes/path; producing task writes the record. Normalize `"octet-stream"` to `"file"`. `body` MUST equal FILE_TYPE_JSON_SCHEMA byte-for-byte, including `$schema`, `description`, `additionalProperties`, and `"x-uipath-resource-kind": "JobAttachment"`, matching FE `VariableConstants.ts:10-36`; missing fields cause FE round-trip drift. Root Variable additionally uses `default: ""`, `custom: true`, `elementId: "root"`; In companions retain trigger `elementId` and no default/custom.

```json
{ "id": "evidenceDoc", "name": "evidenceDoc", "type": "file", "body": { "$schema": "http://json-schema.org/draft-07/schema#", "type": "object", "properties": { "ID": { "type": "string", "description": "Orchestrator attachment key" }, "FullName": { "type": "string", "description": "File name" }, "MimeType": { "type": "string", "description": "The MIME type of the content, such as application/json or image/png" }, "Metadata": { "type": "object", "description": "Dictionary<string, string> of metadata", "additionalProperties": { "type": "string" } } }, "required": ["ID"], "x-uipath-resource-kind": "JobAttachment" }, "default": "", "custom": true, "elementId": "root" }
```

## date / datetime types

Primitive; no body or target. FE uses DatePicker/DateTimePicker. Root Variables use `custom: true`, `elementId: "root"`, and string defaults, e.g. `type: "date"`, `default: ""`; datetime may use `default: "=js:new Date().toISOString()"`.

## Expression Syntax

See [`../../../bindings-and-expressions.md`](../../../bindings-and-expressions.md). Plain reads are `=vars.x`; comparisons are `=js:vars.x === 'val'`; never use `$vars.x`.

## Task Output → variable resolution

Task outputs with `id` (always `->`) self-declare. Reassign shape includes `originalVar`, making FE `mutateRootVariables` filter the output (`VariableMutationUtils.ts:135`) and preserve root companion:

```json
{ "name": "Decision", "id": "decision", "var": "finalDecision", "originalVar": "decision", "source": "=Decision", "target": "=decision", "value": "finalDecision", "type": "string", "elementId": "<stageId>-<taskId>" }
```

For equal source/destination, `id`, `var`, and `originalVar` may equal root companion when uncontended; on collision only `id`, `originalVar`, and `target` suffix, while `var`/`value` retain the existing case variable. `originalVar` is mandatory in both. `=` uses Custom Outputs shape. The variables plugin always writes Out companions and companions for task `->` case Variables so they are picker-visible.

## Connector-Rule Output → variable resolution

Connector condition rules use the same `FPSFormServiceTypeFields` shapes as tasks; `updateRootVariables` also handles them (`FPSFormServiceTypeFields.tsx:80`). Extract `->` emits reassignment output with `originalVar` and a root companion (`elementId: "root"`, `custom: true`); output `elementId` is `<stageId>-<ruleId>` or `root-<ruleId>`. Assign `=` emits `custom: true` with `value` and no root mirror (`isUpdateExistingOutput`); Loop B still emits the SDD Variable companion, with default only when declared. Bare outputs are gate-local and receive no companion.

Dispatch is defined in [io-binding/impl-json.md § Output Binding Shapes for Connector Condition Rules](../io-binding/impl-json.md#output-binding-shapes-for-connector-condition-rules), invoked last by `plugins/conditions/*/impl-json.md` `wait-for-connector`. This plugin scans SDD rows regardless of producer; task/condition producers write upstream outputs with `var: <caseVar.id>`. Skip unresolved rules with no `uipath.outputs[]`; they contribute neither pool entries nor companions. See [`connector-trigger-impl.md § Placeholder fallback`](../../../connector-trigger-impl.md#placeholder-fallback).

<!-- END: impl-json.md -->