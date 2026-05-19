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
| `root.data.uipath.variables.inputOutputs[]` | YES if `id` present | Canonical declaration site |
| `root.data.uipath.variables.inputs[]` | YES — by random `id` | Picker-invisible (Finding #13); target only via the companion |
| `root.data.uipath.variables.outputs[]` | YES (the formal entry) | But its `var` points elsewhere — see Out-arg shape below |
| `task.data.outputs[]` | YES if `id` present | Self-declares — task plugin writes id matching the SDD-given name |
| `task.data.inputs[]` | YES — by random `id` | Picker-invisible; used for the In-arg formal slot |
| `triggerNode.data.uipath.outputs[]` | YES if `id` present; **NO if only `var` (no `id`)** | Pattern A entries (`id === var`) self-resolve; Pattern C entries (`var` only) require a companion in `root.inputOutputs[]` |

**"Companion" = the paired `inputOutputs[]` entry whose `id` matches the lookup name.** Required for trigger outputs that lack `id`; load-bearing for Out-args with a `Default` value; optional when the producer (task output) already self-declares.

## Scope of this plugin

Under the B refactor, this plugin is **the sole owner** of:

| Array | Owns? |
|---|---|
| `root.data.uipath.variables.inputs[]` | Yes |
| `root.data.uipath.variables.outputs[]` | Yes |
| `root.data.uipath.variables.inputOutputs[]` | Yes |
| `triggerNode.data.uipath.outputs[]` | **Yes** — sole owner under B (was co-mutated with trigger plugin in previous design) |
| `task.data.outputs[]` | No — task plugins self-declare; this plugin's writes never touch them |
| `task.data.inputs[].value` | No — io-binding owns this |
| `root.bindings[]` | No — connector / trigger plugins own resource bindings |

## Target Paths

Read `Schema:` header from `tasks.md` per Rule 18. Trigger output mappings are identical across schemas (node internals untouched by v20).

### v19

| What | JSON path |
|---|---|
| In argument inputs | `root.data.uipath.variables.inputs[]` |
| Out argument outputs | `root.data.uipath.variables.outputs[]` |
| All internal variables | `root.data.uipath.variables.inputOutputs[]` |
| Trigger output mappings | `nodes[<triggerIndex>].data.uipath.outputs[]` |

### v20

| What | JSON path |
|---|---|
| In argument inputs | `variables.inputs[]` *(top level)* |
| Out argument outputs | `variables.outputs[]` *(top level)* |
| All internal variables | `variables.inputOutputs[]` *(top level)* |
| Trigger output mappings | `nodes[<triggerIndex>].data.uipath.outputs[]` *(unchanged from v19)* |

> v20 hoists `root.data.uipath.variables` to top-level `variables`. Field shape inside is identical — only the destination path changes.

## Uniqueness Rule

Every `var` / `id` must be globally unique across the case. When a name collides, append a counter starting at 2:

```
"decision" exists → "decision2" → "decision3"
"error" + "error2" exist → "error3"
```

The `source` and `name` fields keep the original value — only `var` / `id` / `target` get the suffix.

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
| Not referenced by SDD | (no row) | `{name: <spec.name>, var: <spec.name>, id: <spec.name>, type: <spec.type>, source: <spec.source>, elementId: <triggerId>}` — `type` and `source` come from the spec entry verbatim (e.g., `type: "jsonSchema"` + `source: "=response"`); do NOT synthesize a path. Plain-name auto-emit per Q5/Alt 1. | — | — | **Required** — `{id: <spec.name>, name: <spec.name>, type: <spec.type>, elementId: <triggerId>, body: <spec.body>}`. For `jsonSchema`-typed entries (e.g., `response`, `Error`), the companion holds the full body schema that the FE picker uses to discover sub-fields. Without it, sub-field picking is broken and the variable can't be selected in connector-task input bindings. |
| Referenced as `Category=Variable` | row's `sourceField` path | `{name: <sdd-name>, var: <sdd-name>, id: <sdd-name>, type: <sdd-row.type>, source: "=<row.sourceField>", elementId: <triggerId>}` (Pattern C with id present for self-resolution; `source` is `=` prepended to the raw `sourceField` value from tasks.md; `type` comes from the SDD row, NOT the spec — author's chosen type wins) | — | — | `{id: <sdd-name>, name: <sdd-name>, type: <sdd-row.type>, elementId: "root"}` — companion with elementId="root" routes variable to Case Variables panel (per audit Finding #6). |
| Referenced as `Category=In` | (only valid for manual/timer triggers — see § In-arg below) | **REJECT for event triggers** (audit Finding #6 misclassification — recategorize to Variable) | — | — | — |
| Referenced as `Category=Out` | — | **REJECT** (direction mismatch — Out-args flow case→caller) | — | — | — |

**Dedup rule:** if multiple SDD rows reference the same trigger spec output (rare, but possible across multi-trigger cases), each writes its own `triggerNode.outputs[]` entry but they share one `root.inputOutputs[]` declaration (first-write-wins on type / default; Phase 2 validator rejects conflicts).

**Variant A semantics (per Q6a):** matching is by **top-level spec output name only** (i.e., the `name` field of an entry in `caseShape.outputs[]` — `response`, `Error`, etc.). When an SDD row's Name equals the top-level spec name, the SDD-named entry **replaces** the would-be plain-name auto-emit for that exact entry; do not write both.

**Name matching is case-sensitive.** Preserve the spec's name verbatim in the emitted `name`/`var`/`id` fields. Connector specs typically return PascalCase top-level keys (`response`, `Error`, `Title`); SDDs may use camelCase. If an SDD row's Name is `subject` and the spec returns `Subject`, **the match does NOT fire** — they are different identifiers per the runtime resolver (`VariablesService.findVariableByVariableId` performs direct case-sensitive string equality). To match, the SDD Name must equal the spec's name byte-for-byte. The skill never re-cases or aliases.

**Sub-field references DO NOT trigger replacement.** When SDD references a sub-field path (e.g., `sourceField: response.Title`), the Pattern C entry is in ADDITION to — not in place of — the top-level `response` auto-emit. Worked example for SDD `calendarTitle ← response.Title` (Variable, type=string) on a trigger whose spec returns two top-level `jsonSchema` outputs `response` and `Error`:

```jsonc
triggerNode.outputs[]: [
  { name: "Title",    var: "calendarTitle", id: "calendarTitle", type: "string",     source: "=response.Title", elementId: "<triggerId>" },  // Pattern C — SDD
  { name: "response", var: "response",      id: "response",      type: "jsonSchema", source: "=response",       elementId: "<triggerId>" },  // auto-emit — coexists
  { name: "Error",    var: "Error",         id: "Error",         type: "jsonSchema", source: "=Error",          elementId: "<triggerId>" }   // auto-emit — unreferenced
]

root.inputOutputs[]: [
  { id: "calendarTitle", name: "calendarTitle", type: "string",     elementId: "root" },                    // Pattern C companion → Case Variables panel
  { id: "response",      name: "response",      type: "jsonSchema", elementId: "<triggerId>", body: <full schema from spec> },  // auto-emit companion (REQUIRED — body drives sub-field picker)
  { id: "Error",         name: "Error",         type: "jsonSchema", elementId: "<triggerId>", body: <error schema from spec> }
]
```

Six entries total: 3 trigger outputs + 3 companions. The auto-emit companions carry the full body schemas so the FE picker can navigate sub-fields. The Pattern C companion has no body (its type is the primitive `string`).

### Loop B — SDD-only rows (rows with no trigger source)

For each variable T-entry in `tasks.md` that has **no `sourceTrigger` / `sourceTriggers` field**:

| SDD row | `root.inputs[]` | `root.outputs[]` | `root.inputOutputs[]` |
|---|---|---|---|
| `Category=Variable` (pure state, no trigger) | — | — | `{id: <sdd-name>, name: <sdd-name>, type: <type>, elementId: "root", default: <value if Default set>, custom: true}` |
| `Category=In` for manual/timer trigger (sourceTrigger is the trigger T-number; no `sourceField`) | `{id: <random9>, name: <sdd-name>, type: <type>, default: <value>, elementId: <triggerId>}` | — | `{id: <sdd-name>, name: <sdd-name>, type: <type>, elementId: <triggerId>}`. Additionally write the **bridge** on `triggerNode.outputs[]` (see § In argument below). |
| `Category=Out`, **no Default** | — | `{id: <random9>, name: <sdd-name>, type: <type>, var: <sdd-name>}` (formal-arg pointer) | — (omitted — producer task's `id` self-declares; see § Out argument) |
| `Category=Out`, **with Default** | — | `{id: <random9>, name: <sdd-name>, type: <type>, var: <sdd-name>}` | `{id: <sdd-name>, name: <sdd-name>, type: <type>, default: <value>, elementId: "root"}` |
| `Category=InOut` | (entries per § InOut argument below) | (entries per § InOut argument below) | (shared companion per § InOut) |

> Loop A and Loop B can write the SAME `root.inputOutputs[]` entry when an SDD row appears in both contexts (e.g., a `Category=Variable` row with `sourceTrigger`). Apply dedup by `id`: if an entry with the same `id` already exists from Loop A, do not re-write in Loop B; Phase 2 validator has already confirmed there's no Type/Default conflict.

## Pattern shapes by category

### Pure state Variable (no trigger source)

SDD row: `Category=Variable`, no `sourceTriggers`, optional `Default`.

```json
// root.data.uipath.variables.inputOutputs[]
{ "id": "caseStatus", "name": "caseStatus", "type": "string",
  "custom": true, "elementId": "root", "default": "Open" }
```

No trigger.outputs[] write, no root.inputs[] / outputs[] writes.

### Trigger-sourced Variable (Pattern C)

SDD row: `Category=Variable`, `sourceTriggers: T02`, `sourceFields: response.subject`.

```json
// triggerNode.data.uipath.outputs[]  (the trigger plugin's caseplan node — written by THIS plugin under B)
{ "name": "subject", "var": "calendarTitle", "id": "calendarTitle",
  "source": "=response.subject", "type": "string", "elementId": "<triggerId>" }

// root.data.uipath.variables.inputOutputs[]
{ "id": "calendarTitle", "name": "calendarTitle", "type": "string",
  "elementId": "root" }
```

`elementId: "root"` on the root companion places the variable under FE's Case Variables panel (correct semantics — it's case state, not a formal trigger argument).

### Trigger-sourced Variable — multi-trigger

SDD row: `Category=Variable`, `sourceTriggers: T02, T03`, `sourceFields: T02: response.user; T03: response.initiator`.

Write TWO `triggerNode.outputs[]` entries (one per trigger node) + ONE shared `root.inputOutputs[]` companion:

```json
// On trigger_T02's node:
{ "name": "caseStarter", "var": "caseStarter", "id": "caseStarter",
  "source": "=response.user", "type": "string", "elementId": "<triggerId-T02>" }

// On trigger_T03's node:
{ "name": "caseStarter", "var": "caseStarter", "id": "caseStarter",
  "source": "=response.initiator", "type": "string", "elementId": "<triggerId-T03>" }

// root.inputOutputs[] — single companion
{ "id": "caseStarter", "name": "caseStarter", "type": "string", "elementId": "root" }
```

Resolver doesn't care that two trigger entries write to the same `vars.caseStarter` slot — last writer wins, and only one trigger fires per case lifecycle. The companion is the canonical declaration.

### In argument (manual / timer triggers ONLY)

SDD row: `Category=In`, `triggerRef: T02` where T02 is a manual or timer trigger.

Three entries — formal slot + companion + bridge:

```json
// 1. root.inputs[]  — formal-arg slot (caller writes here)
{ "id": "<random9>", "name": "applicantName", "type": "string",
  "default": "", "elementId": "<triggerId>" }

// 2. root.inputOutputs[]  — companion (readable as =vars.applicantName)
{ "id": "applicantName", "name": "applicantName", "type": "string",
  "elementId": "<triggerId>" }

// 3. triggerNode.data.uipath.outputs[]  — bridge from formal slot to companion
{ "name": "applicantName", "source": "=vars.<random9>", "var": "applicantName" }
```

**Why three entries instead of one?** The runtime resolver (`VariablesService.findVariableByVariableId`) is a single string-equality find on `Variable.id`. The caller writes the formal-arg's value into `vars.<random9>` at trigger fire (because `inputs[].id` is `<random9>`); downstream code wants to read it as `=vars.applicantName` (because that's the readable name). There is no automatic forwarding between the two slots — the bridge entry on `triggerNode.outputs[]` executes the copy at fire time: `source: "=vars.<random9>"` reads the formal slot, `var: "applicantName"` writes to the companion's slot. Without the bridge, `=vars.applicantName` resolves to undefined. The companion's `inputOutputs[]` entry alone declares the *name* in the namespace, but holds no *value* because nobody writes to it. See knowledge doc § 6 for the FE source evidence.

> **Event triggers DO NOT use this pattern.** They use Pattern C (trigger-sourced Variable above). Audit Finding #6: event-trigger payload is not caller-supplied, so it's not a formal In argument.

> **Placeholder trigger interaction:** if the producing manual / timer trigger is a placeholder, write entries 1 + 2 only; skip the bridge (entry 3) — the placeholder has no `data.uipath.outputs` array. The placeholder trigger never fires, so the bridge would never execute anyway. **Consequence:** at runtime `vars.<name>` (the companion slot) is undefined — the `default` on the `inputs[]` formal slot does NOT propagate to the companion without the bridge. This is expected: a placeholder case is structurally incomplete and not meant to run until the trigger is resolved. Re-generate from scratch (Rule 6) after the trigger resolves to get the working bridge.

### Out argument

SDD row: `Category=Out`. Three cases.

#### Q10b — Conditional companion emission

The companion (`root.inputOutputs[]` entry for the Out-arg's `var`) is **conditional** on whether a `Default` value is declared:

| SDD `Default` | Producer task output declared in tasks.md | Companion emitted? | Runtime source |
|---|---|---|---|
| empty | yes | **No** (Q10b: omit) | Task output's `id` self-declares; resolver matches `var` to task output |
| present | yes | **Yes** with `default` | Task fire → value overwrites; task not fire → companion default returned |
| present | no | **Yes** with `default` | Companion default returned (no producer to overwrite) |
| empty | no | **No companion** | Pure orphan — Q10 II validator AskUserQuestion (see [`io-binding/impl-json.md` § Check 2](../io-binding/impl-json.md)) |

**Why omit when no Default and producer exists:** the producer task's `task.data.outputs[].id` IS the variable slot (self-declares). Adding a `root.inputOutputs[]` companion with no default would be redundant and could conflict with the task's own write at runtime.

#### Shapes

**Case 1 — No `Default`, producer present (Q10b: companion omitted):**

```json
// root.data.uipath.variables.outputs[]  — formal Out-arg entry
{ "id": "<random9>", "name": "finalDecision", "type": "string",
  "var": "finalDecision" }
// var is a POINTER — at case end, engine reads vars.finalDecision via this pointer
```

No `root.inputOutputs[]` companion. The io-binding validator (Phase 3 Step 12) confirms a task output exists with matching `id`.

**Case 2 — `Default` present (companion required, ± producer):**

```json
// 1. root.data.uipath.variables.outputs[]  — formal Out-arg entry (same as above)
{ "id": "<random9>", "name": "finalDecision", "type": "string", "var": "finalDecision" }

// 2. root.data.uipath.variables.inputOutputs[]  — companion holds the default
{ "id": "finalDecision", "name": "finalDecision", "type": "string",
  "default": "Pending", "elementId": "root" }
```

The companion's `default` is the fallback returned if no task writes to `vars.finalDecision` (e.g., the producing stage was skipped via entry condition, OR the case has no producer task declared at all).

**Default + producer precedence at runtime:** if a producer task is declared AND fires, its output value overwrites the companion's default in `vars.<name>`. If the producer task does NOT fire (e.g., skipped by stage entry condition, or stage exited without running it), the companion's default is what gets returned at case end. The runtime resolver does not see "default vs producer" — it sees a single slot whose value is whatever was last written to it; the design-time companion default is the initial value at case start.

### InOut argument

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
{ "name": "claimId", "source": "=vars.<random9-in>", "var": "claimId" }
```

Caller writes value; bridge copies to companion at trigger fire; task body updates `vars.claimId`; case end returns updated value to caller.

## Phase 3 Spec-dependent Validation

These checks need the `trigger-spec-cache.json` to exist (Phase 3 product), so they live here (not in Phase 2 planning). Run during the dispatcher loop.

| Check | Severity | Action |
|---|---|---|
| `Category=In` row references a spec output of an **event** trigger | ERROR | Reject — audit Finding #6 misclassification. AskUserQuestion: recategorize as Variable. |
| `sourceField` path doesn't exist in the referenced trigger's `caseShape.outputs[]` (top-level miss OR nested-path walk fails) | ERROR | Halt — audit Finding #5 drift. AskUserQuestion at planning time, listing the available spec property keys (e.g., `Title`, `Description`, `Location`, …). User picks the correct field; update SDD's `sourceField` accordingly. **DO NOT** preserve the SDD value with a "runtime fallback" note (e.g., `"if extraction fails, switch source to =response.Title"`) — that defers resolution to runtime where the failure is silent (audit Finding #1). Resolve at planning. |
| `sourceField` exists but its type doesn't match SDD row's Type | WARNING | Proceed but log to `build-issues.md`. |
| Multi-trigger row's `sourceFields` has a T-number not in `sourceTriggers` (or vice versa) | ERROR | Reject (Q9 strict). |

All logged per [`../../logging/impl-json.md`](../../logging/impl-json.md).

> **Phase 2 vs Phase 3 split — what's checked where:**
>
> | Concern | Phase | Reason |
> |---|---|---|
> | Category column missing or empty | Phase 2 (planning) | SDD-only structural check; needs no spec data |
> | `Category=Out` + `sourceTriggers` declared | Phase 2 | Direction mismatch is purely SDD-internal |
> | Type / Default conflict across rows sharing same Name | Phase 2 | Pure SDD consistency check; not re-validated in Phase 3 |
> | Missing `Type` on In/Out row | Phase 2 | SDD-internal |
> | `sourceTriggers` references nonexistent T-number | Phase 2 | tasks.md cross-reference, no spec needed |
> | `Category=In` + event-trigger source (Finding #6) | Phase 3 | Needs spec cache to confirm the trigger is event-typed and the row references a real spec output |
> | `sourceField` path missing in spec (Finding #5 drift) | Phase 3 | Needs spec data |
> | Type mismatch SDD vs spec | Phase 3 | Needs spec data |
> | Multi-trigger sourceTriggers/sourceFields T-number mismatch | Phase 3 | Cross-references spec cache for each T-number |
> | Out-arg producer presence | Phase 3 (io-binding validator, end of phase) | Cross-references task outputs, which only exist after task plugins run |
>
> Phase 3 does NOT re-validate the Phase 2 structural checks — they are prerequisite-met by the time Phase 3 runs (Phase 2 rejects before tasks.md is finalized).

## Custom Outputs (`custom: true` on task.data.outputs[])

Writes a fixed constant to a global variable when a task completes — not from the task's response. Task plugins own this (the task plugin writes `custom: true` on a `task.data.outputs[]` entry). The variables plugin's role is only to ensure the targeted variable is declared in `root.inputOutputs[]` if the custom output's `var` references one that doesn't already exist.

| Field | Standard Output | Custom Output |
|-------|-----------------|---------------|
| `source` | `"=<schema-field>"` | omitted |
| `value` | mirrors var | `"=<literal>"` or `"=js:<expr>"` |
| `custom` | omitted / `false` | `true` |
| `target` | `"=<varId>"` | omitted |

Custom outputs are an existing task-plugin concept, unchanged by B's redesign. They are a workaround for use cases that don't fit the schema-extraction model (literal constants, computed expressions). The new `<-` aliasing notation (per [`../io-binding/planning.md`](../io-binding/planning.md)) handles schema field renames and nested-field extraction; custom outputs are for things schema extraction can't do.

## jsonSchema type

```json
{ "id": "caseData", "name": "caseData", "type": "jsonSchema",
  "body": { "type": "object", "properties": { "status": { "type": "string" } } },
  "_jsonSchema": { "type": "object", "properties": { "status": { "type": "string" } } } }
```

## Expression Syntax

See [`../../../bindings-and-expressions.md`](../../../bindings-and-expressions.md). Key rule: plain reads use `=vars.x`, comparisons use `=js:vars.x === 'val'`. Never use `$vars.x`.

## Task Output → variable resolution (no companion needed when id present)

When a task's `data.outputs[]` entry has `id` set (which is always the case under the `<-` aliasing — see task plugin impl-json files), the entry **self-declares**. The variable namespace includes `vars.<id>` directly; no `root.inputOutputs[]` companion is required for resolution.

```json
// Task output written by task plugin (e.g., agent/impl-json.md):
{ "name": "Decision", "var": "finalDecision", "id": "finalDecision",
  "source": "=Decision", "target": "=finalDecision", "value": "finalDecision",
  "type": "string", "elementId": "<stageId>-<taskId>" }
```

Downstream `=vars.finalDecision` resolves directly against this entry's `id`. The variables plugin does NOT write a `root.inputOutputs[]` companion for task outputs by default — audit Finding #2 confirms it's safe to omit when `id` is present.

The exception is when an Out-arg with `Default` declares the slot to provide a fallback value when the producing task is skipped — then variables plugin writes the companion to hold the default (see § Out argument with Default above).
