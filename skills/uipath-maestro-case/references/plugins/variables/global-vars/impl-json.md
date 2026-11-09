# Variables — Implementation

No CLI command exists for variable declaration. Edit `caseplan.case` directly (Read → reason → Write/Edit).

## § Terminology + Resolution Semantics (read this first)

`VariablesService.findVariableByVariableId` resolves by direct, case-sensitive equality on `Variable.id`:

```ts
const variableId = strip("=vars.", lookupExpression);
return allVariables.find(v => v.id === variableId);
```

| Field | Meaning | Resolver |
|---|---|---|
| `id` | Sole match key | Yes |
| `name` | Human-readable/FE label | No |
| `var` | Wire pointer: outward target on Out formal, trigger output, or reassigned task output; mirrors `id` on bare declarations and trigger auto-emits | Only FE fallback when `id` is absent: synthesizes `=vars.<var>` (non-resolvable partial form) |
| `elementId` | FE picker scope; `validate` also requires non-empty | No |
| `source` | Runtime extraction expression, e.g. `=Decision`, `=response.subject` | No; BPMN engine reads it |
| `target` | Runtime write expression | No |
| `value` | Bound task-input value or task-output mirror of `var` | No |
| `default` | Design/runtime fallback for unwritten slot | Returned at design time when `default` is non-empty |
| `body` | JSON schema for `type: "jsonSchema"` | No |

| Array | Resolves `=vars.X` | Rule |
|---|---|---|
| `variables.inputOutputs[]` (top level) | Yes, if `id` | Canonical declaration |
| `variables.inputs[]` (top level) | Yes, by random `id` | Picker-invisible; target via companion |
| `variables.outputs[]` (top level) | Yes, formal entry | `var` points elsewhere |
| `task.data.outputs[]` | Yes, if `id` | Bare outputs have `id === var`; reassigned outputs may have collision-safe `id` and target Case variable in `var` |
| `task.data.inputs[]` | Yes, by random `id` | Picker-invisible In formal |
| `triggerNode.data.inputs.outputs[]` | Yes if `id`; no if only `var` | Pattern A (`id === var`) self-resolves; Pattern C requires `root.inputOutputs[]` companion |

A **companion** is the paired `inputOutputs[]` entry whose `id` equals the lookup name. It is required for trigger outputs without `id`, load-bearing for Out-args with a `Default`, and optional when a task output already self-declares.

### Validator contract — `validate` is stricter than the resolver

`uip maestro case validate` is stricter/different from the runtime resolver:

| Check | Match rule | Location |
|---|---|---|
| `CASE_MGMT_REFERENCE_UNBOUND` | Lenient: `id` or `name` or `var` | Referencing expression path |
| `VARIABLE_DOES_NOT_EXIST` | Strict: `id` and non-empty `elementId` | Owning `nodes[<stageId>]` |

`VARIABLE_DOES_NOT_EXIST` fails the default profile and `--strict` identically; `--strict` adds nothing. Only skeleton profiles miss it. Matching `id` is insufficient when `elementId` is missing/`""`; truthiness is tested, so `"root"`, a stage id, or a trigger id passes. Write `elementId` on every `inputOutputs[]` entry (`"root"` for case state).

`--skeleton-v2` skips task-content checks and can miss this defect when consumers are task-scoped (task entry conditions or `skipCondition`). `validate` emits at most one `VARIABLE_DOES_NOT_EXIST` per node; audit every declaration.

## Scope of this plugin

Under refactor B this plugin solely owns `variables.inputs[]`, `variables.outputs[]`, `variables.inputOutputs[]`, and `triggerNode.data.inputs.outputs[]` (formerly co-mutated with trigger plugin). It does not own `task.data.outputs[]` (task plugins self-declare), `task.data.inputs[].value` (io-binding), or top-level `bindings[]` (connector/trigger plugins).

## Target Paths

| What | Path |
|---|---|
| In formal inputs | `variables.inputs[]` |
| Out formal outputs | `variables.outputs[]` |
| Internal variables | `variables.inputOutputs[]` |
| Trigger mappings | `nodes[<triggerIndex>].data.inputs.outputs[]` |

## Uniqueness Rule

Every independently minted `var`/`id` is globally unique across the case, except the single root-companion alias for equal-name `->` extraction. On collision append a counter from 2 (`decision`, `decision2`, `decision3`; `error`, `error2`, `error3`). Preserve original `source` and `name`; suffix independently minted `var`/`id` and its `target`; on reassignment also suffix `originalVar` and mirror allocated `id`.

A normal `field -> caseVar` owns an independently minted source-side `id` although `var` points to the existing Case variable. Deduplicate that `id` globally and set `target` and `originalVar` to it; never suffix pointer `var`. For example, if `aPIOutput1` already exists, `APIOutput1 -> renamedResult` emits `id: "aPIOutput12"`, `target: "=aPIOutput12"`, `var: "renamedResult"`, and `originalVar: "aPIOutput12"`. See [io-binding § Output Binding Shapes](../io-binding/impl-json.md#output-binding-shapes).

For equal-name reassignment, when `baseId == target case-variable id`, exclude exactly the matching root companion (`variables.inputOutputs[]`, `id == target`, `elementId == "root"`) from source allocation. Exclude no task, trigger, rule, argument, or unrelated root entry. The first `greeting -> greeting` may use `id == var == originalVar == "greeting"`; with another owner use `id: "greeting2"`, `originalVar: "greeting2"`, `target: "=greeting2"`, while `var` and `value` remain `"greeting"`. Never suffix root companion or pointer `var`. `originalVar` marks reassignment so `mutateRootVariables` retains the companion.

### Pool composition (what to scan)

Scan every current `var`/`id` in `caseplan.case` globally:

| Source | Path |
|---|---|
| Root | top-level `variables.{inputs,outputs,inputOutputs}[]` |
| Task outputs | `nodes[<stage>].data.tasks[<lane>][].data.outputs[]` for every task |
| Trigger outputs | `nodes[<trigger>].data.inputs.outputs[]` for every trigger |
| Stage rule outputs | `nodes[<stage>].data.entryConditions[].rules[][].uipath.outputs[]` and `nodes[<stage>].data.exitConditions[].rules[][].uipath.outputs[]` |
| Case-exit rule outputs | `metadata.caseExitRules[].rules[][].uipath.outputs[]` |
| Task-entry rule outputs | `nodes[<stage>].data.tasks[<lane>][].entryConditions[].rules[][].uipath.outputs[]` |

Rule outputs use `elementId = <stageId>-<ruleId>`; case-exit outputs use `elementId = root-<ruleId>`. Connector rules dedupe against `{tasks ∪ triggers ∪ rules ∪ root}`; tasks/triggers also dedupe against rule outputs. `FPSFormServiceTypeFields` registers rule outputs in `getAllVariables()`; duplicate `var`/`id` across task/trigger/rule space cross-wires `allInputOutputsByElementMap` on round-trip. Skip rules without `uipath.outputs[]` (unresolved configuration; see [`connector-trigger-impl.md § Placeholder fallback`](../../../connector-trigger-impl.md#placeholder-fallback)) and placeholder tasks with `data:{}`.

## Formal-arg slot ID format

`variables.inputs[].id` and `variables.outputs[].id` MUST start with a letter: mint **`v` + 8 chars** from `[A-Za-z0-9]` (for example `vK3mNp9Qx`), as in task-input slots ([io-binding](../io-binding/impl-json.md)). Do not use a bare prefix-less random id: the formal id becomes BPMN `<uipath:input id="...">`, is referenced as `=vars.<id>`, and must satisfy C# identifier/XML NCName leading-letter/underscore constraints.

Formal slots carry readable `name` and `var`; only `id` is synthetic. Their companion uses readable name as `id`:

```json
{ "name": "literalResult", "var": "literalResult", "id": "vK3mNp9Qx", "type": "string", "default": "" }
{ "id": "literalResult", "name": "literalResult", "type": "string", "default": "" }
```

When re-minting converted plans, set `var` to the name in the same edit replacing `id`; `sdd convert` may emit name-valued `id` with no `var`. Never copy companion name into formal `id`.

## Inputs the plugin reads at Phase 3 Step 6.2

1. `sdd.md` Case Variables rows: category, type, default, `sourceTrigger(s)`, `sourceField(s)`; `Category=In` has one T-number, blank means primary.
2. `tasks/trigger-spec-cache.json`: each T-number maps to `caseShape.outputs[]` (un-minted: no `var`/`id`/`elementId`) plus `context`, `inputs`, `outputs`; written at Step 6.1; see [`../../triggers/event/impl-json.md` § Step 8](../../triggers/event/impl-json.md) for writer schema.
3. `id-map.json`: `T<N> → trigger_xxxxxx` for trigger outputs and In binding; blank In uses `id-map["T02"].id`.
4. `caseplan.case`: trigger nodes and existing root arrays.

## Dispatcher — two loops

Both loops run at Phase 3 Step 6.2 and write the same root arrays.

### Loop A — Trigger spec output dispatch (for trigger-sourced rows)

For each cache trigger, resolve `triggerId` from `id-map.json[T<N>].id`, find its node, then process each `caseShape.outputs[]`:

| State | Trigger `data.inputs.outputs[]` | Root `inputOutputs[]` |
|---|---|---|
| Unreferenced | `{name: <spec.name>, var: <spec.name>, type: <spec.type>, source: <spec.source>, value: <spec.name>}`; no `id`/`elementId`; spec `type`/`source` verbatim | **Required** — `{id: <spec.name>, name: <spec.name>, type: <spec.type>, elementId: <triggerId>, body: <spec.body>}`. For `jsonSchema`-typed entries (e.g., `response`, `Error`), the companion holds the full body schema that the FE picker uses to discover sub-fields. Without it, sub-field picking is broken and the variable can't be selected in connector-task input bindings. |
| `Category=Variable` reference | `{name: <last sourceField segment>, var: <sdd-name>, type: <sdd type>, source: "=<raw sourceField>", value: <sdd-name>}`; no `id`/`elementId`; SDD type wins | `{id: <sdd-name>, name: <sdd-name>, type: <sdd type>, elementId: "root", custom: true}` |
| `Category=In` | Emit nothing here; Loop B only, even when name matches top-level spec | — |
| `Category=Out` | **REJECT** direction mismatch | — |

Top-level matching is exact, case-sensitive spec `name`; a matching SDD name replaces only that top-level auto-emit. Sub-field references add Pattern C and do not replace top-level auto-emit. Preserve connector casing verbatim; never re-case or alias. Multiple rows may write separate trigger entries but share one companion, first-write-wins on type/default; Phase 2 rejects conflicts.

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

**File-type carve-out:** when the spec output's `type` is `"file"` (or `"octet-stream"` — normalize to `"file"`), both rows above additionally require:
- `triggerNode.outputs[]` entry: add `target: "=orchestrator.JobAttachments"` — runtime persists attachment bytes via this expression. Without it, the JobAttachment record is never written.
- `root.inputOutputs[]` companion: add `body: <FILE_TYPE_JSON_SCHEMA verbatim>` (see [`## file type`](#file-type)). Pattern C companions normally have no body, but file-type companions MUST carry the FILE_TYPE_JSON_SCHEMA so the FE picker can navigate `=vars.<id>.FullName` sub-fields and activate the JobAttachment widget.

`Category=In` is never dispatched by spec-name matching. `Category=Variable` with `sourceTrigger(s)` is Loop A; without it is Loop B.

### Loop B — non-extraction rows (In / Out / pure-state Variable)

Process every `Category=In` (any trigger, single or blank), `Category=Out`, and triggerless `Category=Variable`:

| Row | `root.inputs[]` | `root.outputs[]` | `root.inputOutputs[]` |
|---|---|---|---|
| Variable, no trigger | — | — | `{id: <name>, name: <name>, type: <type>, elementId: "root", default: <value if Default set>, custom: true}` |
| In | `{id: v<random8>, name: <name>, type: <type>, default: <value>, elementId: <triggerId>}` | — | `{id: <name>, name: <name>, type: <type>, elementId: <triggerId>}`; no `custom`; also write bridge |
| Out | — | `{id: v<random8>, name: <name>, type: <type>, var: <name>}` | `{id: <name>, name: <name>, type: <type>, default: <value or "">, elementId: "root"}`; no `custom` |
| InOut | unsupported in v1 | unsupported in v1 | unsupported in v1 |

In trigger resolution: `id-map.json[T<N>].id` for row `sourceTriggers`; blank means `id-map["T02"].id`. Formal, companion, and bridge use that same trigger. If Loop A already wrote the same `inputOutputs[].id`, do not rewrite; In rows never straddle loops. `Category=InOut` is rejected by Phase 2 because v1 enum is `In | Out | Variable`.

## Pattern shapes by category

### Pure state Variable (no trigger source)

Write only root companion, with `custom: true`, `elementId: "root"`; no trigger or formal writes. `jsonSchema` also requires `body` and `_jsonSchema`; see [`## jsonSchema type`](#jsonschema-type).

### `default` encoding — EVERY type, MANDATORY

`default` is always a JSON string, regardless of `type`; never object, array, number, or boolean. Encode JSON-schema values as strings (`"{\"amount\":125.5}"`), integer as `"5"`, boolean as `"true"`, date as `"2029-10-12"`, and file/no default as `""`.

A non-primitive default is silently deleted by the caseplan→BPMN converter, which retains only primitive fields ([`bpmn-moddle.ts` `onlyPrimitiveVariableFields`](https://github.com/UiPath/PO.Frontend/blob/develop/src/services/serialization/bpmn-moddle.ts#L323-L331)). The variable is then null at runtime while adjacent string-defaulted variables retain `default=""`; a first task read can fail `AGENT_STARTUP.INPUT_VALIDATION_ERROR / <input> Field required`. `uip maestro case validate` returns `Valid`, FE Zod uses `z.any()`, and serialization reports nothing. **This recipe is the enforcement point** — Step 12 Check 14 is the backstop.

### Trigger-sourced Variable (Pattern C)

SDD row: `Category=Variable`, `sourceTriggers: T02`, `sourceFields: response.subject`.

```json
// triggerNode.data.inputs.outputs[]  (the trigger plugin's caseplan node — written by THIS plugin under B)
{ "name": "subject", "var": "calendarTitle",
  "source": "=response.subject", "type": "string", "value": "calendarTitle" }
// No `id`, no `elementId` — FE auto-emit convention. `name` is the last segment of sourceField path.

// variables.inputOutputs[]
{ "id": "calendarTitle", "name": "calendarTitle", "type": "string",
  "elementId": "root", "custom": true }
```

`elementId: "root"` on the root companion places the variable under FE's Case Variables panel (correct semantics — it's case state, not a formal trigger argument). `custom: true` marks it user-declared.

### Trigger-sourced Variable — multi-trigger

SDD row: `Category=Variable`, `sourceTriggers: T02, T03`, `sourceFields: T02: response.user; T03: response.initiator`.

Write TWO `triggerNode.outputs[]` entries (one per trigger node) + ONE shared `root.inputOutputs[]` companion:

```json
// On trigger_T02's node:
{ "name": "user", "var": "caseStarter",
  "source": "=response.user", "type": "string", "value": "caseStarter" }

// On trigger_T03's node:
{ "name": "initiator", "var": "caseStarter",
  "source": "=response.initiator", "type": "string", "value": "caseStarter" }
// No `id`, no `elementId` on either entry. `name` reflects each trigger's spec sub-field segment.

// root.inputOutputs[] — single shared companion
{ "id": "caseStarter", "name": "caseStarter", "type": "string", "elementId": "root", "custom": true }
```

Resolver doesn't care that two trigger entries write to the same `vars.caseStarter` slot — last writer wins, and only one trigger fires per case lifecycle. The companion is the canonical declaration.

### In argument

SDD row: `Category=In`, optional `sourceTriggers: T<N>` (a single T-number selecting the bound trigger; blank → primary trigger T02). `sourceFields` is empty for In rows. **Works on any trigger type — manual, timer, or event.** For event triggers, the bridge mechanics are identical; the formal slot's `default` propagates to the companion at trigger fire (no caller-override path since events have no API caller, but the structural emission is the same).

**Trigger resolution.** `<triggerId>` in the entries below = `id-map.json[T<N>].id` for the trigger named by `sourceTriggers`; blank `sourceTriggers` → `id-map["T02"].id` (the primary trigger). Entries 1 (formal slot) and 2 (companion) carry it as `elementId`; entry 3 (bridge) is written on that same trigger node's `data.inputs.outputs[]`. `sourceFields` is not consulted for In.

> **Manual bound trigger:** a manual trigger is spelled `data.inputs.serviceType: "None"` — `"None"` is a named arm in the product's own `getTriggerType` switch, and 503 of 542 corpus trigger nodes carry it (see [`../../triggers/manual/impl-json.md`](../../triggers/manual/impl-json.md)). Older plans may omit `inputs` entirely; both forms read as manual, so **never assume `data.inputs` is absent**. When the bound trigger is manual (the common case — the primary trigger is usually manual), append the bridge to the existing `data.inputs.outputs`, creating `outputs: []` on the node's existing `data.inputs` if that array is missing. Do not change or remove a `serviceType: "None"` that is already there.

Three entries — formal slot + companion + bridge:

```json
// 1. root.inputs[]  — formal-arg slot (caller writes here at fire, OR initialized via default for event triggers)
{ "id": "v<random8>", "name": "applicantName", "type": "string",
  "default": "", "elementId": "<triggerId>" }

// 2. root.inputOutputs[]  — companion (readable as =vars.applicantName)
{ "id": "applicantName", "name": "applicantName", "type": "string",
  "elementId": "<triggerId>" }

// 3. triggerNode.data.inputs.outputs[]  — bridge from formal slot to companion
{ "name": "applicantName", "type": "string", "source": "=vars.v<random8>", "var": "applicantName" }
// No `id`, no `elementId` on bridge — FE convention. `type` matches the SDD row's Type column.
```

> **An In-arg bridge carries `source`, never `value`.** The two Pattern C shapes immediately above this section (§ Trigger-sourced Variable, § Trigger-sourced Variable — multi-trigger) carry `value: "<companionName>"`; an In-arg bridge MUST NOT. Do not merge the two shapes. The In-arg bridge's only copy instruction is `source: "=vars.<formal-slot-id>"` — the formal slot's `id` from entry 1, not the argument's name. Emitting `{name, var, type, value}` with no `source` produces a bridge that copies nothing: `uip maestro case validate` still returns `Valid`, and `=vars.<name>` is undefined at runtime. Step 12 Check 17 is the backstop.

**Why three entries instead of one?** The runtime resolver (`VariablesService.findVariableByVariableId`) is a single string-equality find on `Variable.id`. The caller (or trigger fire for event triggers) writes the formal-arg's value into `vars.v<random8>` at trigger fire (because `inputs[].id` is `v<random8>`); downstream code wants to read it as `=vars.applicantName` (because that's the readable name). There is no automatic forwarding between the two slots — the bridge entry on `triggerNode.outputs[]` executes the copy at fire time: `source: "=vars.v<random8>"` reads the formal slot, `var: "applicantName"` writes to the companion's slot. Without the bridge, `=vars.applicantName` resolves to undefined. The companion's `inputOutputs[]` entry alone declares the *name* in the namespace, but holds no *value* because nobody writes to it.

> **Placeholder trigger interaction:** if the **bound trigger** (the one named by `sourceTriggers`, or the primary trigger when blank) is a placeholder (any type), write entries 1 + 2 only; skip the bridge (entry 3) — the placeholder has no `data.inputs.outputs` array. The placeholder trigger never fires, so the bridge would never execute anyway. **Consequence:** at runtime `vars.<name>` (the companion slot) is undefined — the `default` on the `inputs[]` formal slot does NOT propagate to the companion without the bridge. This is expected: a placeholder case is structurally incomplete and not meant to run until the trigger is resolved. Re-generate from scratch (Rule 7) after the trigger resolves to get the working bridge.

**File-type In-arg carve-out:** when `type === "file"`:
- Formal slot (entry 1) MUST add `body: <FILE_TYPE_JSON_SCHEMA>` (see [`## file type`](#file-type)) — drives entry-points.json `$ref: "#/definitions/job-attachment"` at packaging
- Companion (entry 2) MUST add `body: <FILE_TYPE_JSON_SCHEMA>` — drives FE picker sub-field navigation (`=vars.<id>.FullName`)
- Bridge (entry 3) unchanged — no `target` on the bridge; the runtime caller has already uploaded the bytes via JobAttachments API before case-start
- `default` MUST stay `""` — FE rejects any other value for file Variables (`InputOutputArgumentsDialog.tsx:148`)

### Out argument

SDD row: `Category=Out`. **Companion is ALWAYS emitted at write time** (per FE convention — `UnifiedBuildCaseDataManager.tsx:298-324` always writes the companion when an Out-arg is created). The BPMN packager's `collapseArgumentCompanions` (`CaseManagementRootConverterUtils.ts:211-237`) may collapse the companion at packaging time, but that's downstream of the skill.

| SDD `Default` | Producer in the SDD (via task's `->` Outputs row or `=` Updates row) | Runtime behavior |
|---|---|---|
| empty | yes | Producer task fires → writes to `vars.<name>` → caller gets that value at case end. If producer fails to fire, caller gets `""` (the companion's empty default). |
| present | yes | Producer fires → overwrites companion default. If producer skipped, companion default returned. |
| present | no | Companion default always returned at case end. |
| empty | no | **Pure orphan** — Out-arg producer-presence validator AskUserQuestion at end of Phase 3 (see [`io-binding/impl-json.md` § Check 2](../io-binding/impl-json.md)). Author picks: (a) add producer, (b) add Default, (c) recategorize, (d) continue with best-effort emit. |

#### Shape

Same shape regardless of Default presence (two entries):

```json
// 1. variables.outputs[]  — formal Out-arg pointer
{ "id": "v<random8>", "name": "finalDecision", "type": "string",
  "var": "finalDecision" }
// var is a POINTER — at case end, engine reads vars.finalDecision via this pointer

// 2. variables.inputOutputs[]  — companion (always written)
{ "id": "finalDecision", "name": "finalDecision", "type": "string",
  "default": "<value or empty string>", "elementId": "root" }
// no custom — argument companions are NOT custom per FE convention
```

**Default + producer precedence at runtime:** if a producer task is declared AND fires, its output value overwrites the companion's default in `vars.<name>`. If the producer task does NOT fire (e.g., skipped by stage entry condition, or stage exited without running it), the companion's default is what gets returned at case end. The runtime resolver does not see "default vs producer" — it sees a single slot whose value is whatever was last written to it; the design-time companion default is the initial value at case start.

### InOut argument

> **NOT supported in v1.** The SDD template's Category enum is `In | Out | Variable` only. If real customer cases require InOut, this section documents the FE-canonical shape for future re-introduction. Skill validators reject `Category=InOut` in v1 (Phase 2 — invalid Category value). If revived, `<triggerId>` resolves per § In argument (`id-map[<sourceTriggers T-number>].id`; blank → `id-map["T02"].id`).

Combines In + Out. One shared companion serves both:

```json
// 1. root.inputs[]  — formal In slot
{ "id": "v<random8-in>", "name": "claimId", "type": "string",
  "default": "", "elementId": "<triggerId>" }

// 2. root.inputOutputs[]  — shared companion
{ "id": "claimId", "name": "claimId", "type": "string", "elementId": "<triggerId>" }

// 3. root.outputs[]  — formal Out slot pointing at same companion
{ "id": "v<random8-out>", "name": "claimId", "type": "string", "var": "claimId" }

// 4. triggerNode.outputs[]  — bridge from In formal slot to shared companion
{ "name": "claimId", "type": "string", "source": "=vars.v<random8-in>", "var": "claimId" }
```

Caller writes value; bridge copies to companion at trigger fire; task body updates `vars.claimId`; case end returns updated value to caller.

## Phase 3 Spec-dependent Validation

Run during dispatcher loop; log per [`../../logging/impl-json.md`](../../logging/impl-json.md):

| Condition | Severity/action |
|---|---|
| `sourceField` top-level or nested path absent in referenced `caseShape.outputs[]` | ERROR; halt, AskUserQuestion with available keys (e.g. `Title`, `Description`, `Location`, …), update SDD; never defer via runtime fallback |
| Existing sourceField type differs from SDD Type | WARNING; proceed and log to `build-issues.md` |
| Multi-trigger `sourceFields` T-number not in `sourceTriggers`, or vice versa | ERROR; reject |

Phase split: Phase 2 checks missing/empty Category; `Category=Out` with `sourceTriggers`; `Category=In` with >1 T-number; `Category=In` with nonempty `sourceFields`; Same-Name pair column mismatch; missing In/Out Type; nonexistent `sourceTriggers` trigger. Phase 3 checks spec path, SDD/spec type mismatch, and multi-trigger T-number mismatch. Out producer presence is Phase 3 io-binding validation at phase end. Phase 3 does not repeat Phase 2 checks. `Category=In` on event triggers is allowed in v1; its three-entry structure is identical and event default propagates through the bridge.

## Custom Outputs (`custom: true` on task.data.outputs[])

Task plugins own these outputs; this plugin only declares the referenced root variable when absent. Custom output writes a fixed constant, not task response:

| Field | Standard | Custom |
|---|---|---|
| `source` | `"=<runtime-path>"` (SDD left side, verbatim) | omitted |
| `value` | mirrors var | `"=<literal>"` or `"=js:<expr>"` |
| `custom` | omitted/`false` | `true` |
| `target` | `"=<varId>"` | omitted |

For SDD `=` rows (set/compute/copy; see [`../io-binding/planning.md`](../io-binding/planning.md)), task plugin emits `custom: true`, `var: <caseVar.id>`, `value: <expression>`, `source: <same as value>`, `elementId: "root"`; no root mirror because of FE `isUpdateExistingOutput` filter (`VariableMutationUtils.ts:49-64`). `->` performs schema extraction/renaming; `=` performs literal/computed/variable-reference writes.

## jsonSchema type

A `jsonSchema` variable MUST carry `body` and `_jsonSchema`, the same schema object from the SDD Description (for example `Body schema: {"type": "object"}`). `body: null` leaves it untyped: FE cannot pick subfields, `=vars.<id>.<field>` cannot be selected, and `validate` still reports `Valid`.

`sdd convert` emits companions with `body: null` and omits them from `Data.Unresolved[]`; fill both fields after conversion. This is the named exception to SKILL.md Rule 4's settled-shape clause. `default` remains a string; `body` and `_jsonSchema` are objects:

```json
{ "id": "caseData", "name": "caseData", "type": "jsonSchema", "default": "{\"status\":\"Open\"}", "body": { "type": "object", "properties": { "status": { "type": "string" } } }, "_jsonSchema": { "type": "object", "properties": { "status": { "type": "string" } } } }
```

Empty default is `""` or `"{}"`; `sdd convert` uses `""`. Never object `{}`.

## file type

File Variables hold a JobAttachment record (`{ID, FullName, MimeType, Metadata}`), not a path or bytes. Runtime writes the record when the producing task completes.

`body` MUST be the FILE_TYPE_JSON_SCHEMA constant **byte-for-byte** (matches FE `VariableConstants.ts:10-36`). The `x-uipath-resource-kind: "JobAttachment"` marker activates the FE picker; missing `description` / `additionalProperties` fields cause round-trip drift on FE re-save.

Normalize `"octet-stream"` → `"file"` before emitting. The FE's `isFileType` accepts both, but only `"file"` round-trips through CLI emission.

```json
{ "id": "evidenceDoc", "name": "evidenceDoc", "type": "file",
  "body": {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "type": "object",
    "properties": {
      "ID":       { "type": "string", "description": "Orchestrator attachment key" },
      "FullName": { "type": "string", "description": "File name" },
      "MimeType": { "type": "string", "description": "The MIME type of the content, such as application/json or image/png" },
      "Metadata": { "type": "object",
                    "description": "Dictionary<string, string> of metadata",
                    "additionalProperties": { "type": "string" } }
    },
    "required": ["ID"],
    "x-uipath-resource-kind": "JobAttachment"
  },
  // Case-root Variable only. An In argument's companion keeps its trigger elementId and carries neither default nor custom (Loop B table).
  "default": "", "custom": true, "elementId": "root" }
```

## date / datetime types

Primitive — no body, no target. FE renders DatePicker / DateTimePicker based on the type.

```json
{ "id": "submittedOn", "name": "submittedOn", "type": "date",
  // Case-root Variable only. An In argument's companion keeps its trigger elementId and carries neither default nor custom (Loop B table).
  "default": "", "custom": true, "elementId": "root" }

{ "id": "lastSeen", "name": "lastSeen", "type": "datetime",
  "default": "=js:new Date().toISOString()", "custom": true, "elementId": "root" }
```

## Expression Syntax

See [`../../../bindings-and-expressions.md`](../../../bindings-and-expressions.md). Plain reads use `=vars.x`; comparisons use `=js:vars.x === 'val'`; never `$vars.x`.

## Task Output → variable resolution

Task `data.outputs[]` with `id` self-declares (always under `->`). Reassignment preserves source-side `id`, points `var` to Case variable, and requires `originalVar`:

```json
{ "name": "Decision", "id": "decision", "var": "finalDecision", "originalVar": "decision", "source": "=Decision", "target": "=decision", "value": "finalDecision", "type": "string", "elementId": "<stageId>-<taskId>" }
```

`originalVar` is required for FE Scenario B/D and makes `mutateRootVariables` (`VariableMutationUtils.ts:135`) skip root mirroring, preserving the companion. Equal-name reassignment may have identical `id`, `var`, `originalVar` and root companion; unrelated collision suffixes only `id`, `originalVar`, `target`, never `var`/`value`. `=` uses separate `custom: true` Scenario E output. Variables plugin always writes Out companions and task `->` Case-variable companions for picker visibility.

## Connector-Rule Output → variable resolution

Connector rule outputs use the same FE `FPSFormServiceTypeFields` shapes as task outputs; `updateRootVariables` also handles them (`FPSFormServiceTypeFields.tsx:80`):

- Extract `->`: rule emits reassignment entry with `originalVar`; Loop B emits matching root companion (`elementId: "root"`, `custom: true`) from SDD `Category=Variable`. Rule output `elementId` is `<ownerNodeId>-<ruleId>` (`<stageId>-<ruleId>` or `root-<ruleId>`).
- Assign `=`: rule emits `custom: true` Scenario E with `value: "<expression>"`; no root mirror via `isUpdateExistingOutput`; Loop B emits companion, populating `default` only when SDD declares one.
- Bare: gate-local output named like spec field (`response`/`Error`); no companion.

Dispatch is in [io-binding/impl-json.md § Output Binding Shapes for Connector Condition Rules](../io-binding/impl-json.md#output-binding-shapes-for-connector-condition-rules), invoked by condition plugins' `wait-for-connector` recipe. This plugin scans SDD rows agnostically of producer; task/condition producer writes upstream `outputs[]` with `var: <caseVar.id>`. Skip rules without `uipath.outputs[]`; they add neither pool outputs nor Loop B companions. See [`connector-trigger-impl.md § Placeholder fallback`](../../../connector-trigger-impl.md#placeholder-fallback).

<!-- END: impl-json.md -->
