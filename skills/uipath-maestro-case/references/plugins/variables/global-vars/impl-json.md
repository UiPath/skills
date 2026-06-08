# Variables — Implementation

No CLI command exists for variable declaration. Edit `caseplan.json` directly (Read → reason → Write/Edit).

## § Terminology + Resolution Semantics (read this first)

The runtime resolver (`VariablesService.findVariableByVariableId`) is **direct, case-sensitive string equality on `Variable.id`**. Knowing this prevents the most common wiring bugs.

```ts
// Resolver pseudocode
const variableId = strip("=vars.", lookupExpression);
return allVariables.find(v => v.id === variableId);
```

| Field | What it does | Read by resolver? |
|---|---|---|
| `id` | The resolver match key | YES — sole match key |
| `name` | Human-readable label / FE display | No — never matched |
| `var` | Pointer field. On wires (Out-arg formal, trigger output): points OUTWARD to the slot. On self-declarations (task output, trigger spec auto-emit): mirrors `id`. | Only when `id` is absent (FE fallback: synthesizes `Variable.id = "=vars.<var>"` — partial form, non-resolvable) |
| `elementId` | FE picker scope only. Controls which panel displays the variable. **Not used by the resolver.** | No |
| `source` | Runtime extraction expression (e.g., `=Decision`, `=response.subject`) | No — read by BPMN engine at runtime |
| `target` | Runtime write expression (rarely matters) | No |
| `value` | Currently-bound input value (task inputs) or mirror of var (task outputs) | No |
| `default` | Design-time / runtime fallback when slot is unwritten | Returned at design time when `default` is non-empty |
| `body` | JSON schema (for `type: "jsonSchema"`) | No |

**Which arrays contribute to the namespace:**

| Array | Resolves `=vars.X`? | Notes |
|---|---|---|
| `variables.inputOutputs[]` *(top level)* | YES if `id` present | Canonical declaration site |
| `variables.inputs[]` *(top level)* | YES — by random `id` | Picker-invisible (resolution works, but the FE picker does not surface it); target only via the companion |
| `variables.outputs[]` *(top level)* | YES (the formal entry) | But its `var` points elsewhere — see Out-arg shape below |
| `task.data.outputs[]` | YES if `id` present | Self-declares — task plugin writes id matching the SDD-given name |
| `task.data.inputs[]` | YES — by random `id` | Picker-invisible; used for the In-arg formal slot |
| `triggerNode.data.uipath.outputs[]` | YES if `id` present; **NO if only `var` (no `id`)** | Pattern A entries (`id === var`) self-resolve; Pattern C entries (`var` only) require a companion in `root.inputOutputs[]` |

**"Companion" = the paired `inputOutputs[]` entry whose `id` matches the lookup name.** Required for trigger outputs that lack `id`; load-bearing for Out-args with a `Default` value; optional when the producer (task output) already self-declares.

## Scope of this plugin

Under the B refactor, this plugin is **the sole owner** of:

| Array | Owns? |
|---|---|
| `variables.inputs[]` *(top level)* | Yes |
| `variables.outputs[]` *(top level)* | Yes |
| `variables.inputOutputs[]` *(top level)* | Yes |
| `triggerNode.data.uipath.outputs[]` | **Yes** — sole owner under B (was co-mutated with trigger plugin in previous design) |
| `task.data.outputs[]` | No — task plugins self-declare; this plugin's writes never touch them |
| `task.data.inputs[].value` | No — io-binding owns this |
| top-level `bindings[]` | No — connector / trigger plugins own resource bindings |

## Target Paths

| What | JSON path |
|---|---|
| In argument inputs | `variables.inputs[]` *(top level)* |
| Out argument outputs | `variables.outputs[]` *(top level)* |
| All internal variables | `variables.inputOutputs[]` *(top level)* |
| Trigger output mappings | `nodes[<triggerIndex>].data.uipath.outputs[]` |

## Uniqueness Rule

Every `var` / `id` must be globally unique across the case. When a name collides, append a counter starting at 2:

```
"decision" exists → "decision2" → "decision3"
"error" + "error2" exist → "error3"
```

The `source` and `name` fields keep the original value — only `var` / `id` / `target` get the suffix.

### Pool composition (what to scan)

Build the uniqueness pool from EVERY `var` / `id` currently in `caseplan.json`. The pool is global — minting in any one location must consult ALL of the following:

| Source | JSON path | Notes |
|---|---|---|
| Root variables | top-level `variables.{inputs,outputs,inputOutputs}[]` | The canonical case-variable namespace |
| Task outputs | `nodes[<stage>].data.tasks[<lane>][].data.outputs[]` (for every task) | Self-declared task outputs |
| Trigger outputs | `nodes[<trigger>].data.uipath.outputs[]` (for every trigger node) | Plain-name auto-emit + Pattern C wires |
| **Stage entry / exit rule outputs** | `nodes[<stage>].data.entryConditions[].rules[][].uipath.outputs[]` AND `nodes[<stage>].data.exitConditions[].rules[][].uipath.outputs[]` | Connector-bound condition rules — outputs minted under `elementId = <stageId>-<ruleId>` |
| **Case-exit rule outputs** | `metadata.caseExitRules[].rules[][].uipath.outputs[]` | Connector-bound case-exit rules — outputs minted under `elementId = root-<ruleId>` |
| **Task-entry rule outputs** | `nodes[<stage>].data.tasks[<lane>][].entryConditions[].rules[][].uipath.outputs[]` (for every task) | Connector-bound task-entry rules — outputs minted under `elementId = <stageId>-<ruleId>` |

**Both directions.** When a connector rule mints outputs, dedupe against the union {tasks ∪ triggers ∪ rules ∪ root}. When a task or trigger mints outputs, dedupe against existing rule outputs too — NOT just tasks + triggers. The shared FE form (`FPSFormServiceTypeFields`) registers rule outputs in the same global pool (`getAllVariables()`), so any duplicate `var` / `id` across the {task, trigger, rule} space collapses in `allInputOutputsByElementMap` and cross-wires ownership at round-trip.

**Skip guard.** Rules with no `uipath.outputs[]` (connector configuration unresolved — see [`connector-trigger-common.md § Placeholder fallback`](../../../connector-trigger-common.md#placeholder-fallback)) contribute zero outputs to the pool and must be skipped during enumeration. Same skip pattern as placeholder tasks (`data:{}`).

## Inputs the plugin reads at Phase 3 Step 6.2

1. **`tasks.md`** variable T-entries — for category, type, default, sourceTrigger(s), sourceField(s)
2. **`tasks/trigger-spec-cache.json`** — for each trigger's `caseShape.outputs[]` (un-minted), keyed by T-number. Written by trigger plugin at Step 6.1; see [`../../triggers/event/impl-json.md` § Step 8](../../triggers/event/impl-json.md) for the writer-side schema. Top-level keys are T-numbers (e.g., `T02`, `T03`); values have `context`, `inputs`, `outputs` from the trigger's `caseShape`, un-minted (no `var` / `id` / `elementId` synthesized).
3. **`id-map.json`** — for `T<N> → trigger_xxxxxx` lookup when writing trigger.outputs[]
4. **`caseplan.json`** — to locate trigger nodes (by triggerId from id-map) and existing root variable arrays

## Dispatcher — two loops

The plugin runs **two iterations** at Phase 3 Step 6.2. Both write into the same root variable arrays but iterate over different inputs.

### Loop A — Trigger spec output dispatch (for trigger-sourced rows)

For each trigger in `trigger-spec-cache.json`:
1. Look up triggerId from `id-map.json[T<N>].id`
2. Find the trigger node in `caseplan.json` by id
3. For each spec output in cache's `outputs[]`:

| Spec output state | SDD reference | `triggerNode.outputs[]` write | `root.inputs[]` | `root.outputs[]` | `root.inputOutputs[]` |
|---|---|---|---|---|---|
| Not referenced by SDD | (no row) | `{name: <spec.name>, var: <spec.name>, type: <spec.type>, source: <spec.source>, value: <spec.name>}` — `type` and `source` come from the spec entry verbatim (e.g., `type: "jsonSchema"` + `source: "=response"`). **No `id`, no `elementId`** per FE auto-emit convention (`IntsvcActivityPropertiesUtils.tsx:288-302`). Plain-name auto-emit. | — | — | **Required** — `{id: <spec.name>, name: <spec.name>, type: <spec.type>, elementId: <triggerId>, body: <spec.body>}`. For `jsonSchema`-typed entries (e.g., `response`, `Error`), the companion holds the full body schema that the FE picker uses to discover sub-fields. Without it, sub-field picking is broken and the variable can't be selected in connector-task input bindings. |
| Referenced as `Category=Variable` | row's `sourceField` path | `{name: <last segment of sourceField path>, var: <sdd-name>, type: <sdd-row.type>, source: "=<row.sourceField>", value: <sdd-name>}` (Pattern C wire). **No `id`, no `elementId`** — resolution flows through the companion in `root.inputOutputs[]`, not through this entry. `name` is the spec sub-field segment (e.g., `"Title"` when `sourceField: response.Title`) — matches FE convention where `name` is the display label of the source field. `source` is `=` prepended to the raw `sourceField` value from tasks.md; `type` comes from the SDD row, NOT the spec — author's chosen type wins. | — | — | `{id: <sdd-name>, name: <sdd-name>, type: <sdd-row.type>, elementId: "root", custom: true}` — companion with elementId="root" routes variable to Case Variables panel; `custom: true` marks it user-declared. |
| Referenced as `Category=In` | — (In doesn't reference a payload field; the value comes from caller or Default at fire) | Bridge entry per § In argument below — `{name: <sdd-name>, type: <sdd-row.type>, source: "=vars.<inputId>", var: <sdd-name>}`. Works on ANY trigger type (manual, timer, event). For event triggers, the bridge propagates the formal slot's `default` to the companion at trigger fire (no caller-override path, but mechanics are identical). | per § In argument below | — | per § In argument below |
| Referenced as `Category=Out` | — | **REJECT** (direction mismatch — Out-args flow case→caller) | — | — | — |

**File-type carve-out:** when the spec output's `type` is `"file"` (or `"octet-stream"` — normalize to `"file"`), both rows above additionally require:
- `triggerNode.outputs[]` entry: add `target: "=orchestrator.JobAttachments"` — runtime persists attachment bytes via this expression. Without it, the JobAttachment record is never written.
- `root.inputOutputs[]` companion: add `body: <FILE_TYPE_JSON_SCHEMA verbatim>` (see [`## file type`](#file-type)). Pattern C companions normally have no body, but file-type companions MUST carry the FILE_TYPE_JSON_SCHEMA so the FE picker can navigate `=vars.<id>.FullName` sub-fields and activate the JobAttachment widget.

**Dedup rule:** if multiple SDD rows reference the same trigger spec output (rare, but possible across multi-trigger cases), each writes its own `triggerNode.outputs[]` entry but they share one `root.inputOutputs[]` declaration (first-write-wins on type / default; Phase 2 validator rejects conflicts).

**Top-level match semantics:** matching is by **top-level spec output name only** (i.e., the `name` field of an entry in `caseShape.outputs[]` — `response`, `Error`, etc.). When an SDD row's Name equals the top-level spec name, the SDD-named entry **replaces** the would-be plain-name auto-emit for that exact entry; do not write both.

**Name matching is case-sensitive.** Preserve the spec's name verbatim in the emitted `name`/`var`/`id` fields. Connector specs typically return PascalCase top-level keys (`response`, `Error`, `Title`); SDDs may use camelCase. If an SDD row's Name is `subject` and the spec returns `Subject`, **the match does NOT fire** — they are different identifiers per the runtime resolver (`VariablesService.findVariableByVariableId` performs direct case-sensitive string equality). To match, the SDD Name must equal the spec's name byte-for-byte. The skill never re-cases or aliases.

**Sub-field references DO NOT trigger replacement.** When SDD references a sub-field path (e.g., `sourceField: response.Title`), the Pattern C entry is in ADDITION to — not in place of — the top-level `response` auto-emit. Worked example for SDD `calendarTitle ← response.Title` (Variable, type=string) on a trigger whose spec returns two top-level `jsonSchema` outputs `response` and `Error`:

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

### Loop B — SDD-only rows (rows with no trigger source)

For each variable T-entry in `tasks.md` that has **no `sourceTrigger` / `sourceTriggers` field**:

| SDD row | `root.inputs[]` | `root.outputs[]` | `root.inputOutputs[]` |
|---|---|---|---|
| `Category=Variable` (pure state, no trigger) | — | — | `{id: <sdd-name>, name: <sdd-name>, type: <type>, elementId: "root", default: <value if Default set>, custom: true}` |
| `Category=In` (any trigger type — manual / timer / event) | `{id: <random9>, name: <sdd-name>, type: <type>, default: <value>, elementId: <triggerId>}` | — | `{id: <sdd-name>, name: <sdd-name>, type: <type>, elementId: <triggerId>}` (no `custom` — argument companion). Additionally write the **bridge** on `triggerNode.outputs[]` (see § In argument below). |
| `Category=Out` (companion ALWAYS emitted — see § Out argument) | — | `{id: <random9>, name: <sdd-name>, type: <type>, var: <sdd-name>}` (formal-arg pointer) | `{id: <sdd-name>, name: <sdd-name>, type: <type>, default: <value or "">, elementId: "root"}` (no `custom`) |
| `Category=InOut` | (not supported in v1 — see SDD template) | (not supported in v1) | (not supported in v1) |

> Loop A and Loop B can write the SAME `root.inputOutputs[]` entry when an SDD row appears in both contexts (e.g., a `Category=Variable` row with `sourceTrigger`). Apply dedup by `id`: if an entry with the same `id` already exists from Loop A, do not re-write in Loop B; Phase 2 validator has already confirmed there's no Type/Default conflict.

## Pattern shapes by category

> Cross-reference: this section is the canonical JSON shape per category. The dispatcher logic that decides which shape to emit is in § Dispatcher — two loops above.

### Pure state Variable (no trigger source)

SDD row: `Category=Variable`, no `sourceTriggers`, optional `Default`.

```json
// variables.inputOutputs[]
{ "id": "caseStatus", "name": "caseStatus", "type": "string",
  "custom": true, "elementId": "root", "default": "Open" }
```

No trigger.outputs[] write, no root.inputs[] / outputs[] writes.

### Trigger-sourced Variable (Pattern C)

SDD row: `Category=Variable`, `sourceTriggers: T02`, `sourceFields: response.subject`.

```json
// triggerNode.data.uipath.outputs[]  (the trigger plugin's caseplan node — written by THIS plugin under B)
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

SDD row: `Category=In`, `triggerRef: T02`. **Works on any trigger type — manual, timer, or event.** For event triggers, the bridge mechanics are identical; the formal slot's `default` propagates to the companion at trigger fire (no caller-override path since events have no API caller, but the structural emission is the same).

Three entries — formal slot + companion + bridge:

```json
// 1. root.inputs[]  — formal-arg slot (caller writes here at fire, OR initialized via default for event triggers)
{ "id": "<random9>", "name": "applicantName", "type": "string",
  "default": "", "elementId": "<triggerId>" }

// 2. root.inputOutputs[]  — companion (readable as =vars.applicantName)
{ "id": "applicantName", "name": "applicantName", "type": "string",
  "elementId": "<triggerId>" }

// 3. triggerNode.data.uipath.outputs[]  — bridge from formal slot to companion
{ "name": "applicantName", "type": "string", "source": "=vars.<random9>", "var": "applicantName" }
// No `id`, no `elementId` on bridge — FE convention. `type` matches the SDD row's Type column.
```

**Why three entries instead of one?** The runtime resolver (`VariablesService.findVariableByVariableId`) is a single string-equality find on `Variable.id`. The caller (or trigger fire for event triggers) writes the formal-arg's value into `vars.<random9>` at trigger fire (because `inputs[].id` is `<random9>`); downstream code wants to read it as `=vars.applicantName` (because that's the readable name). There is no automatic forwarding between the two slots — the bridge entry on `triggerNode.outputs[]` executes the copy at fire time: `source: "=vars.<random9>"` reads the formal slot, `var: "applicantName"` writes to the companion's slot. Without the bridge, `=vars.applicantName` resolves to undefined. The companion's `inputOutputs[]` entry alone declares the *name* in the namespace, but holds no *value* because nobody writes to it.

> **Placeholder trigger interaction:** if the trigger is a placeholder (any type), write entries 1 + 2 only; skip the bridge (entry 3) — the placeholder has no `data.uipath.outputs` array. The placeholder trigger never fires, so the bridge would never execute anyway. **Consequence:** at runtime `vars.<name>` (the companion slot) is undefined — the `default` on the `inputs[]` formal slot does NOT propagate to the companion without the bridge. This is expected: a placeholder case is structurally incomplete and not meant to run until the trigger is resolved. Re-generate from scratch (Rule 6) after the trigger resolves to get the working bridge.

**File-type In-arg carve-out:** when `type === "file"`:
- Formal slot (entry 1) MUST add `body: <FILE_TYPE_JSON_SCHEMA>` (see [`## file type`](#file-type)) — drives entry-points.json `$ref: "#/definitions/job-attachment"` at packaging
- Companion (entry 2) MUST add `body: <FILE_TYPE_JSON_SCHEMA>` — drives FE picker sub-field navigation (`=vars.<id>.FullName`)
- Bridge (entry 3) unchanged — no `target` on the bridge; the runtime caller has already uploaded the bytes via JobAttachments API before case-start
- `default` MUST stay `""` — FE rejects any other value for file Variables (`InputOutputArgumentsDialog.tsx:148`)

### Out argument

SDD row: `Category=Out`. **Companion is ALWAYS emitted at write time** (per FE convention — `UnifiedBuildCaseDataManager.tsx:298-324` always writes the companion when an Out-arg is created). The BPMN packager's `collapseArgumentCompanions` (`CaseManagementRootConverterUtils.ts:211-237`) may collapse the companion at packaging time, but that's downstream of the skill.

| SDD `Default` | Producer in tasks.md (via task's `->` Outputs row or `=` Updates row) | Runtime behavior |
|---|---|---|
| empty | yes | Producer task fires → writes to `vars.<name>` → caller gets that value at case end. If producer fails to fire, caller gets `""` (the companion's empty default). |
| present | yes | Producer fires → overwrites companion default. If producer skipped, companion default returned. |
| present | no | Companion default always returned at case end. |
| empty | no | **Pure orphan** — Out-arg producer-presence validator AskUserQuestion at end of Phase 3 (see [`io-binding/impl-json.md` § Check 2](../io-binding/impl-json.md)). Author picks: (a) add producer, (b) add Default, (c) recategorize, (d) continue with best-effort emit. |

#### Shape

Same shape regardless of Default presence (two entries):

```json
// 1. variables.outputs[]  — formal Out-arg pointer
{ "id": "<random9>", "name": "finalDecision", "type": "string",
  "var": "finalDecision" }
// var is a POINTER — at case end, engine reads vars.finalDecision via this pointer

// 2. variables.inputOutputs[]  — companion (always written)
{ "id": "finalDecision", "name": "finalDecision", "type": "string",
  "default": "<value or empty string>", "elementId": "root" }
// no custom — argument companions are NOT custom per FE convention
```

**Default + producer precedence at runtime:** if a producer task is declared AND fires, its output value overwrites the companion's default in `vars.<name>`. If the producer task does NOT fire (e.g., skipped by stage entry condition, or stage exited without running it), the companion's default is what gets returned at case end. The runtime resolver does not see "default vs producer" — it sees a single slot whose value is whatever was last written to it; the design-time companion default is the initial value at case start.

### InOut argument

> **NOT supported in v1.** The SDD template's Category enum is `In | Out | Variable` only. If real customer cases require InOut, this section documents the FE-canonical shape for future re-introduction. Skill validators reject `Category=InOut` in v1 (Phase 2 — invalid Category value).

Combines In + Out. One shared companion serves both:

```json
// 1. root.inputs[]  — formal In slot
{ "id": "<random9-in>", "name": "claimId", "type": "string",
  "default": "", "elementId": "<triggerId>" }

// 2. root.inputOutputs[]  — shared companion
{ "id": "claimId", "name": "claimId", "type": "string", "elementId": "<triggerId>" }

// 3. root.outputs[]  — formal Out slot pointing at same companion
{ "id": "<random9-out>", "name": "claimId", "type": "string", "var": "claimId" }

// 4. triggerNode.outputs[]  — bridge from In formal slot to shared companion
{ "name": "claimId", "type": "string", "source": "=vars.<random9-in>", "var": "claimId" }
```

Caller writes value; bridge copies to companion at trigger fire; task body updates `vars.claimId`; case end returns updated value to caller.

## Phase 3 Spec-dependent Validation

These checks need the `trigger-spec-cache.json` to exist (Phase 3 product), so they live here (not in Phase 2 planning). Run during the dispatcher loop.

| Check | Severity | Action |
|---|---|---|
| `sourceField` path doesn't exist in the referenced trigger's `caseShape.outputs[]` (top-level miss OR nested-path walk fails) | ERROR | Halt — sourceField drift. AskUserQuestion at planning time, listing the available spec property keys (e.g., `Title`, `Description`, `Location`, …). User picks the correct field; update SDD's `sourceField` accordingly. **DO NOT** preserve the SDD value with a "runtime fallback" note (e.g., `"if extraction fails, switch source to =response.Title"`) — that defers resolution to runtime where the failure is silent. Resolve at planning. |
| `sourceField` exists but its type doesn't match SDD row's Type | WARNING | Proceed but log to `build-issues.md`. |
| Multi-trigger row's `sourceFields` has a T-number not in `sourceTriggers` (or vice versa) | ERROR | Reject. |

All logged per [`../../logging/impl-json.md`](../../logging/impl-json.md).

> **Phase 2 vs Phase 3 split — what's checked where:**
>
> | Concern | Phase | Reason |
> |---|---|---|
> | Category column missing or empty | Phase 2 (planning) | SDD-only structural check; needs no spec data |
> | `Category=Out` + `sourceTriggers` declared | Phase 2 | Direction mismatch is purely SDD-internal |
> | Same-Name pair (any column mismatch) | Phase 2 | Pure SDD consistency check; not re-validated in Phase 3 |
> | Missing `Type` on In/Out row | Phase 2 | SDD-internal |
> | `sourceTriggers` references nonexistent T-number | Phase 2 | tasks.md cross-reference, no spec needed |
> | `sourceField` path missing in spec (spec drift) | Phase 3 | Needs spec data |
> | Type mismatch SDD vs spec | Phase 3 | Needs spec data |
> | Multi-trigger sourceTriggers/sourceFields T-number mismatch | Phase 3 | Cross-references spec cache for each T-number |
> | Out-arg producer presence | Phase 3 (io-binding validator, end of phase) | Cross-references task outputs, which only exist after task plugins run |
>
> Phase 3 does NOT re-validate the Phase 2 structural checks — they are prerequisite-met by the time Phase 3 runs (Phase 2 rejects before tasks.md is finalized).
>
> **`Category=In` on event triggers is ALLOWED** in v1 (per SDD contract). The previous rejection rule for Category=In on event triggers is removed — the structural emission for In (3-entry: formal slot + companion + bridge) is identical regardless of trigger type. For event triggers, the formal slot's `default` propagates through the bridge to the companion at trigger fire; there's no caller-override path, but the mechanics are valid.

## Custom Outputs (`custom: true` on task.data.outputs[])

Writes a fixed constant to a global variable when a task completes — not from the task's response. Task plugins own this (the task plugin writes `custom: true` on a `task.data.outputs[]` entry). The variables plugin's role is only to ensure the targeted variable is declared in `root.inputOutputs[]` if the custom output's `var` references one that doesn't already exist.

| Field | Standard Output | Custom Output |
|-------|-----------------|---------------|
| `source` | `"=<runtime-path>"` (SDD's left-side string, verbatim) | omitted |
| `value` | mirrors var | `"=<literal>"` or `"=js:<expr>"` |
| `custom` | omitted / `false` | `true` |
| `target` | `"=<varId>"` | omitted |

Custom outputs are an existing task-plugin concept, unchanged by B's redesign. They are the emission shape for SDD `=` rows (set / compute / copy operations per [`../io-binding/planning.md`](../io-binding/planning.md)): when a task's Outputs table contains `caseVar = expression`, the task plugin emits a `custom: true` entry with `var: <caseVar's id>, value: <expression>, source: <same as value>, elementId: "root"`, and NO root mirror is created (per FE's `isUpdateExistingOutput` filter at `VariableMutationUtils.ts:49-64`). The `->` operator handles schema-field extraction and renaming; `=` handles literal / computed / variable-reference writes.

## jsonSchema type

```json
{ "id": "caseData", "name": "caseData", "type": "jsonSchema",
  "body": { "type": "object", "properties": { "status": { "type": "string" } } },
  "_jsonSchema": { "type": "object", "properties": { "status": { "type": "string" } } } }
```

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
  "default": "", "custom": true, "elementId": "root" }
```

## date / datetime types

Primitive — no body, no target. FE renders DatePicker / DateTimePicker based on the type.

```json
{ "id": "submittedOn", "name": "submittedOn", "type": "date",
  "default": "", "custom": true, "elementId": "root" }

{ "id": "lastSeen", "name": "lastSeen", "type": "datetime",
  "default": "=js:new Date().toISOString()", "custom": true, "elementId": "root" }
```

## Expression Syntax

See [`../../../bindings-and-expressions.md`](../../../bindings-and-expressions.md). Key rule: plain reads use `=vars.x`, comparisons use `=js:vars.x === 'val'`. Never use `$vars.x`.

## Task Output → variable resolution

When a task's `data.outputs[]` entry has `id` set (which is always the case under the `->` operator — see task plugin impl-json files for the reassign shape with `originalVar`), the entry self-declares. The variable namespace includes `vars.<id>` directly through the task output entry.

```json
// Task output written by task plugin under `Decision -> finalDecision`:
{ "name": "Decision",                      // schema field display name
  "id": "decision",                         // original camelCase auto-mint (preserved)
  "var": "finalDecision",                   // reassigned to case var's id
  "originalVar": "decision",                // FE reassignment marker — load-bearing
  "source": "=Decision", "target": "=decision",
  "value": "finalDecision",                  // mirrors var
  "type": "string", "elementId": "<stageId>-<taskId>" }
```

This is the **reassign shape** (FE Scenario B/D). The `originalVar` field tells the FE's `mutateRootVariables` to filter this entry out of root-mirroring (`VariableMutationUtils.ts:135`), so the case Variables companion stays intact across FE edits. Without `originalVar`, FE edits would create duplicate root entries and orphan the case variable.

For `=` operator rows (Scenario E), the task plugin emits a separate `custom: true` entry — see Custom Outputs section above.

Per Out-arg companion rule above, the variables plugin ALWAYS writes a `root.inputOutputs[]` companion for Out-args (no longer conditional on Default). For case Variables sourced via `->` from tasks, the companion is also written so the variable is picker-visible at Case Variables panel.

## Connector-Rule Output → variable resolution

Connector condition rules (`rule.uipath.outputs[]`) participate in the case-variable namespace through the same shapes as task outputs — the FE renders the SAME `FPSFormServiceTypeFields` form for both, and `updateRootVariables` is dispatched for rule outputs too (`FPSFormServiceTypeFields.tsx:80`). The variable resolution path is:

- **Extract (`->`)** — rule emits a reassign-shape entry on `rule.uipath.outputs[]` with `originalVar` (load-bearing for `mutateRootVariables` to skip root-mirroring), and Loop B emits the matching `root.inputOutputs[]` companion (`elementId: "root"`, `custom: true`) from the SDD's `Category=Variable` row. The rule's `elementId` on the output entry is `<ownerNodeId>-<ruleId>` (= `<stageId>-<ruleId>` stage-scoped, `root-<ruleId>` case-exit).
- **Assign (`=`)** — rule emits a `custom: true` Scenario E entry on `rule.uipath.outputs[]` with `value: "<expression>"`. No root mirror per `isUpdateExistingOutput` filter. Loop B emits the `Category=Variable` companion unconditionally (per Loop B line 166); only the `default` field is populated, and only when the SDD declares a Default.
- **Bare** (no operator) — rule output is gate-local (named like the spec field, e.g. `response` / `Error`); not a case variable. No companion written.

The dispatcher logic lives in [io-binding/impl-json.md § Output Binding Shapes for Connector Condition Rules](../io-binding/impl-json.md#output-binding-shapes-for-connector-condition-rules) (the 3rd dispatch path, parallel to task dispatch). The condition plugins (`plugins/conditions/*/impl-json.md`) invoke it as the last step of their `wait-for-connector` recipe.

Loop B (this file) handles the COMPANION emission — it scans `tasks.md` Case Variables rows agnostically of producer type. A `Category=Variable` row whose producer is a connector rule's `->` extract gets the same companion shape as one whose producer is a task's `->` extract. The producer (task plugin OR condition plugin) is responsible for writing the upstream `outputs[]` entry referencing the companion via `var: <caseVar.id>`.

> **Skip guard.** Rules with no `uipath.outputs[]` (stub placeholder — connector configuration unresolved) contribute no outputs to the global pool and no companions to Loop B — see [`connector-trigger-common.md § Placeholder fallback`](../../../connector-trigger-common.md#placeholder-fallback).
