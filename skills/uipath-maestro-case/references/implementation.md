# Phases 2–6 — Execution: tasks.md → caseplan.json

Execute approved `tasks.md` plan, building `caseplan.json` via direct JSON edits per plugin. Validate, then optionally debug and publish. Five phases: **Phase 2 Prototyping** → **Phase 3 Implementation** → **Phase 4 Validate** → **Phase 5 Debug** → **Phase 6 Publish**.

> **Prerequisite:** User must have explicitly approved `tasks.md` from [Phase 1 Planning](planning.md) before starting.
>
> **Input:** `tasks/tasks.md` — the complete handoff artifact.

> **Five phases follow planning.** Execution splits into **Phase 2 — Prototyping** (skeleton build), **Phase 3 — Implementation** (detail build), **Phase 4 — Validate** (authoritative validate + dump), **Phase 5 — Debug** (optional CLI debug run), **Phase 6 — Publish** (optional Studio Web upload). Hard stops gate Phase 2→3, Phase 4 retry exhaustion, Phase 5 entry, and Phase 6 entry. Read [phased-execution.md](phased-execution.md) for full phase contracts, informational Phase 2 validate, hard-stop prompts, re-entry protocol, retry policy, and abort semantics. Step numbering below marks phase boundaries.

## Per-plugin execution

Every plugin uses direct JSON writes via its `impl-json.md`. Cross-cutting mechanics (ID generation, Pre-flight Checklist, primitive ops, the canonical write contract) are in [case-editing-operations.md](case-editing-operations.md).

**Per-section batched writes — mandatory.** Process `tasks.md` one **section** at a time (§4.2.1 vars, §4.3 triggers, §4.4 stages, §4.6 task-shapes, §9.7 connector schema, §9.8 I/O binding, §10 conditions, §11 SLA):

1. **One Read** of `caseplan.json` at section entry.
2. **Writes sized to section** — pick by T-entry count:
   - **<10 T-entries** — N Edits in sequence, one per T-entry. Skip the re-Read between sibling Edits.
   - **≥10 T-entries** — single whole-section Edit or Write replacing the section's container (e.g., `schema.nodes`, a stage's `data.tasks`). Compose the complete post-section state in reasoning from the section-entry Read, then emit one write. Untouched siblings (other sections, root fields, unrelated nodes) MUST be copied verbatim — drop nothing.
3. **One validate** at section boundary.

TaskUpdate items keyed by T-number are the audit trail — mark each `in_progress` before composing the entry's mutation, `completed` after the write returns success. The audit trail stays T-by-T even when the file diff collapses to one whole-section write.

**Bundle status text with tool_use.** Any progress text emitted alongside writes MUST share the same assistant turn as the next tool_use (text block + tool_use block in one content array). Standalone text-only turns between Edits are forbidden — they each cost ~5s inference + full cache replay for no work. Cap inline status to ≤1 sentence / ~20 tokens. **Hard token cap:** any single text block >200 tokens (or >500 tokens for allow-listed exceptions — completion reports, AskUserQuestion preambles, validate result summaries) is a planning monologue, forbidden regardless of content. **Forbidden announcement verbs** at any length: text blocks starting with `Building`, `Composing`, `Writing`, `Drafting`, `Generating`, `Now I'll`, `Next:`, `Approach:`, `Strategy:`, `Plan:`, `Caveman push:`, `Big single Write:`, `Let me`, or any other narration of the imminent tool call. The tool_use input IS the announcement.

**Cap single Write at ~15K out tok / ~40KB.** When a section's whole-section Write would exceed this, split into Phase 2 skeleton (root + nodes + vars, `edges` stays `[]`, empty task `data`) → Phase 3 fill (per-section Edits onto populated nodes). For cases with ≥40 tasks or ≥8 stages, NEVER emit the full populated caseplan.json in one Write — always Phase 2 → Phase 3 split. A single 15K-out-tok Write turn pays ~150s inference; smaller turns let validate gates catch field drops between phases. Build-assembler helper scripts (`/tmp/build-caseplan.js` etc.) are forbidden — they violate Rule 13 regardless of `/tmp` placement or framing.

For CLI-gated sections (§4.6 non-connector schema, §9.7 connector schema), use **gather-then-write**: run all CLI calls first, collect results in reasoning, then enter the Read → writes → validate batch.

Full contract — recovery, tool primitive selection (Edit default, whole-section Write at ≥10 T-entries), audit trail, scope — in [case-editing-operations.md § Per-section batch write contract](case-editing-operations.md#per-section-batch-write-contract--canonical). Phase 1 `tasks.md` building uses the same section-batched contract per [planning.md §4.0a](planning.md).

> **Per-node-type detail lives in plugins.** This document covers the cross-cutting execution workflow. For how to execute a specific node, consult the matching plugin's `impl-json.md`:
> - Root case → `plugins/case/impl-json.md`
> - Stages → `plugins/stages/impl-json.md`
> - Tasks → `plugins/tasks/<type>/impl-json.md`
> - Triggers → `plugins/triggers/<type>/impl-json.md`
> - Conditions → `plugins/conditions/<scope>/impl-json.md`
> - SLA → `plugins/sla/impl-json.md`
> - Global variables & arguments → `plugins/variables/global-vars/impl-json.md`
> - Task I/O binding → `plugins/variables/io-binding/impl-json.md`
> - Logging → `plugins/logging/impl-json.md`

---

## Issue Log — Initialize Before Step 6

Before any build step, initialize an empty issue list **in the agent's reasoning** (not as a file, not via subprocess). All plugins append to this shared list during execution. Dump to `tasks/build-issues.md` via the Write tool after Step 12. See [`plugins/logging/impl-json.md`](plugins/logging/impl-json.md) for the entry format, severity levels, and file schema.

```text
# pseudocode — kept in the agent's reasoning, not on disk
issues = []  # shared across all steps
```

---

## Seed Phase 2 progress todos — Before Step 6

Before Step 6, seed TodoWrite with the section-level items below. Mark each `in_progress` on entry, `completed` on exit. Replace any Phase 1 todos — do not append.

1. Scaffold solution + project + root case (Step 6)
2. Add triggers (Step 6.1)
3. Declare variables + arguments (Step 6.2)
4. Add stages (Step 7)
5. Write task shapes (Step 9)
6. Regenerate bindings_v2.json (Step 9.4)
7. Skeleton validate + hard stop (Step 9.5)

(No edge step — edges are retired; stage transitions are condition-driven and written in Phase 3 Step 10.)

**Per-T-entry sub-items.** Inside each section, also seed one TodoWrite item per T-entry the section will Edit (e.g., `T04 stage "Intake"`, `T05 stage "Review"`). Mark each `in_progress` before composing the entry's mutation in reasoning, `completed` after the Edit returns success. These per-T-entry items are the audit trail — section-level Edits collapse the file diff, but the todo log preserves T-by-T progress for reviewers (per [case-editing-operations.md § Per-section batch write contract](case-editing-operations.md#per-section-batch-write-contract--canonical)).

---

# Phase 2 — Prototyping (Steps 6 – 9.5)

Steps 6 through 9.5 build structural skeleton: solution, project, root case, global variables, stages, triggers, and tasks without value binding. Full contract in [phased-execution.md § Phase 2](phased-execution.md#phase-2--prototyping).

## Step 6 — Create the Case project structure

The case file must live inside a solution + project. The case plugin owns project scaffolding **and** the root caseplan write. Solution setup and project registration are the only CLI calls:

1. **Step 6.0 (CLI)** — `uip solution init <SolutionName>` — creates the solution directory + `.uipx`.
2. **T01 (plugin)** — execute [`plugins/case/impl-json.md`](plugins/case/impl-json.md) in full:
   - § Scaffold writes 5 boilerplate files (`project.uiproj`, `operate.json`, `entry-points.json`, `bindings_v2.json`, `package-descriptor.json`) directly into `<SolutionDir>/<ProjectName>/`.
   - § Write caseplan.json writes the root skeleton (`root` + empty `nodes: []` + empty `edges: []`).
3. **Step 6.0b (CLI)** — `uip solution project add <AbsolutePathToProjectDir> <AbsolutePathToUipxFile> --output json` — registers the project in `.uipx.Projects[]`. **Both arguments MUST be absolute paths.** Relative form `uip solution project add <ProjectName> <SolutionName>.uipx` fails with `Failed to add project to solution` regardless of CWD. Runs after `project.uiproj` exists.

**No trigger is emitted at T01.** The primary trigger is added by the triggers plugin at T02 — its ID is generated by that plugin. `entry-points.json` is scaffolded with an empty `entryPoints[]` array — the triggers plugin owns every insertion.

## Step 6.1 — Add triggers

For each trigger T-entry in `tasks.md §4.3`, open the matching plugin's `impl-json.md`:

- Manual / Timer / Event (resolved) → `plugins/triggers/<type>/impl-json.md` §3
- Event (UNRESOLVED) → [`plugins/triggers/event/impl-json.md` § Placeholder fallback](plugins/triggers/event/impl-json.md) — node still written; case stays reachable

Each plugin writes one node to `caseplan.json.nodes[]` and appends one entry to `entry-points.json.entryPoints[]` atomically. Capture every `TriggerId` for Step 6.2 (In-arg `elementId`).

## Step 6.2 — Declare global variables and arguments

For each variable/argument T-entry from `tasks.md §4.2.1`, write entries directly into `caseplan.json` per [`plugins/variables/global-vars/impl-json.md`](plugins/variables/global-vars/impl-json.md). This step populates top-level `variables` (inputs, outputs, inputOutputs) and trigger output mappings. Execute these before adding stages — downstream tasks and conditions reference variables via `=vars.<id>`.

## Step 7 — Add stages

For each stage in `tasks.md §4.4`, execute per [`plugins/stages/impl-json.md`](plugins/stages/impl-json.md). **Capture the generated `StageId` for every stage** into the name → ID map (and into `id-map.json`) — downstream tasks, conditions, and SLA all reference it.

`isRequired` from `tasks.md` is planning-only metadata; it is not written into the stage node. It is consumed later by case-exit-conditions with `rule-type: required-stages-completed` (Step 10).

## Step 8 — (RETIRED — no edges)

Edges are retired; there is no edge-building step. `schema.edges` stays `[]`. Stage transitions are expressed as entry/exit conditions, written in Phase 3 Step 10. The case start comes from the first stage's `case-entered` entry condition, not a Trigger→stage edge.

For multi-trigger cases, add the additional triggers via the appropriate trigger plugin (Step 6.1) — no edge wiring is needed; any trigger entering the case activates the first stage's `case-entered` condition.

## Step 9 — Add tasks (Phase 2 shape, gather-then-write)

**Phase A — gather.** For each non-connector task in `tasks.md §4.6`, run `uip maestro case tasks describe --type <type> --id <entityKey> --output json` and collect the input schema in reasoning. Connector tasks (`connector-activity`, `connector-trigger`) skip the gather — `case spec` defers to Phase 3 Step 9.7. Unresolved tasks skip too — they become placeholders per Step 9.1.

**Phase B — batched write.** One Read of `caseplan.json`. Then one Edit per task in §4.6 order, appending the task node to its stage's `data.tasks` lane per the matching plugin's `impl-json.md`. **Capture each `TaskId`** — cross-task references and conditions in Phase 3 need it. Skip the re-Read between sibling Edits. One validate at section end.

Per-class shape inside each Edit:

| Task class | Phase 2 `data` content |
|---|---|
| Non-connector (`process`, `agent`, `rpa`, `action`, `api-workflow`, `case-management`, `wait-for-timer`) | Full `data.inputs[]` schema from the Phase A gather. Each input's `value` is `""`. Outputs populated per plugin. |
| Connector (`connector-activity`, `connector-trigger`) | `data.typeId` + `data.connectionId` set. `data.inputs` omitted. **Do NOT call `case spec` in Phase 2** — schema discovery happens in Phase 3. |
| Unresolved (any class) | Placeholder task per Step 9.1 — empty `data: {}` plus action-only extras. |

**Do NOT bind input `value` fields in Step 9.** All literals, expressions, and cross-task references written in Phase 3 Step 9.8 per [`plugins/variables/io-binding/impl-json.md`](plugins/variables/io-binding/impl-json.md).

On context-compaction mid-gather: re-Read `caseplan.json`, scan for §4.6 tasks not yet appended, re-run Phase A for those only.

**Pass `lane: <n>` on every task** (or the plugin's equivalent JSON field). Default: increment per task within a stage starting at 0 — lane is FE-layout-only for these tasks. **Exception:** parallel members of a `runs-sequentially` group share the same `lane` (shared lane = parallel siblings inside the sequential group, carries execution semantics). Solo runs-sequentially tasks still get own lane.

### Step 9.1 — Placeholder tasks for unresolved resources

When a task entry's `taskTypeId` (or `typeId` / `connectionId` for connector tasks) is `<UNRESOLVED: …>`, create a **placeholder task** instead of halting. See [placeholder-tasks.md](placeholder-tasks.md) for the canonical reference.

For every task class (process / agent / rpa / action / api-workflow / case-management / connector-activity / connector-trigger): follow the Unresolved Fallback section of the matching `plugins/tasks/<type>/planning.md` and write a task with `type` + `displayName` + `id` + `elementId` + `isRequired`, `data: {}`, and no `taskTypeId` / `connectionId` keys directly to `caseplan.json` per `plugins/tasks/<type>/impl-json.md`.

**Skip all input binding for placeholder tasks** — they have no input schema. Capture the intended wiring from the fenced `wiring notes` code block in `tasks.md` into the completion report so the user knows what to hook up after registering the resource.

Placeholder tasks integrate with the rest of the graph:
- **Task-entry conditions** use the captured placeholder `TaskId` normally.
- **Stage-exit `selected-tasks-completed`** rules reference placeholder `TaskId`s normally.
- **Cross-task variable bindings** are deferred — the user binds them after attaching the real resource.

## Step 9.4 — Regenerate bindings_v2.json (batch)

After all non-connector tasks are written (Step 9), regenerate `bindings_v2.json` once per [bindings-v2-sync.md § Regenerate](bindings-v2-sync.md). This single pass converts all root bindings accumulated during Step 9 — no per-task regeneration needed.

## Step 9.5 — Placeholder-mode validate + HARD STOP

End of Phase 2. Full contract (summary content, prompt options, publish branch, abort cleanup, continue branch) in [phased-execution.md § Phase 2 hard stop](phased-execution.md#phase-2-hard-stop). This section is a bridge — do NOT duplicate contract here.

1. Run placeholder-profile validate:

   ```bash
   uip maestro case validate "<caseplan.json path>" --skeleton --output json
   ```

   `--skeleton` skips tasks, SLAs, escalations, and entry/exit rules — those are filled in Phase 3. Structural checks (nodes, edges, identity, types, topology) still run.

   **Do NOT halt on errors or warnings.** Capture error + warning counts for summary; remaining errors are structural and surfaced to user via the hard-stop prompt.

2. Print hard-stop summary, including captured validate counts ([phased-execution.md § Summary content](phased-execution.md#summary-content)).

3. Execute hard-stop prompt + branches per [phased-execution.md § Prompt](phased-execution.md#prompt) and following sections. Unconditional — SKILL.md Rule 11.

On continue (either `Skip publish and continue` or `Continue to phase 3` after publish): proceed to Step 9.6.

---

# Phase 3 — Implementation (Steps 9.6 – 11.5)

Steps 9.6 onwards wire connector task schemas, input/output values, conditions, SLA, and in-expression marker resolution. Full contract in [phased-execution.md § Phase 3](phased-execution.md#phase-3--implementation).

## Step 9.6 — Phase 3 re-entry

Before any Phase 3 mutation:

1. **Re-read `tasks.md`** — per Rule 7 of `SKILL.md`.
2. **Re-read `caseplan.json`** — rebuild name → ID maps from authoritative artifact. See [phased-execution.md § Re-entry protocol](phased-execution.md#re-entry-protocol) for which fields to index.
3. **Seed Phase 3 progress todos** — call TodoWrite with the section-level items below. Mark each `in_progress` on entry, `completed` on exit. Phase 2 todos (if any) are stale — replace, do not append.
   1. Wire connector task schemas (Step 9.7)
   2. Bind task I/O values (Step 9.8)
   3. Add conditions (Step 10)
   4. Configure SLA + escalation (Step 11)
   5. Resolve in-expression `vars.$xref` markers (Step 11.5)

   Inside each section, also seed per-T-entry sub-items (one per T-entry that section will Edit). Mark each `in_progress` before composing the entry's mutation in reasoning, `completed` after the Edit returns success. Per-T-entry items are the audit trail under the per-section batched contract (per [case-editing-operations.md § Per-section batch write contract](case-editing-operations.md#per-section-batch-write-contract--canonical)).

Never trust in-memory maps from Phase 2 without re-reading `caseplan.json` — context may be compacted across hard stop.

## Step 9.7 — Connector task detail (gather-then-write)

**Phase A — gather.** For each connector task (`connector-activity`, `connector-trigger`) in `tasks.md`:

1. Run `get-connection` (each task runs its own — never reuse).
2. Run `uip maestro case spec --type <activity|trigger> --activity-type-id <id> --connection-id <id> --input-details '<json>' --output json` per the plugin's `impl-json.md`.
3. Substitute `{{CONN_BINDING_ID}}` / `{{FOLDER_BINDING_ID}}` placeholders in `caseShape.context[*].value` with minted binding ids; mint `var` / `id` / `elementId` on `caseShape.inputs` / `outputs` per the plugin's uniqueness rule.

Hold all gathered shapes (per-task `caseShape` + root-level Connection + FolderKey bindings) in reasoning. Skip connector tasks that are placeholders (unresolved `typeId` / `connectionId`).

**Phase B — batched write.** One Read of `caseplan.json`. Then for each gathered task: one Edit setting `data.context = caseShape.context`, `data.inputs = caseShape.inputs`, `data.outputs = caseShape.outputs` plus the matching root-level Connection + FolderKey binding entries. Skip the re-Read between sibling Edits.

**Phase C — sync + validate.** Populate IS connection cache per [bindings-v2-sync.md § Populate IS connection cache](bindings-v2-sync.md). Regenerate `bindings_v2.json` once per [bindings-v2-sync.md § Regenerate](bindings-v2-sync.md) — single pass includes non-connector bindings from Step 9 and Connection bindings from this step. Run validate.

On context-compaction mid-gather: re-Read `caseplan.json`, scan for connector tasks without `data.context` populated, re-run Phase A for those only.

## Step 9.8 — Bind task input/output values (per-task Edit batch)

One Read of `caseplan.json` at Step 9.8 entry. Then **one Edit per task** replacing that task's full `data.inputs` array. Skip the re-Read between sibling Edits. Skip placeholder tasks entirely — they have no inputs.

Per-task composition (in reasoning, before that task's Edit) per [`plugins/variables/io-binding/impl-json.md`](plugins/variables/io-binding/impl-json.md):

1. Literals / expressions (`input = "<value>"`): write `<value>` to `input.value`.
2. Cross-task references (`input <- "Stage"."Task".output`): resolve source output's `var` field from the just-Read `caseplan.json`, then write `=vars.<var>` to the target input's `value`.

If a cross-task reference points to a task that does not exist in the just-Read `caseplan.json`, halt — `tasks.md` ordering is wrong; report to the user.

One validate at section end.

## Step 10 — Add conditions (per (scope, target) Edit batch)

One Read of `caseplan.json` at Step 10 entry. Group `tasks.md §4.7` entries by `(scope, target)` pair: each pair becomes one Edit replacing the relevant conditions array on its target node.

| Scope | Target | Edit replaces |
|---|---|---|
| Stage entry | one stage | `nodes[stage].data.entryConditions` |
| Stage exit | one stage | `nodes[stage].data.exitConditions` |
| Task entry | one task | `data.entryConditions` on the task object |
| Case exit | root | `metadata.caseExitRules` |

Skip the re-Read between sibling Edits. One validate at section end. Per-scope composition rules live in the matching plugin's `impl-json.md`:

- Stage entry → [`plugins/conditions/stage-entry-conditions/impl-json.md`](plugins/conditions/stage-entry-conditions/impl-json.md)
- Stage exit → [`plugins/conditions/stage-exit-conditions/impl-json.md`](plugins/conditions/stage-exit-conditions/impl-json.md)
- Task entry → [`plugins/conditions/task-entry-conditions/impl-json.md`](plugins/conditions/task-entry-conditions/impl-json.md)
- Case exit → [`plugins/conditions/case-exit-conditions/impl-json.md`](plugins/conditions/case-exit-conditions/impl-json.md)

> **Connector-bound rules need a CLI gather.** A `wait-for-connector` rule in any scope is NOT a pure JSON write — it requires a `uip maestro case spec --type trigger` call (like Step 9.7 connector tasks) to mint its `uipath` block, plus root bindings + IS-cache + deferred `bindings_v2` sync. Gather per `(scope, target)`, then write. See [connector-trigger-common.md § Target: connector-bound condition rule](connector-trigger-common.md#target-connector-bound-condition-rule). Full `validate` flags a missing `rule.uipath`/`context` (`connector activity missing`), not its internals.

> **Step 10 ends with a `bindings_v2` sync.** After all connector rules across the 4 scopes are written, run the third batched `bindings_v2.json` regeneration + IS-cache population — see [bindings-v2-sync.md § When to Run](bindings-v2-sync.md#when-to-run) (point 3). Without this third sync, rule-introduced Connection/Folder bindings + IS-cache entries don't land until the post-Phase-3 catch-all and `resource refresh` misses them.

## Step 11 — SLA and escalation (per-target Edit batch)

One Read of `caseplan.json` at Step 11 entry. Group `tasks.md §4.8` entries by target (root or stage). For each target, one Edit replacing that target's full `slaRules[]` array per [`plugins/sla/impl-json.md`](plugins/sla/impl-json.md). Skip the re-Read between sibling Edits. Supports per-conditional-rule escalations, ExceptionStage SLA, and multi-recipient single rules. One validate at section end.

## Step 11.5 — Resolve in-expression `vars.$xref` markers (whole-file pass)

Runs after bindings (9.8), conditions (10), and SLA (11) — when every task / trigger / rule output is minted and deduped (the dedup pool spans tasks ∪ triggers ∪ rules, so a marker's target `var` is not final until Step 10's rule outputs are minted). Resolve every `vars.$xref('Stage','Task','output')` marker in `caseplan.json` in ONE pass: one Read, then Edit each string value holding a marker — substitute the source output's post-dedup `var` as bare `vars.<var>` (no leading `=`; the marker already sits inside `=js:`). Sink-blind: covers composite input payloads, `conditionExpression`, SLA `expression`, computed `=` outputs, and connector body fields in one place. An unresolved name-triple is an ERROR (Check 4 below). Algorithm + pseudocode: [`plugins/variables/io-binding/impl-json.md § In-Expression Marker Resolution`](plugins/variables/io-binding/impl-json.md#in-expression-marker-resolution-step-115). One validate at section end.

## Step 12 — End-of-Phase-3 validator pass

> **Algorithm reference:** the per-check pseudocode + AskUserQuestion prompt templates + skill-response-per-pick details all live in [`plugins/variables/io-binding/impl-json.md § Binding Procedure`](plugins/variables/io-binding/impl-json.md#binding-procedure). This step is the orchestration hook; that doc is the algorithm. When in doubt, follow the impl-json doc.

After all value bindings (Step 9.8), conditions (Step 10), SLA (Step 11), and marker resolution (Step 11.5) are written, invoke the end-of-Phase-3 validator — Checks 1, 2, 3, 4.

- **Check 1** — Resolve every `=vars.X` reference against `variables.{inputs, inputOutputs}[].id`. Scan all task input `value` fields, entry/exit condition expressions (stage and task), case-exit and trigger rule expressions, SLA expressions, and `=js:` expressions anywhere they appear. On unresolved → **AskUserQuestion** offering: (a) name the intended variable, (b) remove the reference, (c) continue with best-effort emit (entry logged under Open Items, runtime returns undefined).
- **Check 2 — Out-arg producer presence** — For every formal Out-arg in `variables.outputs[]`, verify the producer/Default situation per [`io-binding/impl-json.md` § Check 2](plugins/variables/io-binding/impl-json.md):
  - **Has Default but no companion** → AskUserQuestion.
  - **No Default + producer declared in SDD on a Rule 17 placeholder task** (declared-but-unresolvable) → no prompt; silent log to `## Open Items for User` in `tasks/build-issues.md`. Rule 17 already prompted the author for this task.
  - **No Default + no producer declared anywhere (pure orphan)** → AskUserQuestion offering 4 options: (a) add producer task output, (b) add Default value, (c) recategorize as Variable / remove, (d) continue with best-effort emit (entry logged under Open Items).
- **Check 3** — Type mismatch between `=vars.X` reference and consumer slot → log WARN inline (non-blocking; string coercion is runtime-tolerant).
- **Check 4 — No surviving `$xref` markers** — Scan every string value in `caseplan.json` for the literal `$xref(`. Step 11.5 resolves all; any survivor means its name-triple failed (typo'd stage / task / output) — the same class of failure as a Check 1 unresolved `=vars.X`, so it gets the same interactive remediation. On unresolved → **AskUserQuestion** (present the outputs that DO exist on the named task as candidates): (a) name the intended source output — skill rewrites the triple, re-resolves, substitutes `vars.<var>`; (b) edit the SDD expression + re-run the Phase 1 dispatcher (when the output genuinely doesn't exist); (c) continue with best-effort emit (token left unsubstituted, entry logged under Open Items; `vars.$xref(...)` throws at runtime until fixed). Detail: [`io-binding/impl-json.md` § Check 4](plugins/variables/io-binding/impl-json.md).

**Build-with-best policy:** for any user pick of "continue with best-effort emit" on a Check 1, Check 2, or Check 4 AskUserQuestion, append a `## Open Items for User` entry to `tasks/build-issues.md` and proceed to Phase 4. AskUserQuestion is the surface; build-with-best is the escape. The skill conservatively emits what it has; Phase 4 validate stays green (structural validity is intact); runtime concerns are listed for pre-publish review.

**Reporting:** at end of Phase 4, count entries in the `## Open Items for User` section of `tasks/build-issues.md` (read the file after writing). If count > 0, the completion report MUST include a literal line of the form:

```
Open Items: <N> entry/entries — review tasks/build-issues.md § Open Items for User before publishing.
```

(Use `entry` for N == 1, `entries` otherwise.) Place this line above the per-stage / per-task summary in the completion report so it's not buried.

End of Phase 3 mutations. Proceed directly to Phase 4 — no hard stop between Phase 3 and Phase 4.

---

# Phase 4 — Validate (Steps 12 – 12.1)

Authoritative validation. Full contract — command, retry policy, AskUserQuestion options — in [phased-execution.md § Phase 4](phased-execution.md#phase-4--validate). This section is a bridge — do NOT duplicate contract here.

## Step 12 — Full validate

Run validate per [phased-execution.md § Phase 4](phased-execution.md#phase-4--validate). On success: proceed to Step 12.1. On 3rd failure: hard-stop prompt per the same section.

## Step 12.1 — Dump issue log

Write issue list to `tasks/build-issues.md` per [`plugins/logging/impl-json.md`](plugins/logging/impl-json.md). On Phase 4 success → proceed to Phase 5.

---

# Phase 5 — Debug (Steps 13, 13a)

Optional CLI debug run. Full contract — report fields, prompt options, debug command, safety warning, loop behavior — in [phased-execution.md § Phase 5](phased-execution.md#phase-5--debug). This section is a bridge — do NOT duplicate contract here.

## Step 13 — Completion report + Debug prompt + session

Print report fields and run AskUserQuestion + debug command per [phased-execution.md § Phase 5](phased-execution.md#phase-5--debug). On `Run debug session` → run `uip solution resources refresh` then `uip maestro case debug`, loop until `Skip to Publish`. On `Skip to Publish` → Phase 6. Never auto-run (Rule 12).

## Step 13a — Troubleshoot failed case

When a debug or process run fails, read **[troubleshooting-guide.md](troubleshooting-guide.md)**. Diagnostic priority: incidents → runtime variables → caseplan.json correlation → traces (last resort).

**Diagnose → fix → re-run loop.** After each diagnostic pass, classify root cause and act:

1. **Fixable in `caseplan.json`** (wrong binding, missing condition, malformed expression, incorrect input value): apply targeted fix via matching plugin's `impl-json.md`, re-run `uip maestro case validate`, then re-run Step 13 debug.
2. **Fixable outside `caseplan.json`** (missing/expired connection, unregistered task type, missing Orchestrator asset, permissions): halt agent edits. Report exact resource + remediation steps to user via **AskUserQuestion** with options — `Resource fixed, re-run debug`, `Abort`.
3. **Inconclusive** (no actionable cause): proceed to next round per retry policy.

**Retry policy.** Up to 3 troubleshoot → fix → debug rounds per failed run. Each round must add new context (different element ID, broader scope, fallback command) or apply different fix — do not repeat identical commands or re-apply same fix. Track round count.

**Per-round timeout.** If debug run exceeds 10 minutes wall-clock, treat round as inconclusive and advance to next round (counts toward 3-round limit). Advisory — do not hard-kill subprocess; classify by elapsed time and move on.

After 3rd inconclusive round (or 3rd debug failure post-fix), halt and ask user with **AskUserQuestion**. Report: instance ID, folder key, incident IDs/messages, faulting element ID, variable snapshot, what was tried each round. Options — `Provide additional context` (user supplies hints; run one more targeted round), `Pause for manual investigation`, `Abort`. Do not propose `caseplan.json` edits without confirmed cause.

---

# Phase 6 — Publish (Steps 14, 15)

Optional Studio Web upload. Full contract — prompt options, publish commands, pack/publish warning — in [phased-execution.md § Phase 6](phased-execution.md#phase-6--publish). This section is a bridge — do NOT duplicate contract here.

## Step 14 — Publish prompt

Run AskUserQuestion per [phased-execution.md § Phase 6](phased-execution.md#phase-6--publish). On `Publish to Studio Web` → Step 15. On `Done` → exit skill.

## Step 15 — Publish to Studio Web

Run `uip solution resources refresh` then `uip solution upload` per [phased-execution.md § Publish notes](phased-execution.md#publish-notes). Print `DesignerUrl`. Exit skill.
