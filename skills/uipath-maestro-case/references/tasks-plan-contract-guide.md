# `tasks.md` Plan Contract

> **Load condition:** Read this guide only when Phase 1 reaches Step 4, after discovery and resource resolution, and before the first `tasks.md` write.

## Contents

- [§4.0 Completeness principle](#40-completeness-principle-no-omissions)
- [§4.0a Section-batched write contract](#40a--section-batched-write-contract-mandatory)
- [§4.1 Task ordering](#41-task-ordering)
- [§4.2 Create case file](#42-create-case-file-t01)
- [§4.2.1 Declare global variables and arguments](#421-declare-global-variables-and-arguments)
- [§4.3 Configure triggers](#43-configure-triggers-t02)
- [§4.4 Create stages](#44-create-stages)
- [§4.5 Edges — not authored](#45-edges--not-authored-retired)
- [§4.6 Add tasks](#46-add-tasks)
- [§4.7 Configure conditions](#47-configure-conditions)
- [§4.8 Set SLA and escalation rules](#48-set-sla-and-escalation-rules)
- [§4.9 Not Covered](#49-not-covered-section)

Cross-reference: [case-schema.md](case-schema.md) for JSON shape, [bindings-and-expressions.md](bindings-and-expressions.md) for inputs/outputs wiring.

Field names use plain identifiers (e.g., `type:`, `displayName:`, `lane:`), not CLI flag syntax.

### 4.0 Completeness principle (no omissions)

Every declaration in `sdd.md` must become a T-task in `tasks.md`. Mapping is 1-to-1:

- **Never filter** declarations on the grounds that the default rule-type, default field value, or "implicit behavior" would cover them. If `sdd.md` lists a task, stage, trigger, condition, SLA row, **variable, or argument**, `tasks.md` emits a T-task for it — regardless of rule-type (`current-stage-entered`, `case-entered`, `exit-only`, `required-tasks-completed`, etc.).
- **Never merge** two sdd.md items into one T-task "because they're similar."
- **Never drop** defaults-looking items (e.g., `is-interrupting: false`, `runOnlyOnce: true`, `marks-stage-complete: true`). The explicit declaration is the signal — honor it.
- **Never drop design rationale.** Copy each SDD stage/task/SLA `Design Rationale` into `rationale:` on its matching T-entry. Condition T-entries copy the rationale for the routing/activation choice they implement. Rationale is reviewer/audit context; the execution plugin ignores it when composing JSON.
- **When in doubt, emit.** It is always correct to create a T-task that mirrors an sdd.md row. It is never correct to silently omit one.
- **When format is ambiguous or unrecognized, ASK — do not skip.** If a row exists but you cannot determine the right plugin, category, or T-entry shape (e.g., trigger "Initial Variable Mapping" uses an aggregate phrase instead of explicit per-field mappings; a variable's category — In / Out / Variable — is unclear; a task type does not match the closed enum), invoke **AskUserQuestion** with the row content + the specific ambiguity + bounded options. Silent omission is a defect. This obligation applies to every sdd.md declaration class above, including variables and arguments.

Before finalizing `tasks.md` at Step 5, run a completeness cross-check: for every declared stage / task / trigger / condition / SLA row **and every Case Variables table row (one T-entry each, per §4.2.1)** in sdd.md, verify a corresponding T-task exists. Gaps are a defect — fix before proceeding to Phase 2.

**Cross-check inventory.** Before proceeding to Phase 2, count and report each class:

| Class | Source in sdd.md | T-entry section |
|---|---|---|
| Case file | Case Metadata | §4.2 (T01) |
| Triggers | Case Triggers | §4.3 (T02+) |
| Variables / arguments | Case Variables | §4.2.1 (after last trigger) |
| Stages | Section 2 stage headings | §4.4 |
| Tasks | Per-stage Tasks tables | §4.6 |
| Conditions | Stage Entry / Stage Exit / Task Entry / Case Exit tables | §4.7 |
| SLA | Case-Level SLA + per-stage Stage SLA + per-action Task SLA | §4.8 |

Counts that don't match the sdd.md → fix before Step 5 (before proceeding to Phase 2).

### 4.0a — Section-batched write contract (mandatory)

**Per-section batching.** Build `tasks.md` one section at a time — never compose the full body in memory and Write once, but do not pay a Read between sibling T-entries inside a section either.

Procedure:

1. **Seed.** Write `tasks.md` with a `## Inventory` placeholder section only. Single Write.
2. **Per section.** Sections are §4.2.1 vars → §4.3 triggers → §4.4 stages → §4.6 tasks → §4.7 conditions → §4.8 SLA. For each section:
   - **One Read** of `tasks.md` at section entry.
   - **N Edit-appends** in sequence, one per T-entry in the section. Skip the re-Read between sibling Edits — Edit's tool result confirms applied state in context.
   - TaskUpdate marks each T-entry `in_progress` → `completed` as it goes — that is the per-T-entry audit trail, not the file diff.
3. **Inventory finalize.** After last T-entry, Edit the inventory section with class-by-class counts (per §4.0 cross-check table).
4. **`registry-resolved.json`.** Same section-batched discipline — one Read per section, N Edit-appends, no re-Read between siblings.

**T-entry heading contract.** Every declaration is its own level-two heading in the exact form `## T<n>: <action>`. Do not use level-three-or-deeper headings for T-entries, and do not nest a task beneath a stage's T-entry. A task heading must quote its display name, for example `## T08: Add wait-for-timer task "First Step" to "Process"`. This keeps the plan independently addressable by Phase 2 and by plan validators.

Why: section-batched round-trips keep tool-call transcript reviewable, preserve rollback granularity at section boundary, allow mid-run interruption recovery via re-Read + resume from next un-applied T-entry, and surface omissions before they propagate — without paying a per-T-entry Read tax that inflates inference latency by ~5s per turn.

**Hard cap on tasks.md write size.** After the §4.0a Step 1 Seed Write (Inventory placeholder, <1KB), the only legal mutation of `tasks.md` is **Edit-append** per the section-batched contract above. A single Write replacing the whole `tasks.md` is **forbidden** regardless of size. A single Edit-append payload >30KB is also forbidden — split into per-section Edit-appends even when consecutive Edits would total >30KB combined. Rationale: a single 96KB Write of tasks.md emits ~40K output tokens in one turn = ~360s inference latency = ~20% of total session in one tool call. Section-batched Edit-appends spread that cost across ~7 turns of ~50s each, recovers reviewability, and matches the recovery contract (re-Read + resume from next un-applied T-entry).

**Recovery on interruption:** re-Read `tasks.md`, scan for next un-applied T-entry (the audit trail in TaskUpdate identifies it), resume from there. No sidecar checkpoint file.

This contract mirrors Phase 3's per-section JSON-write contract (see [implementation.md § Per-plugin execution](implementation.md)).

### 4.1 Task ordering

Always in this order: stages → tasks → conditions → SLA.

The task **title IS the action description** — do not add a redundant `what` or `type` field. Absorb type into the title (e.g., `Add api-workflow task "..."` not `Add task` + `type: api-workflow`).

### 4.2 Create case file (T01)

Title format: `Create case file "<name>"`

Consult [`plugins/case/planning.md`](plugins/case/planning.md) for required fields (name, file path, case-identifier, identifier-type, case-app-enabled, description). Source all fields from sdd.md.

When `identifier-type: external`, `case-identifier` carries the sdd.md expression verbatim (`=vars.<varId>` or `=js:…`); any `=vars.<varId>` it references must be a variable declared in §4.2.1 (an **In** argument or **Variable**). See [`plugins/case/planning.md` § External identifier value](plugins/case/planning.md).

### 4.2.1 Declare global variables and arguments

Title format: `Declare <category> "<name>"` where category is `In argument`, `Out argument`, or `variable`.

One T-entry per variable or argument from the sdd.md "Case Variables" table. Place these after the case file (T01) and **all** trigger T-entries (T02+) — i.e., after the last trigger row, before stages. In multi-trigger cases the variables block starts at `T0<last-trigger>+1`, not at `T03`. Consult [`plugins/variables/global-vars/planning.md`](plugins/variables/global-vars/planning.md) for the SDD-to-category mapping rules and entry format.

### 4.3 Configure trigger(s) (T02+)

Title format: `Configure <trigger-type> trigger "<name>"`

Consult the corresponding trigger plugin (`plugins/triggers/<type>/planning.md`) for required fields.

**One T-entry per trigger row in sdd.md.** A case with N entry-point rows in its triggers table emits N trigger T-entries (T02, T03, …) — even when several rows would resolve to `<UNRESOLVED>` because the IS connection isn't provisioned. Per §4.0, "value can't be resolved yet" is not a reason to omit a row; it's a reason to mark `<UNRESOLVED: …>` and continue. Regardless of how many triggers a case has, no per-trigger edge is created (Rule 20; §4.5) — the case starts at the first stage's `case-entered` entry condition whenever any trigger fires.

Each trigger row uses its plugin's full field set — see `plugins/triggers/<type>/planning.md` for the per-type entry format. Worked example — sdd.md declares 3 entry-point rows (one manual + two events), one of which is unresolved:

```markdown
## T02: Configure manual trigger "Operator Starts Case"
- display-name: "Operator Starts Case"
- description: "Operator kicks off a case from the portal"
- order: after T01
- verify: Confirm node appended; capture TriggerId

## T03: Configure event trigger "New Inbound Email"
- type-id: <uiPathActivityTypeId>
- connection-id: <connection-uuid>
- connector-key: uipath-microsoft-office-365-outlook
- object-name: Email
- event-operation: created
- event-mode: webhooks
- input-values: {"parentFolderId": "AAMkADNm..."}
- filter: "(contains(subject, 'urgent'))"
- order: after T02
- verify: Confirm trigger configured with correct event parameters

## T04: Configure event trigger "Jira Issue Created"
- type-id: <UNRESOLVED: no IS connection for uipath-atlassian-jira>
- connection-id: <UNRESOLVED>
- connector-key: <UNRESOLVED>
- object-name: <UNRESOLVED>
- event-operation: <UNRESOLVED>
- event-mode: <UNRESOLVED>
- order: after T03
- verify: trigger skipped at execution; user attaches after registering connection
```

Do **not** collapse the unresolved trigger into a note on T02 or omit it entirely — execution behavior for unresolved event triggers is documented in [`triggers/event/planning.md § Unresolved Fallback`](plugins/triggers/event/planning.md#unresolved-fallback), but the planning row is still required.

### 4.4 Create stages

Title format: `Create stage "<name>"` or `Create secondary stage "<name>"`

One task per stage. Consult [`plugins/stages/planning.md`](plugins/stages/planning.md) for required fields and the `stage` vs `secondary` decision. Basic properties only — SLA and escalation come later (§4.7).

Every stage T-entry includes `rationale:` copied from the SDD. It must explain the stage-kind decision and routing shape, especially when one interrupting secondary-stage entry handles a global event.

### 4.5 Edges — not authored (RETIRED)

The skill does not author edges (Rule 20). Emit no edge T-entries. Stage transitions derive entirely from stage entry/exit conditions (§4.7); `caseplan.json.edges` stays `[]`; case start is the first stage's `case-entered` entry condition. See the reachability check in [`sdd-generation-rules.md`](sdd-generation-rules.md).

### 4.6 Add tasks

Title format: `Add <type> task "<name>" to "<stage>"`

One task per task from the sdd.md — do NOT group multiple tasks under a single T-number. Read both the task-type plugin (`plugins/tasks/<type>/planning.md`) and the shared I/O-binding plugin (`plugins/variables/io-binding/planning.md`) before writing the entry. The task plugin owns resource-specific fields; the I/O-binding plugin is the single source of truth for the common output-row grammar.

Every task entry includes at least:

- **taskTypeId** — resolved from the registry in Step 3
- **rationale** — copied from the SDD; explains the task-type and activation/sequencing choice
- **activation-mode** — required on every task. One of `sequential`, `parallel`, `parallel-after-predecessor`, `event-triggered`, `adhoc`, `fan-in`, or `conditional-gate`. This is the user-visible task mode decision, not layout state.
- **entry-rule** — required on every task; mirrors the planned task-entry condition rule. Sequential tasks MUST say `runs-sequentially`, event-triggered tasks normally say `wait-for-connector`, adhoc tasks say `adhoc`, parallel stage-start tasks say `current-stage-entered`, parallel siblings after an immediate predecessor say `runs-sequentially`, and fan-in / non-immediate gates say `selected-tasks-completed`.
- **inputs** / **outputs** — see [bindings-and-expressions.md](bindings-and-expressions.md) for the two input modes (literal/expression and cross-task reference)
- **runOnlyOnce** — from sdd.md (default `false` if not specified). Phase 0-generated SDDs should always state `Run Only Once: Yes/No`; when a user-authored SDD omits it, use the frontend/default-new-task behavior (`false`) and do not infer `true` from task type.
- **isRequired** — from sdd.md (default `true` if not specified)
- **order** — authoring order in `tasks.md` (`after T05`, etc.). It is not allowed to carry execution semantics by itself; execution is carried by `activation-mode` + `entry-rule`.
- **lane** — integer task-set index, default increments per task within the stage starting at 0 for structural/layout compatibility. Lane does not express sequencing by itself; it controls the inner `data.tasks[lane][]` grouping only after `activation-mode` and `entry-rule` are decided. For a strict sequential chain, use consecutive single-task lanes (`[[A], [B], [C]]`) and never reuse a lane. Reuse a lane only for explicit sibling grouping: independent stage-start siblings use `parallel` + `current-stage-entered`; siblings after the same immediate predecessor use `parallel-after-predecessor` + `runs-sequentially` and share that same next lane (`[[A], [B, C], [D]]`). The rationale must explain why the siblings run together.
- **verify** — what the execution phase should check after running

Additional fields are plugin-specific; read the plugin's `planning.md` before filling the entry.

Preserve every SDD Inputs row with its declared binding mode and value. A JSON object literal stays literal through both handoffs: record the exact JSON in `tasks.md`, then write either the native object or its JSON-encoded string to `input.value`; never add `=js:` or `=jsonString:` unless the SDD itself explicitly uses that prefix.

> **Activation-mode audit before writing §4.7.** After §4.6 is drafted and before any condition T-entry is written, scan every stage's task list and make the task mode visible in the plan:
>
> **Authority order:** an explicit rule in the supplied/approved SDD wins. This audit verifies the handoff; it does not redesign or normalize authored rules. Use the derivation matrix below only when authoring from source behavior that has no explicit task-entry rule.
>
> Task type says **what** a task does; `activation-mode` and `entry-rule` say **when** it starts. A task type never supplies its activation semantics.
>
> | activation-mode | entry-rule / rule-type | Required grouping or selector contract |
> |---|---|---|
> | `sequential` | `runs-sequentially` | A strict chain uses consecutive single-task lanes. |
> | `parallel` | `current-stage-entered` | Independent stage-start siblings may share one lane. |
> | `parallel-after-predecessor` | `runs-sequentially` | Siblings after the same immediate predecessor share the same next lane/task set. |
> | `event-triggered` | The explicitly authored event/condition rule, normally `wait-for-connector` | Preserve the authored event configuration; do not infer this mode from task type. |
> | `adhoc` | `adhoc` | Set `isRequired: false`; the user launches the task. |
> | `fan-in` | `selected-tasks-completed` | Preserve the authored selected tasks and convergence rationale. |
> | `conditional-gate` | The explicitly authored gate rule | Preserve every authored selector and gate expression. |
>
> `runs-sequentially` is a task entry rule, not a stage flag and not a lane marker. When the requirement says `then`, `after`, `before`, `in order`, or otherwise declares a dependency/order, preserve the ordered task-set structure in `data.tasks` and write one `entryConditions` entry containing only `rules: [[{ "rule": "runs-sequentially" }]]` for every task in that ordered run. The first task set's rule means current-stage-entered; each later task set's rule means the preceding task set completed. Do not let the absence of a data binding turn an explicitly ordered run into parallel stage-start tasks. Do not add `current-stage-entered` alongside the sequential rule. Use parallel `current-stage-entered` tasks only for independent stage-start work; add `selected-tasks-completed` fan-in only when downstream work requires all branches.
>
> `manually-triggered` / `adhoc` → one `adhoc` entry rule, `isRequired: false`, started by a user from the Case App, with no additional entry events. `adhoc` is an activation mode, not a task type; a manually triggered task can still be `action`, `agent`, `api-workflow`, `process`, etc. Never model an adhoc task as event-triggered or sequential, and never add `adhoc` to a stage-entry condition.
>
> While authoring a new SDD, do not invent `selected-tasks-completed` merely because a task follows the immediately previous task; model a plain contiguous run as `runs-sequentially`. Once an SDD is supplied or approved, however, preserve every explicit `selected-tasks-completed` row and selector in `tasks.md` and `caseplan.json`; planning is not a second design pass. Map that task to `conditional-gate` or `fan-in` as its authored rationale supports, never to `sequential`.
> Before leaving §4.6, audit each stage's planned lanes: sequential tasks that form a strict chain MUST NOT share a lane with each other or with adhoc/event-driven/parallel work. If `activation-mode`/`entry-rule` conflicts with `lane`, the mode wins and the lane must be corrected. Same-lane grouping is reserved for intentional `parallel` or `parallel-after-predecessor` siblings, and the rationale must explain the grouping.

> **Outputs are a lossless handoff, not a discovered-name summary.** Project each SDD Outputs table row through the common grammar in [`plugins/variables/io-binding/planning.md` § SDD Outputs table → `tasks.md` projection](plugins/variables/io-binding/planning.md#sdd-outputs-table-to-tasksmd-projection-mandatory), then preserve the resulting list item exactly. Schema discovery may add truly undeclared fields as bare items, but it must not rewrite an SDD row. An explicit equal-name extract such as `greeting -> greeting` stays exactly that; collapsing it to bare `greeting` changes the binding from "write the existing case variable" to "auto-mint a task output." Before the Step 5 approval gate, compare every SDD Outputs row to its task T-entry and fix any missing or changed operator/operand or leaked table placeholder.

> **Registry handoff:** For a resolved `action` or `case-management` T-entry, translate the selected audit object into the canonical `tasks.md` labels and values:
>
> | Task type | `name` from | `folder-path` from | `taskTypeId` from |
> |---|---|---|---|
> | `action` | `selected.deploymentTitle` | `selected.deploymentFolder.fullyQualifiedName` | `selected.id` |
> | `case-management` | `selected.name` | `selected.folders[0].fullyQualifiedName` | `selected.entityKey` |
>
> Before Step 5, confirm these labels and values match the `selected` object in `registry-resolved.json`.

> **No shell commands in task entries.** Each task is a declarative specification. Never write `uip` invocations or any other shell commands inside a task body — the execution phase translates specs into JSON mutations.

> **Record `lane: <n>` per task only when required by the artifact contract.** It is structural/layout state, not a sequencing control. For sequential tasks, preserve their order in `data.tasks`, write `activation-mode: sequential`, put each strict-chain task in its own consecutive lane, and add the `runs-sequentially` entry condition to each task.

> **Placeholder shape for unresolved resources.** If `taskTypeId` / `typeId` / `connectionId` is `<UNRESOLVED: …>`, omit `inputs:` and `outputs:` entirely and capture wiring intent in a trailing comment block. Execution creates a bare task node — structural only. See [placeholder-tasks.md](placeholder-tasks.md) for the full pattern and upgrade path.

### 4.7 Configure conditions

One task per condition. Order within §4.7: stage entry → stage exit → case exit → task entry.

Title format: `Add <scope> condition for "<target>"`

For per-scope fields, consult the corresponding condition plugin:
- `plugins/conditions/stage-entry-conditions/planning.md`
- `plugins/conditions/stage-exit-conditions/planning.md`
- `plugins/conditions/task-entry-conditions/planning.md`
- `plugins/conditions/case-exit-conditions/planning.md`

Every condition T-entry includes `rationale:` copied from the SDD choice it implements. For global events, state why one interrupting secondary-stage entry replaces per-primary-stage exits/tasks.

### 4.8 Set SLA and escalation rules

SLA comes last. Consult [`plugins/sla/planning.md`](plugins/sla/planning.md) for the three sub-operations (default SLA, conditional SLA rules, escalation rules) and per-target ordering. Root rules target `metadata.slaRules[]`; stage rules target that stage's `data.slaRules[]`. Every SLA/escalation T-entry includes `rationale:` copied from the SDD's case/stage SLA rationale.

### 4.9 Not Covered section

Add a brief section at the end of `tasks.md` listing things referenced in sdd.md but outside the scope of `caseplan.json` (e.g., Data Fabric entity schemas). These stay as notes for the user.

---

<!-- END: tasks-plan-contract-guide.md -->
