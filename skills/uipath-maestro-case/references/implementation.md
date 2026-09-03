# Phases 2–7 — Execution: sdd.md → caseplan.json

Build `caseplan.json` from `sdd.md` via direct JSON edits per plugin, using `tasks/registry-resolved.json` for tenant identities. Validate, then optionally publish, debug, and publish to Orchestrator. Six phases: **Phase 2 Prototyping** → **Phase 3 Implementation** → **Phase 4 Validate** → **Phase 5 Publish** → **Phase 6 Debug** → **Phase 7 Publish to Orchestrator**.

> **Editing an existing case?** Targeted edits to an existing `caseplan.json` skip this execution pipeline — see [brownfield.md](brownfield.md).

> **Prerequisite:** [Phase 1 Resolution](planning.md) produced `tasks/registry-resolved.json`. Phase 1 auto-proceeds into execution — it stops before Phase 2 only when the request explicitly asked to stop before the build.
>
> **Inputs:** `sdd.md` — the design contract, and the sole source of structure, activation modes, entry rules, inputs, outputs, and rationale. `tasks/registry-resolved.json` — tenant identities only. There is no intermediate plan file; never author one.

> **Element classes.** Execution walks the SDD in six classes, in this order: **variables** (Case Variables table) → **triggers** (Case Triggers table) → **stages** (Section 2 stage headings) → **tasks** (per-stage Tasks tables + their `##### Task N.M` detail blocks) → **conditions** (Stage Entry / Stage Exit / Task Entry / Case Exit tables) → **SLA** (Case-Level SLA + per-stage Stage SLA + per-action Task SLA). Each class is one write section.

> **Completeness principle — no omissions.** Every declaration in `sdd.md` becomes an element in `caseplan.json`; the mapping is 1-to-1. **Never filter** a row because a default rule-type or "implicit behavior" would cover it. **Never merge** two SDD rows "because they're similar." **Never drop** defaults-looking items (`is-interrupting: false`, `runOnlyOnce: true`, `marks-stage-complete: true`) — the explicit declaration is the signal. **Never drop design rationale**: copy each stage/task/SLA `Design Rationale` into the element's `description` where the schema has one, and into `tasks/build-issues.md` where it does not. **When in doubt, emit.** **When a row is ambiguous or unrecognized** (a variable whose category is unclear, a task type outside the closed enum, an aggregate trigger mapping phrase), invoke **AskUserQuestion** with the row content, the specific ambiguity, and bounded options — silent omission is a defect. Step 12's `audit_caseplan.py` gate enforces this against the finished artifact.

> **Six phases follow planning.** Execution splits into **Phase 2 — Prototyping** (reviewable preview: structure, conditions, SLA/escalation, and connector-rule stubs), **Phase 3 — Implementation** (connector schemas, task values, and connector-rule upgrades), **Phase 4 — Validate** (authoritative validate + dump), **Phase 5 — Publish** (optional Studio Web upload), **Phase 6 — Debug** (optional CLI debug run), **Phase 7 — Publish to Orchestrator** (optional `case pack` + `solution pack` + `solution publish`). Hard stops gate Phase 2→3, Phase 4 retry exhaustion, Phase 5 entry, Phase 6 entry, and Phase 7 entry. Read [phased-execution.md](phased-execution.md) for full phase contracts, informational Phase 2 validate, hard-stop prompts, re-entry protocol, retry policy, and abort semantics. Step numbers are stable labels; follow the order stated by each phase.

## Per-plugin execution

Every plugin uses direct JSON writes via its `impl-json.md`. Cross-cutting mechanics (ID generation, Pre-flight Checklist, primitive ops, the canonical write contract) are in [case-editing-operations.md](case-editing-operations.md).

> **Read each `impl-json.md` once per plugin type, not per element.** Group the section's SDD rows by plugin, read that plugin's `impl-json.md` a single time, then execute every row of that type from the one read (this is what the per-section batch write contract already assumes). Re-opening a plugin reference per element is a read-budget defect — observed at up to 26 re-reads of one `impl-json.md` in a single build, each costing a full inference round-trip. After context compaction, re-read only the plugin for the section in progress.

**Per-section batched writes — mandatory.** Process the SDD one **element class** at a time (Phase 2: variables, triggers, stages, task-shapes, SLA, conditions; Phase 3: connector schema at Step 9.7, I/O binding at Step 9.8, connector-rule upgrades at Step 10.5):

1. **One Read** of `caseplan.json` at section entry.
2. **Writes sized to section** — pick by element count:
   - **<10 elements** — N Edits in sequence, one per element. Skip the re-Read between sibling Edits.
   - **≥10 elements** — single whole-section Edit or Write replacing the section's container (e.g., `schema.nodes`, a stage's `data.tasks`). Compose the complete post-section state in reasoning from the section-entry Read, then emit one write. Untouched siblings (other sections, root fields, unrelated nodes) MUST be copied verbatim — drop nothing.
3. **One validate** at section boundary.
4. **One issue-log flush** at the same boundary — append the section's buffered issues to `tasks/build-issues.md` per [`plugins/logging/impl-json.md` § Flush](plugins/logging/impl-json.md), then clear the buffer. The first flush creates the file; later flushes append to its Journal table. **Flush even when the section produced zero issues** — after the first section the file must exist, and its existence is what proves the log survived the build.

TaskUpdate items keyed by SDD element (stage name, task name, variable name) are the audit trail — mark each `in_progress` before composing the element's mutation, `completed` after the write returns success. The audit trail stays element-by-element even when the file diff collapses to one whole-section write.

**Bundle status text with tool_use.** Any progress text emitted alongside writes MUST share the same assistant turn as the next tool_use (text block + tool_use block in one content array). Standalone text-only turns between Edits are forbidden — they each cost ~5s inference + full cache replay for no work. Cap inline status to ≤1 sentence / ~20 tokens. **Hard token cap:** any single text block >200 tokens (or >500 tokens for allow-listed exceptions — completion reports, AskUserQuestion preambles, validate result summaries) is a planning monologue, forbidden regardless of content. **Forbidden announcement verbs** at any length: text blocks starting with `Building`, `Composing`, `Writing`, `Drafting`, `Generating`, `Now I'll`, `Next:`, `Approach:`, `Strategy:`, `Plan:`, `Caveman push:`, `Big single Write:`, `Let me`, or any other narration of the imminent tool call. The tool_use input IS the announcement.

**Cap single Write at ~15K out tok / ~40KB.** When a section's whole-section Write would exceed this, keep the per-section cadence: root/nodes/vars and task shapes first, then Phase 2 SLA and conditions, then Phase 3 connector/value details. For cases with ≥40 tasks or ≥8 stages, NEVER emit the full populated caseplan.json in one Write. A single 15K-out-tok Write turn pays ~150s inference; smaller turns let validate gates catch field drops between phases. Build-assembler helper scripts (`/tmp/build-caseplan.js` etc.) are forbidden — they violate Rule 13 regardless of `/tmp` placement or framing.

For CLI-gated sections (non-connector task schema at Step 9, connector schema at Step 9.7), use **gather-then-write**: run all CLI calls first, collect results in reasoning, then enter the Read → writes → validate batch.

Full contract — recovery, tool primitive selection (Edit default, whole-section Write at ≥10 elements), audit trail, scope — in [case-editing-operations.md § Per-section batch write contract](case-editing-operations.md#per-section-batch-write-contract--canonical). Phase 1's `registry-resolved.json` uses the same section-batched contract per [planning.md Step 4](planning.md).

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

Before any build step, initialize an empty issue buffer **in the agent's reasoning** (not as a file, not via subprocess). All plugins append to it during the current section, and **the buffer is flushed to `tasks/build-issues.md` at every section boundary, then cleared** — it is NOT a whole-build accumulator. See [`plugins/logging/impl-json.md`](plugins/logging/impl-json.md) for the entry format, severity levels, flush mechanics, and file schema.

```text
# pseudocode — per-section buffer, flushed at each section boundary
issues = []
```

> **Why incremental.** A whole-build buffer held in reasoning is lost to context pressure before it is ever written, and no Step 12 check reads the log. Flushing per section bounds worst-case loss to one section and rides the validate seam already at that boundary.

---

## Seed Phase 2 progress todos — Before Step 6

Before Step 6, seed TodoWrite with the section-level items below. Mark each `in_progress` on entry, `completed` on exit. Replace any Phase 1 todos — do not append.

1. Scaffold solution + project + root case (Step 6)
2. Add triggers (Step 6.1)
3. Declare variables + arguments (Step 6.2)
4. Refresh entry-points.json input/output (Step 6.3)
5. Add stages (Step 7)
6. Write task shapes (Step 9)
7. Regenerate bindings_v2.json (Step 9.4)
8. Write SLA + escalation objects (Step 11)
9. Add conditions with connector-rule stubs (Step 10)
10. Preview validate + boundary (Step 11.9)

(No edge step — Rule 20; see Step 8.)

**Per-element sub-items.** Inside each section, also seed one TodoWrite item per SDD element the section will Edit, named for the element (e.g., `stage "Intake"`, `stage "Review"`). Mark each `in_progress` before composing the element's mutation in reasoning, `completed` after the Edit returns success. These per-element items are the audit trail — section-level Edits collapse the file diff, but the todo log preserves element-by-element progress for reviewers (per [case-editing-operations.md § Per-section batch write contract](case-editing-operations.md#per-section-batch-write-contract--canonical)).

---

# Phase 2 — Prototyping (Steps 6 – 11.9)

Execution order: 6 → 6.1 → 6.2 → 6.3 → 7 → 9 → 9.4 → 11 → 10 → 11.9. Step numbers are stable labels; SLA objects run before conditions so `sla-status-change` can reference emitted IDs. The preview contains the complete case flow and SLA model; task values, connector task schemas, and final connector-rule configuration remain deferred. Full contract in [phased-execution.md § Phase 2](phased-execution.md#phase-2--prototyping).

## Step 6 — Create the Case project structure

The case file must live inside a solution + project. The case plugin owns project scaffolding **and** the root caseplan write. Solution setup and project registration are the only CLI calls. **Never use `uip maestro case cases add` (or another case mutation command) to create the root caseplan** — execute the T01 direct-JSON recipe so required root metadata such as `caseDirectlyPassTaskOutputs` is emitted. **Never use `uip maestro case init`** — T01 writes the same 5 files, and run outside `<SolutionDir>` (which includes the `solution init && case init` chain) it auto-creates a second solution and forks the working root — see [`case-commands.md` § uip maestro case init](case-commands.md#uip-maestro-case-init).

1. **Step 6.0 (CLI)** — `uip solution init <SolutionName>` — creates the solution directory + `.uipx`. **Idempotent w.r.t. a Phase 1 Create:** if the Rule 17 **Create** flow already scaffolded the solution in Phase 1 (per [registry-discovery.md § Create-on-Missing → 0 Prerequisite](registry-discovery.md#create-on-missing-build-and-rediscovery)), the `.uipx` already exists — **skip this call iff that exact `<SolutionDir>/<SolutionName>.uipx` is present** (same canonical name + working-root location — [plugins/case/planning.md § Naming](plugins/case/planning.md#project-structure-prerequisites)). Re-running `init` over an existing solution errors, and a differently-named or -located `init` would fork the solution.
2. **T01 (plugin)** — execute [`plugins/case/impl-json.md`](plugins/case/impl-json.md) in full:
   - § Scaffold writes 5 boilerplate files (`project.uiproj`, `operate.json`, `entry-points.json`, `bindings_v2.json`, `package-descriptor.json`) directly into `<SolutionDir>/<ProjectName>/`.
   - § Write caseplan.json writes the root skeleton (`root` + empty `nodes: []` + empty `edges: []`).
3. **Step 6.0b (CLI)** — `uip solution projects add <AbsolutePathToProjectDir> <AbsolutePathToUipxFile> --output json` — registers the project in `.uipx.Projects[]`. **Both arguments MUST be absolute paths.** Relative form `uip solution projects add <ProjectName> <SolutionName>.uipx` fails with `Failed to add project to solution` regardless of CWD. Runs after `project.uiproj` exists.
4. **Step 6.0c (verify)** — exactly one `.uipx` under the working root, at `<SolutionDir>/<SolutionName>.uipx`. A second manifest is a forked solution: read the stray project first — delete that solution directory if it holds no work, else adopt it as `<SolutionDir>`. Validate cannot catch this; it reads only the caseplan path given.

**No trigger is emitted at T01.** The primary trigger is added by the triggers plugin at T02 — its ID is generated by that plugin. `entry-points.json` is scaffolded with an empty `entryPoints[]` array — the triggers plugin owns every insertion.

## Step 6.1 — Add triggers

For each row of the SDD's Case Triggers table, open the matching plugin's `impl-json.md`:

- Manual / Timer / Event (resolved) → `plugins/triggers/<type>/impl-json.md` §3
- Event (UNRESOLVED) → [`plugins/triggers/event/impl-json.md` § Placeholder fallback](plugins/triggers/event/impl-json.md) — node still written; case stays reachable

Each plugin writes one node to `caseplan.json.nodes[]` and appends one entry to `entry-points.json.entryPoints[]` atomically. Capture every `TriggerId` for Step 6.2 — an In-arg's `elementId` resolves to `id-map[<sourceTriggers T-number>].id`, or the primary trigger (T02) when its `sourceTriggers` is blank.

## Step 6.2 — Declare global variables and arguments

For each row of the SDD's Case Variables table, write entries directly into `caseplan.json` per [`plugins/variables/global-vars/impl-json.md`](plugins/variables/global-vars/impl-json.md). This step populates top-level `variables` (inputs, outputs, inputOutputs) and trigger output mappings. Execute these before adding stages — downstream tasks and conditions reference variables via `=vars.<id>`.

## Step 6.3 — Refresh entry-points.json input/output

After Step 6.2, project the declared In/Out arguments onto every `entry-points.json` entry's `input`/`output` schema per [entry-points-sync.md](entry-points-sync.md). Triggers (Step 6.1) scaffold each entry with empty `input`/`output` because variables don't exist yet; this back-fills them. Prerequisites — all entries (Step 6.1) + all In/Out args (Step 6.2) — are complete here, and In/Out formal args never change in Phase 3, so the file is correct from the Phase-2 publish branch onward. Idempotent — re-run on regenerate. Verified by Step 12 Check 6.

> **Execution order.** Always: variables → triggers → stages → tasks → conditions → SLA. Within a class, follow SDD document order: stages in Section 2 heading order, tasks in their stage's Tasks-table row order. Ordering carries no execution semantics on its own — `activation-mode` and the entry rule do.

## Step 7 — Add stages

For each stage heading in SDD Section 2 (primary and `Secondary Stage`), execute per [`plugins/stages/impl-json.md`](plugins/stages/impl-json.md). **Capture the generated `StageId` for every stage** into the name → ID map (and into `id-map.json`) — downstream tasks, conditions, and SLA all reference it.

The SDD's **Required for Case Completion** is planning-only metadata; it is not written into the stage node. It is consumed by case-exit-conditions with `rule-type: required-stages-completed` (Step 10).

## Step 8 — (RETIRED — no edges)

No edge-building step (Rule 20) — stage transitions are entry/exit conditions, written in Phase 2 Step 10. Multi-trigger cases: add extra triggers via the trigger plugin (Step 6.1); any trigger entering the case activates the first stage's `case-entered` condition.

## Step 9 — Add tasks (Phase 2 shape, gather-then-write)

**Phase A — gather.** For each non-connector task in the SDD's per-stage Tasks tables, run `uip maestro case tasks describe --type <type> --id <entityKey> --output json` and collect the input schema in reasoning. Connector tasks (`connector-activity`, `connector-trigger`) skip the gather — `case spec` defers to Phase 3 Step 9.7. Unresolved tasks skip too — they become placeholders per Step 9.1. **Inline-built siblings (agent / api-workflow, Rule 17 Create) also skip the gather** — they were resolved + bound in Phase 1 with I/O read from the sibling's on-disk `entry-points.json`; their `taskTypeId` is a local audit-only key with no tenant resource, so tenant `tasks describe` does not apply. See the per-type Built-inline notes: [`plugins/tasks/agent/impl-json.md`](plugins/tasks/agent/impl-json.md), [`plugins/tasks/api-workflow/impl-json.md`](plugins/tasks/api-workflow/impl-json.md).

**Phase B — batched write.** One Read of `caseplan.json`. Then one Edit per task in SDD order, appending the task node to its stage's `data.tasks` structure per the matching plugin's `impl-json.md` and the placement contract below. **Capture each `TaskId`** — Phase 2 conditions and Phase 3 cross-task references need it. Skip the re-Read between sibling Edits. One validate at section end.

Per-class shape inside each Edit:

| Task class | Phase 2 `data` content |
|---|---|
| Non-connector (`process`, `agent`, `rpa`, `action`, `api-workflow`, `case-management`, `wait-for-timer`) | Full `data.inputs[]` schema from the Phase A gather. Each input's `value` is `""`. Outputs populated per plugin. |
| Connector (`connector-activity`, `connector-trigger`) | `data.typeId` + `data.connectionId` set. `data.inputs` omitted. **Do NOT call `case spec` in Phase 2** — schema discovery happens in Phase 3. |
| Unresolved (any class) | Placeholder task per Step 9.1 — empty `data: {}` plus action-only extras. |

**Do NOT bind input `value` fields in Step 9.** All literals, expressions, and cross-task references written in Phase 3 Step 9.8 per [`plugins/variables/io-binding/impl-json.md`](plugins/variables/io-binding/impl-json.md).

On context-compaction mid-gather: re-Read `caseplan.json`, scan for SDD tasks not yet appended, re-run Phase A for those only.

**Task placement contract.** Placement is determined by the SDD's **Activation Mode** column plus the task's **Entry Condition** table; the `data.tasks` task-set index is derived from them, never the reverse.

**Activation-mode audit — before writing any task node.** Scan every stage's task list and fix the mode/rule pairing first; an explicit rule in the SDD always wins, and this audit verifies the handoff rather than redesigning it.

- Contiguous ordered work in one stage (`then`, `after`, `before`, `in order`, or an upstream prerequisite) → `sequential` + `runs-sequentially` on every task in the ordered run, including the first, unless the SDD declares another legal rule.
- Independent work that starts with the stage → `parallel` + `current-stage-entered`. A single-task stage or list position never makes a task sequential.
- Connector/event callback wait → `event-triggered`, usually `wait-for-connector`.
- User-launched optional work → `adhoc` + `adhoc` + `isRequired: false`.
- Branch convergence, fan-in, decision-result routing, or a non-immediate dependency → `fan-in` or `conditional-gate` + `selected-tasks-completed`, with the selected tasks named.

Preserve each explicit `selected-tasks-completed` row and selector only after confirming every selected task is a non-adhoc sibling in the same stage; stop and repair an invalid selector before writing. Never map a valid selected-task gate to `sequential`.

**Lane grouping.** `lane` is the zero-based `data.tasks` task-set index — a number, never a descriptive label. Tasks that run as one task set share the **same** number: `parallel-after-predecessor` siblings after one predecessor share a lane, and a strict sequential chain uses consecutive single-task lanes (`[[A], [B], [C]]`) and never reuses one. Giving two parallel siblings different lanes emits them as separate task sets — the defect the mode exists to prevent. If mode and lane conflict, the mode wins and the completion report must mention the lane correction.

- `activation-mode: sequential` or `entry-rule: runs-sequentially` → append according to the planned task-set order. Strict chains use new single-task inner arrays in declaration order (`[[A], [B], [C]]`); `parallel-after-predecessor` siblings share the same later inner array (`[[A], [B, C], [D]]`).
- `activation-mode: adhoc`, `event-triggered`, `fan-in`, `conditional-gate`, or any standalone non-parallel task → append as its own single-task inner array.
- Only `activation-mode: parallel` or `parallel-after-predecessor` with an explicit same-lane intent and rationale may share an inner array (`[[A, B], [C]]` or `[[A], [B, C], [D]]`). This is the only case where appending to an existing `data.tasks[laneIndex][]` is valid.

**Parallel-after-predecessor guard.** If two or more independent tasks share the same immediate predecessor task or predecessor task set, write them into the same next inner array and keep `activation-mode: parallel-after-predecessor`; do not convert them into separate event-triggered tasks with duplicate `selected-tasks-completed("<previous>")` entry rules. Duplicate selected-task gates on the immediate predecessor are a planning defect to repair before write.

> **`validate` cannot catch a wrong grouping.** Strict-sequential and parallel-after-predecessor emit the same entry rule (`runs-sequentially`); only the `data.tasks` grouping differs. `uip maestro case validate` returns `Valid` for a strict chain, a shared set, a shared set at index 0, and even mixed entry rules inside one set (as of uip 1.198, 2026-08-02). Grouping is enforced only here — get it right at write time; a clean validate is not evidence it is correct.

**Pass `lane: <n>` on every task** only when required by the artifact contract. Default: increment per task within a stage starting at 0; lane is a `data.tasks` task-set index. A strict sequential chain is represented as consecutive single-task sets (`[[A], [B], [C]]`) plus `runs-sequentially` on each task. Reuse the same lane only for intentionally parallel siblings, including stage-start siblings (`[[A, B], [C]]`) and siblings after a predecessor (`[[A], [B, C], [D]]`). Sequencing comes from the task's `entryConditions` and the order of task sets in `data.tasks`, not from lane-sharing alone.

**Task envelope fields.** Write `isRequired` and `shouldRunOnlyOnce` from the SDD's **Task envelope** table (`Required` / `Run Only Once`). If `runOnlyOnce` is omitted, default `shouldRunOnlyOnce` to `false` to match frontend new-task behavior. Do not infer `true` from task type; re-entry semantics from the SDD are the source of truth.

### Step 9.1 — Placeholder tasks for unresolved resources

When a task entry's `taskTypeId` (or `typeId` / `connectionId` for connector tasks) is `<UNRESOLVED: …>`, create a **placeholder task** instead of halting. See [placeholder-tasks.md](placeholder-tasks.md) for the canonical reference.

For every task class (process / agent / rpa / action / api-workflow / case-management / connector-activity / connector-trigger): follow the Unresolved Fallback section of the matching `plugins/tasks/<type>/planning.md` and write a task with `type` + `displayName` + `id` + `elementId` + `isRequired`, `data: {}`, and no `taskTypeId` / `connectionId` keys directly to `caseplan.json` per `plugins/tasks/<type>/impl-json.md`.

**Skip all input binding for placeholder tasks** — they have no input schema. Capture the intended wiring from the entry's `wiringNotes` in `tasks/registry-resolved.json` into the completion report so the user knows what to hook up after registering the resource.

Placeholder tasks integrate with the rest of the graph:
- **Task-entry conditions** use the captured placeholder `TaskId` normally.
- **Stage-exit `selected-tasks-completed`** rules reference placeholder `TaskId`s normally.
- **Cross-task variable bindings** are deferred — the user binds them after attaching the real resource.

## Step 9.4 — Regenerate bindings_v2.json (batch)

After all non-connector tasks are written (Step 9), regenerate `bindings_v2.json` once per [bindings-v2-sync.md § Regenerate](bindings-v2-sync.md). This single pass converts all root bindings accumulated during Step 9 — no per-task regeneration needed.

## Step 11 — Write SLA and escalation objects (per-target Edit batch)

One Read of `caseplan.json` at Step 11 entry. Group the SDD's SLA rows (Case-Level SLA Escalation Rules, per-stage Stage SLA, per-action Task SLA) by target (root or stage). For each target, compose and write the complete `slaRules[]` array per [`plugins/sla/impl-json.md`](plugins/sla/impl-json.md).

Mint each stable `sla_` / `esc_` ID while composing its object, write the object and its `id-map.json` entry in the same section, and reject collisions before the Edit. An escalation-only target still receives the documented synthetic default SLA object. There is no separate ID-preallocation pass: Step 10 resolves `sla-status-change` references against the objects already present in `caseplan.json`, with `id-map.json` as a cross-check. One validate at section end.

## Step 10 — Add conditions (per (scope, target) Edit batch)

One Read of `caseplan.json` at Step 10 entry. Group the SDD's condition rows (Stage Entry / Stage Exit / Task Entry / Case Exit) by `(scope, target)` pair: each pair becomes one Edit replacing the relevant conditions array on its target node.

| Scope | Target | Edit replaces |
|---|---|---|
| Stage entry | one stage | `nodes[stage].data.entryConditions` |
| Stage exit | one stage | `nodes[stage].data.exitConditions` |
| Task entry | one task | `data.entryConditions` on the task object |
| Case exit | root | `metadata.caseExitRules` |

Per-scope composition rules live in the matching plugin's `impl-json.md`. Skip the re-Read between sibling Edits; run one validate at section end.

For every `wait-for-connector` rule, write the canonical stub `uipath` from [`connector-trigger-impl.md § Placeholder fallback`](connector-trigger-impl.md#placeholder-fallback) in Phase 2 **even when its connector resolved in planning**. Do not call `case spec` and do not add Connection/Folder bindings here. Its `id-map.json` value must include `{kind:"condition", id:"<conditionId>", ruleId:"<ruleId>", scope:"<scope>", targetId:"<containerId>"}` so Phase 3 can locate the exact stub without matching display text (`targetId` is the stage ID, task ID, or `root`; task-entry entries also retain `stageId`). Phase 3 Step 10.5 upgrades only `rule.uipath`; a truly unresolved connector keeps the same stub and is reported at completion.

## Step 11.9 — Preview validate + Phase 2 boundary

End of Phase 2. Full contract (summary content, prompt options, publish branch, abort cleanup, continue branch) lives in [phased-execution.md § Phase 2 hard stop](phased-execution.md#phase-2-hard-stop).

1. Try the preview profile:

   ```bash
   uip maestro case validate "<caseplan.json path>" --skeleton-v2 --output json
   ```

2. Fall back once to `--skeleton` only when the parser response names `--skeleton-v2` as unknown or unsupported (typically `ErrorCode: "invalid_argument"` and exit code 3). Exit 3 without that flag-specific message is not sufficient. A v2 validation result containing genuine case errors means the profile ran; capture those findings and do **not** fall back.
3. Print the selected profile plus error/warning counts, then execute the Rule 11 boundary branch. This validation is advisory: never halt solely on its findings. Legacy `--skeleton` checks structure only, so its summary must say rules/SLA remain covered by authoritative Phase 4 validation.

On continue (either `Skip publish and continue` or `Continue to implementation` after publish), proceed to Step 9.6.

---

# Phase 3 — Implementation (Steps 9.6 – 11.5)

Execution order: 9.6 → 9.7 → 9.8 → 10.5 → 11.5 → 12. Phase 3 wires connector task schemas, input/output values, resolved connector-rule configuration, and in-expression markers. Conditions and SLA already exist from Phase 2. Full contract in [phased-execution.md § Phase 3](phased-execution.md#phase-3--implementation).

## Step 9.6 — Phase 3 re-entry

Before any Phase 3 mutation:

1. **Re-read the SDD's task detail blocks** (`##### Task N.M`, their Inputs/Outputs tables) and `tasks/registry-resolved.json` — Phase 3 binds values from them.
2. **Re-read `caseplan.json`** — rebuild name → ID maps from authoritative artifact. See [phased-execution.md § Re-entry protocol](phased-execution.md#re-entry-protocol) for which fields to index.
3. **Seed Phase 3 progress todos** — call TodoWrite with the section-level items below. Mark each `in_progress` on entry, `completed` on exit. Phase 2 todos (if any) are stale — replace, do not append.
   1. Wire connector task schemas (Step 9.7)
   2. Bind task I/O values (Step 9.8)
   3. Upgrade resolved connector-bound condition rules (Step 10.5)
   4. Resolve in-expression `vars.$xref` markers (Step 11.5)

   Inside each section, also seed per-element sub-items (one per SDD element that section will Edit). Mark each `in_progress` before composing the element's mutation in reasoning, `completed` after the Edit returns success. Per-element items are the audit trail under the per-section batched contract (per [case-editing-operations.md § Per-section batch write contract](case-editing-operations.md#per-section-batch-write-contract--canonical)).

Never trust in-memory maps from Phase 2 without re-reading `caseplan.json` — context may be compacted across hard stop.

## Step 9.7 — Connector task detail (gather-then-write)

**Phase A — gather.** For each connector task (`connector-activity`, `connector-trigger`) in the SDD:

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
2. Cross-task references (`input <- "Stage"."Task".output`): resolve the source output reference ID from the just-Read `caseplan.json` using [`io-binding/impl-json.md` § Output reference ID](plugins/variables/io-binding/impl-json.md#output-reference-id-authoritative), then write `=vars.<outputReferenceId>` to the target input's `value`.

If a cross-task reference points to a task that does not exist in the just-Read `caseplan.json`, halt — the SDD orders the consumer before its producer; report to the user.

One validate at section end.

## Step 10.5 — Upgrade connector-bound condition-rule stubs (gather-then-write)

Read `caseplan.json` and scan all four condition scopes for `wait-for-connector` rules whose `uipath.context` still contains the canonical `connectorKey: "placeholder"` and `operation: "placeholder"` entries. Match each rule to its connector fields in `tasks/registry-resolved.json` through its Phase 2 `id-map.json` entry.

For each matched rule whose connector resolved in planning, run the connector-trigger `case spec --type trigger --input-details` procedure, mint its output IDs/element IDs, and gather its root Connection/Folder bindings. Then Edit **only that rule's `uipath` block**. Preserve the enclosing condition array plus the rule's `id`, `rule`, `conditionExpression`, scope, and placement. Apply declared rule-output bindings after the real outputs exist.

If the connector is `<UNRESOLVED>` or `case spec` fails, leave the stub unchanged, log it, and list it in the completion report. After all successful upgrades, populate the IS cache and regenerate `bindings_v2.json` once. Re-scan: every resolved rule must be free of `"placeholder"`; any remaining stub must map to a reported unresolved connector. Full procedure and scope-specific `elementId` rules: [`connector-trigger-impl.md § Target: connector-bound condition rule`](connector-trigger-impl.md#target-connector-bound-condition-rule).

## Step 11.5 — Resolve in-expression `vars.$xref` markers (whole-file pass)

Runs after bindings (9.8) and connector-rule upgrades (10.5), when every task / trigger / rule output is minted and deduped. Conditions and SLA were already written in Phase 2. Resolve every `vars.$xref('Stage','Task','output')` marker in `caseplan.json` in ONE pass: one Read, then Edit each string value holding a marker — resolve the source through the common output-reference-ID algorithm and substitute bare `vars.<outputReferenceId>` (no leading `=`; the marker already sits inside `=js:`). Sink-blind: covers composite input payloads, `conditionExpression`, SLA `expression`, computed `=` outputs, and connector body fields in one place. An unresolved name-triple or reference ID is an ERROR (Check 4 below). Algorithm + pseudocode: [`plugins/variables/io-binding/impl-json.md § In-Expression Marker Resolution`](plugins/variables/io-binding/impl-json.md#in-expression-marker-resolution-step-115). One validate at section end.

## Step 12 — End-of-Phase-3 validator pass

> **Algorithm reference:** the per-check pseudocode + AskUserQuestion prompt templates + skill-response-per-pick details all live in [`plugins/variables/io-binding/impl-json.md § Binding Procedure`](plugins/variables/io-binding/impl-json.md#binding-procedure). This step is the orchestration hook; that doc is the algorithm. When in doubt, follow the impl-json doc.

After value bindings (Step 9.8), connector-rule upgrades (Step 10.5), and marker resolution (Step 11.5), invoke the end-of-Phase-3 validator — Checks 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15. Phase 2 conditions and SLA remain in place throughout.

- **Check 1** — Resolve every `=vars.X` reference against `variables.{inputs, inputOutputs}[].id`. Scan all task input `value` fields, entry/exit condition expressions (stage and task), case-exit and trigger rule expressions, SLA expressions, and `=js:` expressions anywhere they appear. On unresolved → **AskUserQuestion** offering: (a) name the intended variable, (b) remove the reference, (c) continue with best-effort emit (entry logged under Open Items, runtime returns undefined).
- **Check 2 — Out-arg producer presence** — For every formal Out-arg in `variables.outputs[]`, verify the producer/Default situation per [`io-binding/impl-json.md` § Check 2](plugins/variables/io-binding/impl-json.md):
  - **Has Default but no companion** → AskUserQuestion.
  - **No Default + producer declared in SDD on a Rule 17 placeholder task** (declared-but-unresolvable) → no prompt; silent log to `## Open Items for User` in `tasks/build-issues.md`. Rule 17 already prompted the author for this task.
  - **No Default + no producer declared anywhere (pure orphan)** → AskUserQuestion offering 4 options: (a) add producer task output, (b) add Default value, (c) recategorize as Variable / remove, (d) continue with best-effort emit (entry logged under Open Items).
- **Check 3** — Type mismatch between `=vars.X` reference and consumer slot → log WARN inline (non-blocking; string coercion is runtime-tolerant).
  - **Check 4 — No surviving `$xref` markers** — Scan every string value in `caseplan.json` for the literal `$xref(`. Step 11.5 resolves all; any survivor means its name-triple or output reference ID failed — the same class of failure as a Check 1 unresolved `=vars.X`, so it gets the same interactive remediation. On unresolved → **AskUserQuestion** (present the outputs that DO exist on the named task as candidates): (a) name the intended source output — skill rewrites the triple, re-resolves, substitutes `vars.<outputReferenceId>`; (b) edit the SDD expression + re-run the Phase 1 dispatcher (when the output genuinely doesn't exist); (c) continue with best-effort emit (token left unsubstituted, entry logged under Open Items; `vars.$xref(...)` throws at runtime until fixed). Detail: [`io-binding/impl-json.md` § Check 4](plugins/variables/io-binding/impl-json.md).
  - **Check 5 — Resolved-resource I/O completeness** — For each task with a persisted contract in `tasks/registry-resolved.json`, verify every **required** declared input has a bound `value` and every extract output `Field` exists in the resolved output contract. An upstream-output-fed input (`=vars.<outputReferenceId>` / resolved `$xref`) counts as bound with NO §1.5 row. On unbound-required-input or phantom-output-field → **AskUserQuestion**: (a) bind / re-point, (b) `<UNRESOLVED>`+review-item / drop row, (c) continue with best-effort emit (entry logged under Open Items; runtime null until fixed). Tasks with no contract (placeholder / `<UNRESOLVED>`) are skipped. Detail: [`io-binding/impl-json.md` § Check 5](plugins/variables/io-binding/impl-json.md#check-5--resolved-resource-io-completeness).
- **Check 6 — Entry-point schema parity** — Verify every `entry-points.json` entry's `input`/`output` matches the In/Out args projected at Step 6.3 (keys, type mapping, `required`, `file`/`jsonSchema` shapes), plus unique `filePath` fragments and no orphaned `inputs[].elementId`. **Non-interactive:** on mismatch re-run the Step 6.3 refresh once; if still divergent (or a uniqueness/orphan finding) log to `## Open Items for User` and continue. No AskUserQuestion. Algorithm: [`entry-points-sync.md § Check 6`](entry-points-sync.md#check-6--entry-point-schema-parity-step-12-validator).
- **Check 7 — Bindings sidecar parity** — Compare `bindings_v2.json.resources[]` with the complete projection of top-level `caseplan.json.bindings[]` using [`bindings-v2-sync.md`](bindings-v2-sync.md). If they differ — including non-empty bindings with empty resources — regenerate the full sidecar once and re-check. If they still differ, halt before Phase 4. This check is non-interactive.
- **Check 8 — Global generated-output ID uniqueness** — Read the completed `caseplan.json` and build one owner-keyed uniqueness pool from root variables plus every task, trigger, and connector-rule output across all condition scopes. Include unused and schema-generated outputs such as `Error` and `response`. Apply the [global uniqueness rule](plugins/variables/global-vars/impl-json.md#uniqueness-rule): on collision, suffix the later producer, update only that producer's fields and consumers by producer ownership, then re-run the affected binding and marker-resolution steps. Re-read and re-scan the complete pool; halt before Phase 4 if any duplicate generated `id` or `var` remains. `uip maestro case validate` success does not satisfy this check.
- **Check 9 — Resolved-resource emission and repair preservation** — Read `tasks/registry-resolved.json`, `sdd.md`, `caseplan.json`, and `bindings_v2.json`. For every registry entry with a non-null `selected`, locate its declared `(stage, task)` in `caseplan.json`. The task MUST exist and MUST NOT have `data: {}`. For non-connector task types, `data.name` and `data.folderPath` MUST each be `=bindings.<id>` references to complete root binding entries (all required fields present) — Check 7 covers their projection into `bindings_v2.json.resources[]`. A selected resource is never eligible for a placeholder fallback. Any whole-file Write used to repair a finding follows the repair-preservation contract in [`case-editing-operations.md § Per-section batch write contract`](case-editing-operations.md#per-section-batch-write-contract--canonical) — a dropped stage, task, root binding, or selected-resource task is a hard failure. Repair only the named task/binding with a targeted Edit, then repeat Checks 7 and 9. Do not enter Phase 4, report completion, or downgrade this finding to an Open Item while it remains unresolved; `uip maestro case validate` success does not satisfy this check.
- **Check 10 — Formal-arg slot ID format** — For every entry in `variables.inputs[]` and `variables.outputs[]`, verify `id` matches `^v[A-Za-z0-9]{8}$` per [`global-vars/impl-json.md` § Formal-arg slot ID format](plugins/variables/global-vars/impl-json.md#formal-arg-slot-id-format). The most common violation is copying the human-readable companion name into the formal slot (e.g. `variables.inputs[].id: "applicantName"` instead of `"vK3mNp9Qx"`) — `uip maestro case validate` does not catch this, so it silently produces a case whose BPMN packaging can reject the id. **Non-interactive repair:** mint a replacement `v`+8-chars id, deduplicated against the Check 8 global pool; update the `variables.inputs[]`/`variables.outputs[]` entry's `id` to the new value; for an `inputs[]` (In-arg) entry, also find its bound trigger node's `data.inputs.outputs[]` bridge entry whose `source == "=vars.<old id>"` and rewrite it to `"=vars.<new id>"` (skip this sub-step when the bound trigger is a placeholder — no bridge was ever written, per [global-vars/impl-json.md § In argument](plugins/variables/global-vars/impl-json.md#in-argument)). Leave `name`, `var`, and the `inputOutputs[]` companion's `id` unchanged — only the formal slot's `id` (and, for In-args, the bridge's `source`) are rewritten. Re-scan `variables.inputs[]`/`variables.outputs[]` after repair; halt before Phase 4 if any entry still fails the format after one repair pass.
- **Check 11 — resourceKey self-consistency (non-connector tasks)** — For every top-level `bindings[]` pair sharing a `resourceKey` on a non-connector task (`process`, `agent`, `rpa`, `api-workflow`, `case-management`, `action`), verify `resourceKey` is internally consistent with the pair's own `default` fields per [`bindings/impl-json.md` § resourceKey construction](plugins/variables/bindings/impl-json.md#resourcekey-construction--non-connector-tasks): normally `resourceKey == "<folderPath-binding default>.<name-binding default>"`; for an inline-built sibling (agent/api-workflow whose `folderPath` binding `default` is `""`), `resourceKey == "solution_folder.<name-binding default>"` instead. The most common violation is copying a tenant identity value — the SDD's "Resource Identity" column, a `tasks describe --id` argument, or a registry `entityKey` — directly into `resourceKey` instead of constructing the composite string. `uip maestro case validate` does not catch this: it silently produces an unresolvable process reference that only faults at `case debug`. **Non-interactive repair:** recompute the correct `resourceKey` from the pair's own `default` fields and rewrite both bindings in the shared pair (a pair's two `resourceKey` values must stay identical), then re-run Check 7 to resync `bindings_v2.json`. Re-scan `bindings[]` after repair; halt before Phase 4 if any pair still fails after one repair pass.
- **Check 12 — Connector node resolution completeness** — Checks 9 and 11 exempt connector nodes; this check covers them. Read `tasks/registry-resolved.json` and `caseplan.json`. Enumerate every **connector node**: tasks typed `wait-for-connector` / `execute-connector-activity`, the case-level `Intsvc.EventTrigger` node, and every `wait-for-connector` rule across all 4 condition scopes (stage-entry / stage-exit / task-entry, plus case-exit under `metadata.caseExitRules`). For each whose registry entry has a **non-null `selected`** — i.e. the connector resolved in planning — verify its connector block (`data` for a task, `data.inputs` for a trigger node, `uipath` for a rule):
  1. `context` is present and non-empty. A block carrying only `serviceType` + `typeId` + `connectionId` is the Phase 2 / `case spec`-failed shape ([connector-trigger/impl-json.md § Graceful degradation](plugins/tasks/connector-trigger/impl-json.md#graceful-degradation)) and is a **failure** here — the spec call succeeded, so the populated `caseShape` must be spliced in.
  2. `context[name="connectorKey"].value` equals `selected.connectorKey`, and a `context[name="connection"]` entry exists whose `value` is `=bindings.<id>`.
  3. No `"placeholder"` values anywhere in `context` (legal only for a genuinely unresolved connector, which by definition has `selected: null`), and no residual `{{CONN_BINDING_ID}}` / `{{FOLDER_BINDING_ID}}` / `{{TRIGGER_REGISTRATION_KEY}}` token anywhere in the node.
  4. Every `=bindings.<id>` referenced by the block resolves to a complete entry in top-level `caseplan.json.bindings[]` (ConnectionId + FolderKey, the latter omitted only when `spec.connection.folderKey` was null).
  5. The node's spec-cache artifact exists — `tasks/spec-cache.<elementId>.json` for tasks and rules, or this trigger's entry in `tasks/trigger-spec-cache.json` for the case-level event trigger — and its cached `Context` matches the written `context` modulo the placeholder substitutions in (3) and the key re-casing in [connector-trigger-impl.md § Normalize key casing](connector-trigger-impl.md#normalize-key-casing-pascalcase--camelcase). A mismatch means the context was composed from agent memory rather than spliced — forbidden per [connector-trigger-impl.md § Step 4](connector-trigger-impl.md#step-4--substitute-placeholders-in-caseshapecontext).

  **Non-interactive repair:** re-run `case spec --type trigger` (or `--type activity`) for the failing node, persist the response to its spec-cache file, splice `context` / `inputs` / `outputs` verbatim per [connector-trigger-impl.md § Step 4](connector-trigger-impl.md#step-4--substitute-placeholders-in-caseshapecontext) and [§ Step 5](connector-trigger-impl.md#step-5--mint-var--id--elementid-on-inputs-and-outputs), append the missing root bindings per [§ Root-level bindings](connector-trigger-impl.md#root-level-bindings), then re-run Check 7 to resync `bindings_v2.json`. Re-scan after repair; halt before Phase 4 if any resolved connector node still fails after one repair pass. If `case spec` itself fails on the retry, keep the degraded shape, log it under `## Open Items for User` as **"connector node <name> is not runnable — `context` unresolved"**, and report it — do not silently emit it as complete. `uip maestro case validate` success does not satisfy this check: it reports `Valid` for a connector task with an empty `context` and no root bindings.

- **Check 13 — Rule selector integrity (task and stage references)** — Enumerate every rule across all 4 condition scopes (stage-entry / stage-exit / task-entry, plus case-exit under `metadata.caseExitRules`) whose rule type requires a task selector (`selected-tasks-completed`). Each MUST carry a non-empty `selectedTasksIds` array in which every id resolves to a task in the owning stage, and each resolved task MUST have no `adhoc` entry rule. **Non-interactive repair:** resolve missing ids from the selector names in the SDD's condition row via `tasks/id-map.json` using EXACT SDD task display names (paraphrased or shortened names are the common miss — match the task's exact name, per the conditions plugins' selector contract); rewrite the rule, re-scan. If any resolved task is adhoc, stop and return to the plan: required routing cannot depend on optional user-launched work, and replacing the selector without redesigning that route is forbidden. Unresolvable after one pass → **AskUserQuestion** (name the intended task / repair the plan / continue with best-effort emit, logged under Open Items). Halt before Phase 4 while any selector is empty with no user decision or selects an adhoc task; build-with-best does not waive the adhoc restriction. `uip maestro case validate` reports empty selectors as `... has no task(s) selected` but does not enforce the adhoc restriction, so a clean validate is not evidence this check passed. **Stage references too:** in the same pass, every `exitToStageId` and every `selectedStageId` (`selected-stage-completed` / `selected-stage-exited`) MUST resolve to an existing `case-management:Stage` node `id`; repair identically, re-resolving the SDD row's exit-to-stage / selected-stage name through `tasks/id-map.json`.

- **Check 14 — Variable `default` encoding** — Scan `variables.inputs[]`, `variables.outputs[]`, and `variables.inputOutputs[]`. Every entry carrying a `default` MUST hold a **JSON string**, whatever the entry's `type`. An object or array `default` is **silently deleted** by the caseplan → BPMN converter (`bpmn-moddle.ts` keeps only primitive attributes), leaving the variable null at runtime; the first task bound to it fails with `AGENT_STARTUP.INPUT_VALIDATION_ERROR / <input> Field required`. Numbers and booleans survive serialization but violate the field's declared string type and are equally non-conforming.

  **Nothing upstream catches this.** `uip maestro case validate` returns `Valid`; the frontend's own Zod schema types the field `z.any()` and parses an object clean, so borrowing it as a gate does not work here. The enforcement point is [`global-vars/impl-json.md` § `default` encoding](plugins/variables/global-vars/impl-json.md#default-encoding-every-type-mandatory) and this check.

  **Non-interactive repair:** re-encode in place — `{"a":1}` → `"{\"a\":1}"`, `5` → `"5"`, `true` → `"true"` (lowercase JSON, not Python `True`), `{}` → `"{}"`. Do not drop the value and do not change the variable's `type`. Re-scan once; halt before Phase 4 if any non-string `default` remains.

- **Check 15 — Every task carries a non-empty entry rule** — Enumerate every task across `data.tasks` in every stage, all classes, with **no exemptions**: placeholder tasks (Step 9.1: they "integrate with the rest of the graph" via normal task-entry conditions) and connector tasks are included; a manually-triggered task still needs its own `adhoc` entry rule (SKILL.md Rule 6). Each task's top-level `entryConditions` MUST be a non-empty array whose first element has a non-empty `rules[][]`. **`uip maestro case validate`'s "Task has no entry rules" finding is a warning, not an error — a clean `Valid` result is not evidence this check passed.** An empty `entryConditions` means the runtime never tells that task to start; the task never runs, its stage's exit condition can never be satisfied, and `uip maestro case debug` hangs indefinitely rather than faulting — worse than most Step 12 findings since it surfaces only as a live-debug timeout, not a build-time error.
  **Non-interactive repair, in order:**
  1. Look up the task's `##### Task N.M` section in the SDD and reconstruct the condition object from its **Entry Condition** table, using the shapes in [`task-entry-conditions/impl-json.md § Rule Types`](plugins/conditions/task-entry-conditions/impl-json.md#rule-types). Do not substitute a `current-stage-entered` default when the SDD specifies something else (`runs-sequentially`, `adhoc`, `selected-tasks-completed`, `wait-for-connector`, `sla-status-change`) — use it only when the SDD specifies it.
  2. If the task has no **Entry Condition** table, fall back to its **Activation Mode** in the stage's Tasks table and derive the rule through the Activation-mode audit at Step 9.
  3. If NEITHER an Entry Condition table nor an Activation Mode is recorded for the task (no SDD in this build, or a brownfield edit predating one) — **AskUserQuestion**: (a) name the intended entry rule, (b) default to `current-stage-entered` (stage-start, parallel) and log an Open Item. **Option (c) "continue with best-effort emit" is not offered for this check** — an empty `entryConditions` is not a partial or degraded result, it is a task that can never execute, so the agent must pick (a) or (b).
  Re-scan every task after repair; halt before Phase 4 if any task's `entryConditions` is still empty after one repair pass. This check is the mandatory backstop for Step 10 (`plugins/conditions/task-entry-conditions/impl-json.md § Post-Write Verification` only confirms count-parity against the SDD, which is not a safety net when the write itself was skipped) — do not treat Step 10 having run as sufficient evidence this check passes.

**Build-with-best policy:** for any user pick of "continue with best-effort emit" on a Check 1, Check 2, Check 4, Check 5, or Check 13 AskUserQuestion, append a `## Open Items for User` entry to `tasks/build-issues.md` and proceed to Phase 4. Checks 14 and 15 have no best-effort escape — a deleted default or a task with no entry rule is not a partial result. AskUserQuestion is the surface; build-with-best is the escape. The skill conservatively emits what it has; Phase 4 validate stays green (structural validity is intact); runtime concerns are listed for pre-publish review.

**Reporting:** at end of Phase 4, count entries in the `## Open Items for User` section of `tasks/build-issues.md` (read the file after writing). If count > 0, the completion report MUST include a literal line of the form:

```
Open Items: <N> entry/entries — review tasks/build-issues.md § Open Items for User before publishing.
```

(Use `entry` for N == 1, `entries` otherwise.) Place this line above the per-stage / per-task summary in the completion report so it's not buried.

End of Phase 3 mutations. Proceed directly to Phase 4 — no hard stop between Phase 3 and Phase 4.

---

# Phase 4 — Validate (Steps 12 – 12.1)

Authoritative validation. Full contract — command, retry policy, AskUserQuestion options — in [phased-execution.md § Phase 4](phased-execution.md#phase-4--validate). This section is a bridge — do NOT duplicate contract here.

## Step 12 — Completeness gate, then full validate

**Run the completeness gate first — mandatory, read-only:**

```bash
python3 "<this skill's folder>/scripts/audit_caseplan.py" <SolutionDir>/<ProjectName>/caseplan.json --sdd sdd.md --registry tasks/registry-resolved.json
```

It diffs `caseplan.json` against every declaration in `sdd.md` and exits non-zero on any `MISSING IN CASEPLAN` finding. This is the backstop for the completeness principle: `uip maestro case validate` cannot see a stage, task, variable, condition, or SLA row that was simply never written, and it only *warns* about a task with no entry rules — which hangs `case debug` indefinitely rather than faulting.

On `AUDIT FAIL`, repair each MISSING finding with a targeted Edit and re-run; max 3 rounds, then **AskUserQuestion** with the remaining findings. `WARN:` lines (extra caseplan elements, placeholder tasks, surviving `<UNRESOLVED>` markers) do not block — carry them into the completion report's Open Items. Quote the final `AUDIT OK` line as evidence. If `python3` is unavailable, walk the SDD's six element classes against `caseplan.json` by hand and report that the gate could not run.

**Then run validate** per [phased-execution.md § Phase 4](phased-execution.md#phase-4--validate). On success: proceed to Step 12.1. On 3rd failure: hard-stop prompt per the same section.

## Step 12.1 — Summarize the issue log

The journal has been on disk since the first section boundary; this step does **not** create it. Flush any buffered issues from the final section, then read the journal back and write the grouped counts into the summary block per [`plugins/logging/impl-json.md` § Summary](plugins/logging/impl-json.md). Counts come from the file, not from reasoning — that is the point of flushing incrementally.

If `tasks/build-issues.md` is absent here, the incremental flush was skipped: reconstruct from on-disk artifacts and stamp the `NOTE:` line per [§ Recovery](plugins/logging/impl-json.md). A build carrying `<UNRESOLVED>` markers or placeholder tasks must not reach Phase 5 with no log.

On Phase 4 success → proceed to Phase 5.

---

# Phase 5 — Publish (Steps 13, 14)

Optional Studio Web upload. Full contract — report fields, prompt options, publish commands, pack/publish warning — in [phased-execution.md § Phase 5](phased-execution.md#phase-5--publish). This section is a bridge — do NOT duplicate contract here.

## Step 13 — Completion report + Publish prompt

Print report fields and run AskUserQuestion per [phased-execution.md § Phase 5](phased-execution.md#phase-5--publish). On `Publish to Studio Web` → Step 14. On `Skip to Debug` → Phase 6.

## Step 14 — Publish to Studio Web

Run `uip solution resources refresh` then `uip solution upload <SolutionDir> --output json --output-filter "{Status: Status, Action: Action, SolutionId: SolutionId, DesignerUrl: DesignerUrl}"` per [phased-execution.md § Publish notes](phased-execution.md#publish-notes) — the filter is mandatory or `DesignerUrl` is lost to response truncation. Print `DesignerUrl` and say whether `Action` was `Imported` or `Overwritten`, then proceed to Phase 6.

---

# Phase 6 — Debug (Steps 15, 15a)

Optional CLI debug run. Full contract — prompt options, debug command, safety warning, loop behavior — in [phased-execution.md § Phase 6](phased-execution.md#phase-6--debug). This section is a bridge — do NOT duplicate contract here.

## Step 15 — Debug prompt + session

Run AskUserQuestion + debug command per [phased-execution.md § Phase 6](phased-execution.md#phase-6--debug). On `Run debug session` → run `uip solution resources refresh` then `uip maestro case debug`, loop until the user picks `Continue to publish`. On `Continue to publish` → Phase 7. Never auto-run (Rule 12).

## Step 15a — Troubleshoot failed case

When a debug or process run fails, read **[troubleshooting-guide.md](troubleshooting-guide.md)**. Diagnostic priority: incidents → runtime variables → caseplan.json correlation → traces (last resort).

**Diagnose → fix → re-run loop.** After each diagnostic pass, classify root cause and act:

1. **Fixable in `caseplan.json`** (wrong binding, missing condition, malformed expression, incorrect input value): apply targeted fix via matching plugin's `impl-json.md`, re-run `uip maestro case validate`, then re-run Step 15 debug. If the case was already published in Phase 5, ask via **AskUserQuestion** with options — `Re-publish the fixed build`, `Skip re-publish`. On `Re-publish`, re-run Step 14 so Studio Web holds the fixed build (the re-upload overwrites any Studio Web edits made since publish); on `Skip re-publish`, leave Studio Web on the build it already has.
2. **Fixable outside `caseplan.json`** (missing/expired connection, unregistered task type, missing Orchestrator asset, permissions): halt agent edits. Report exact resource + remediation steps to user via **AskUserQuestion** with options — `Resource fixed, re-run debug`, `Abort`.
3. **Inconclusive** (no actionable cause): proceed to next round per retry policy.

> **Known by-design debug fault:** an inline-built api-workflow sibling's task failing with incident `170007` ("job's associated process could not be found") under `case debug` is expected — debug does not provision Api siblings (agent siblings do resolve). Do not spend troubleshoot rounds on it; runtime verification needs a full solution deploy, offered via AskUserQuestion per [phased-execution.md § Debug notes](phased-execution.md#debug-notes) (the contract owner).

**Retry policy.** Up to 3 troubleshoot → fix → debug rounds per failed run. Each round must add new context (different element ID, broader scope, fallback command) or apply different fix — do not repeat identical commands or re-apply same fix. Track round count.

**Per-round timeout.** If debug run exceeds 10 minutes wall-clock, treat round as inconclusive and advance to next round (counts toward 3-round limit). Advisory — do not hard-kill subprocess; classify by elapsed time and move on.

After 3rd inconclusive round (or 3rd debug failure post-fix), halt and ask user with **AskUserQuestion**. Report: instance ID, folder key, incident IDs/messages, faulting element ID, variable snapshot, what was tried each round. Options — `Provide additional context` (user supplies hints; run one more targeted round), `Pause for manual investigation`, `Abort`. Do not propose `caseplan.json` edits without confirmed cause.

---

# Phase 7 — Publish to Orchestrator (Step 16)

Optional `case pack` (BPMN recompile) + `solution pack` + `solution publish` to the tenant solution feed. Full contract — prompt options, publish commands, version bumping, failure handling — in [phased-execution.md § Phase 7](phased-execution.md#phase-7--publish-to-orchestrator). This section is a bridge — do NOT duplicate contract here.

## Step 16 — Publish to Orchestrator

Run AskUserQuestion per [phased-execution.md § Phase 7](phased-execution.md#phase-7--publish-to-orchestrator). On `Publish to Orchestrator` → run `uip solution resources refresh`, then `uip maestro case pack "<SolutionDir>/<ProjectName>" "<SolutionDir>/dist" --output json`, then `uip solution pack "<SolutionDir>" "<SolutionDir>/dist" --output json`, then `uip solution publish "<packagePath>" --wait --output json`. **Never skip `case pack`** — it compiles `caseplan.json` → `caseplan.json.bpmn`, and it runs on every pass regardless of which earlier phases were skipped. Publish the `solution pack` `.zip`, never the `case pack` `.nupkg`. Read `<packagePath>` from the `solution pack` response `Data.Packages` — never guess the filename. On `Done` → exit skill. Never auto-run (Rule 12).

Stops at publish — `uip solution deploy run` is out of scope.
<!-- END: implementation.md -->
