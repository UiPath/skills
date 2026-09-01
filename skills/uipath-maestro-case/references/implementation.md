# Phases 2–7 — Execution: tasks.md → caseplan.json

Execute the `tasks.md` plan, building `caseplan.json` via direct JSON edits per plugin. Validate, then optionally publish, debug, and publish to Orchestrator. Six phases: **Phase 2 Prototyping** → **Phase 3 Implementation** → **Phase 4 Validate** → **Phase 5 Publish** → **Phase 6 Debug** → **Phase 7 Publish to Orchestrator**.

> **Editing an existing case?** Targeted edits to an existing `caseplan.json` skip this execution pipeline — see [brownfield.md](brownfield.md).

> **Prerequisite:** [Phase 1 Planning](planning.md) produced `tasks.md`. Phase 1 auto-proceeds into execution (plan treated as approved) — it stops before Phase 2 only when the request explicitly asked for a plan-only / review-first run.
>
> **Input:** `tasks/tasks.md` — the complete handoff artifact.

> **Six phases follow planning.** Execution splits into **Phase 2 — Prototyping** (reviewable preview: structure, conditions, SLA/escalation, and connector-rule stubs), **Phase 3 — Implementation** (connector schemas, task values, and connector-rule upgrades), **Phase 4 — Validate** (authoritative validate + dump), **Phase 5 — Publish** (optional Studio Web upload), **Phase 6 — Debug** (optional CLI debug run), **Phase 7 — Publish to Orchestrator** (optional `case pack` + `solution pack` + `solution publish`). Hard stops gate Phase 2→3, Phase 4 retry exhaustion, Phase 5 entry, Phase 6 entry, and Phase 7 entry. Read [phased-execution.md](phased-execution.md) for full phase contracts, informational Phase 2 validate, hard-stop prompts, re-entry protocol, retry policy, and abort semantics. Step numbers are stable labels; follow the order stated by each phase.

## Per-plugin execution

Every plugin uses direct JSON writes via its `impl-json.md`. Cross-cutting mechanics (ID generation, Pre-flight Checklist, primitive ops, the canonical write contract) are in [case-editing-operations.md](case-editing-operations.md).

> **Read each `impl-json.md` once per plugin type, not per T-entry.** Group the section's T-entries by plugin, read that plugin's `impl-json.md` a single time, then execute every T-entry of that type from the one read (this is what the per-section batch write contract already assumes). Re-opening a plugin reference per T-entry is a read-budget defect — observed at up to 26 re-reads of one `impl-json.md` in a single build, each costing a full inference round-trip. After context compaction, re-read only the plugin for the section in progress.

**Per-section batched writes — mandatory.** Process `tasks.md` one **section** at a time (Phase 2: §4.2.1 vars, §4.3 triggers, §4.4 stages, §4.6 task-shapes, §4.8 SLA, §4.7 conditions; Phase 3: §9.7 connector schema, §9.8 I/O binding, §10.5 connector-rule upgrades):

1. **One Read** of `caseplan.json` at section entry.
2. **N targeted patches in sequence, one per T-entry** — however many the section holds. Skip the re-Read between siblings. Anchor each on the target node's unique `"id"`. Use the `Edit` tool, or a single-hunk `apply_patch` if your harness has no `Edit` ([tool table](case-editing-primitives.md#skeleton-then-edit--the-only-cadence-for-caseplanjson)). There is no whole-section-write branch: after the Step 7 skeleton, `caseplan.json` grows only by targeted patch.
3. **One validate** at section boundary.
4. **One issue-log flush** at the same boundary — append the section's buffered issues to `tasks/build-issues.md` per [`plugins/logging/impl-json.md` § Flush](plugins/logging/impl-json.md), then clear the buffer. The first flush creates the file; later flushes append to its Journal table. **Flush even when the section produced zero issues** — after the first section the file must exist, and its existence is what proves the log survived the build.

TaskUpdate items keyed by T-number are the audit trail — mark each `in_progress` before composing the entry's mutation, `completed` after the Edit returns success.

**Bundle status text with tool_use.** Any progress text emitted alongside writes MUST share the same assistant turn as the next tool_use (text block + tool_use block in one content array). Standalone text-only turns between Edits are forbidden — they each cost ~5s inference + full cache replay for no work. Cap inline status to ≤1 sentence / ~20 tokens. **Hard token cap:** any single text block >200 tokens (or >500 tokens for allow-listed exceptions — completion reports, AskUserQuestion preambles, validate result summaries) is a planning monologue, forbidden regardless of content. **Forbidden announcement verbs** at any length: text blocks starting with `Building`, `Composing`, `Writing`, `Drafting`, `Generating`, `Now I'll`, `Next:`, `Approach:`, `Strategy:`, `Plan:`, `Caveman push:`, `Big single Write:`, `Let me`, or any other narration of the imminent tool call. The tool_use input IS the announcement.

**Skeleton first, then targeted patches — never a whole-file Write of a populated plan.** Step 7 writes the stage skeleton (stage nodes with `id`, `data.label`, and empty `data.tasks` / condition arrays — a few KB). Every later mutation patches one node, anchored on its unique `"id"`: the `Edit` tool, or a single-hunk `apply_patch` where there is no `Edit` tool. Do not rewrite the file to add a section, to reconcile state, or to repair a validate error, and do not emit a patch whose hunk covers the whole file — that is a whole-file Write in patch form.

An Edit costs output tokens proportional to the change; a whole-file Write costs them proportional to the file. A populated plan reaches 90–120KB — a single Write of it is 23–30K output tokens, more than some harnesses emit in an entire run. That wall is what pushes agents into composing the JSON in a `python`/`node` heredoc and pasting stdout through Write: Rule 13 violated, transcript still looking clean. Skeleton-then-Edit removes the pressure that creates the shortcut. Build-assembler helper scripts (`/tmp/build-caseplan.js`, `python3 - <<'PY' … print(json.dumps(plan))`) stay forbidden regardless of placement or framing.

Full cadence: [case-editing-primitives.md § Skeleton-then-Edit](case-editing-primitives.md#skeleton-then-edit--the-only-cadence-for-caseplanjson).

For CLI-gated sections (§4.6 non-connector schema, §9.7 connector schema), use **gather-then-write**: run all CLI calls first, collect results in reasoning, then enter the Read → writes → validate batch.

Full contract — recovery, tool primitive selection (skeleton Write, then Edit only), audit trail, scope — in [case-editing-operations.md § Per-section batch write contract](case-editing-primitives.md#per-section-batch-write-contract--canonical). Phase 1 `tasks.md` building uses the same section-batched contract per [planning.md §4.0a](planning.md).

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

**The list is the phase's execution order and every item is mandatory, with or without a TodoWrite tool.** The failure mode is silent and tool-independent: the phase's *last* items get dropped — the sweeps and regenerations `uip maestro case validate` cannot check. Agents that track todos diligently drop them too, so treat the per-step verification commands as the safeguard, not the todo list.

1. Read the Phase 2 manifest (Step 5.9)
2. Scaffold solution + project + root case (Step 6)
3. Add triggers (Step 6.1)
4. Declare variables + arguments (Step 6.2)
5. Refresh entry-points.json input/output (Step 6.3)
6. Add stages (Step 7)
7. Write task shapes (Step 9)
8. Regenerate bindings_v2.json (Step 9.4)
9. Write SLA + escalation objects (Step 11)
10. Add conditions with connector-rule stubs (Step 10)
11. Preview validate + boundary (Step 11.9)

(No edge step — Rule 20; see Step 8.)

**Per-T-entry sub-items.** Inside each section, also seed one TodoWrite item per T-entry the section will Edit (e.g., `T04 stage "Intake"`, `T05 stage "Review"`). Mark each `in_progress` before composing the entry's mutation in reasoning, `completed` after the Edit returns success. These per-T-entry items are the audit trail — section-level Edits collapse the file diff, but the todo log preserves T-by-T progress for reviewers (per [case-editing-operations.md § Per-section batch write contract](case-editing-primitives.md#per-section-batch-write-contract--canonical)).

---

# Phase 2 — Prototyping (Steps 5.9 – 11.9)

Execution order: 5.9 → 6 → 6.1 → 6.2 → 6.3 → 7 → 9 → 9.4 → 11 → 10 → 11.9. Step numbers are stable labels; SLA objects run before conditions so `sla-status-change` can reference emitted IDs. The preview contains the complete case flow and SLA model; task values, connector task schemas, and final connector-rule configuration remain deferred. Full contract in [phased-execution.md § Phase 2](phased-execution.md#phase-2--prototyping).

## Step 5.9 — Phase 2 read manifest (mandatory, before any write)

Derive the complete list of references this build needs from `sdd.md`, then read every file on that list **before** Step 6. Do not defer a read to the step that consumes it. Deciding mid-build which plugin to open is how an entire task class gets skipped: the agent writes the stages it has shapes for, never works out that it also needed `tasks/<type>/impl-json.md`, and emits zero task nodes while `validate` still returns `Valid`.

**Step 1 — derive.** Derive from **`sdd.md`** — the approved design, and per Rule 2 the sole post-design input. Collect these four sets. Collect every one; do not drop a set because it looks small or familiar.

| Set | Where it lives in `sdd.md` |
|---|---|
| 1. Every distinct task `type` | the `Type` row of each `##### Task` block |
| 2. Every distinct trigger type | § Section 1, the case trigger declaration |
| 3. Every distinct condition scope | the Entry Condition / Exit Condition tables on each stage and task |
| 4. Whether any SLA or escalation exists | any SLA row on a stage or task |

The SDD is present from the first turn of the build and is what every later step is graded against, so the manifest is derivable before any other artifact exists.

**If `tasks/tasks.md` is present, read it too and take the union.** It is a convenience, never the authority: a plan can be stale, partial, or written after the artifact it was meant to drive. Where the two disagree, the SDD wins and the discrepancy goes in the completion report. **Do not stop or backtrack because `tasks.md` is missing** — a missing plan file never blocks Phase 2.

**Step 2 — build the manifest.** The read list is the fixed core plus one file per distinct value found in Step 1.

Fixed core — always on the manifest, every build, no exceptions:

- [`case-editing-primitives.md`](case-editing-primitives.md)
- [`plugins/case/impl-json.md`](plugins/case/impl-json.md)
- [`plugins/stages/impl-json.md`](plugins/stages/impl-json.md)
- [`plugins/variables/global-vars/impl-json.md`](plugins/variables/global-vars/impl-json.md)
- [`plugins/variables/bindings/impl-json.md`](plugins/variables/bindings/impl-json.md)
- [`plugins/logging/impl-json.md`](plugins/logging/impl-json.md)

Per distinct task `type` — the plan's `type` value is the schema name, not the plugin folder name. Map it through this table; two of the nine differ:

| SDD task `Type` | Add to manifest |
|---|---|
| `process` | [`plugins/tasks/process/impl-json.md`](plugins/tasks/process/impl-json.md) |
| `agent` | [`plugins/tasks/agent/impl-json.md`](plugins/tasks/agent/impl-json.md) |
| `rpa` | [`plugins/tasks/rpa/impl-json.md`](plugins/tasks/rpa/impl-json.md) |
| `action` | [`plugins/tasks/action/impl-json.md`](plugins/tasks/action/impl-json.md) |
| `api-workflow` | [`plugins/tasks/api-workflow/impl-json.md`](plugins/tasks/api-workflow/impl-json.md) |
| `case-management` | [`plugins/tasks/case-management/impl-json.md`](plugins/tasks/case-management/impl-json.md) |
| `execute-connector-activity` | [`plugins/tasks/connector-activity/impl-json.md`](plugins/tasks/connector-activity/impl-json.md) |
| `wait-for-connector` | [`plugins/tasks/connector-trigger/impl-json.md`](plugins/tasks/connector-trigger/impl-json.md) |
| `wait-for-timer` | [`plugins/tasks/wait-for-timer/impl-json.md`](plugins/tasks/wait-for-timer/impl-json.md) |

Per distinct trigger type, add `plugins/triggers/<manual|timer|event>/impl-json.md`. Per distinct condition scope, add `plugins/conditions/<stage-entry-conditions|stage-exit-conditions|task-entry-conditions|case-exit-conditions>/impl-json.md`. If §4.8 declares any SLA or escalation, add [`plugins/sla/impl-json.md`](plugins/sla/impl-json.md).

**Step 3 — read.** Read every manifest file in full, to its `<!-- END: … -->` marker, per Rule 24 of `SKILL.md`. Read them as one batch before Step 6; do not interleave manifest reads with writes. Read each file once — the per-plugin single-read rule above still applies, and the manifest is that single read.

**The manifest is a floor, never a ceiling.** It is the minimum set this build cannot be correct without. It is not the complete list of what you may need, and finishing it does not mean you are done reading. Whenever a step, a plugin, or an SDD row references a shape or procedure you have not read, read that file too — the manifest never overrides Rule 24. A build that reads only the manifest and nothing else has under-read.

**Exact paths, not directories.** Each manifest entry names one file. `planning.md` and `impl-json.md` are different documents with different content, and reading the sibling does NOT satisfy the entry: `plugins/variables/global-vars/planning.md` does not satisfy `plugins/variables/global-vars/impl-json.md`. Planning references describe what to decide; `impl-json.md` carries the JSON shape you are about to write. Check each entry off by its full path.

**Step 4 — gate.** Do not enter Step 6 until every file on the manifest has been read to its END marker in this session. Walk the manifest entry by entry and confirm each exact path was read; a near-miss (the directory's `planning.md`, a `grep` for one section, a read that stopped before the END marker) leaves that entry unread.

Two distinct build defects follow from a skipped entry, and `uip maestro case validate` catches neither:

1. A task `type` present in the SDD whose `impl-json.md` was never read — those task nodes come out missing or malformed, and `validate` returns `Valid` for a caseplan whose stages contain no tasks at all.
2. A fixed-core entry skipped because the plan "obviously" does not need it — `global-vars/impl-json.md` carries the formal-argument output shape, and skipping it silently produces formal outputs with a null `var`, which `validate` also passes.

The manifest is bounded by what the plan actually contains — it is not the full reference tree, and every file on it is needed.

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

For each trigger T-entry in `tasks.md §4.3`, open the matching plugin's `impl-json.md`:

- Manual / Timer / Event (resolved) → `plugins/triggers/<type>/impl-json.md` §3
- Event (UNRESOLVED) → [`plugins/triggers/event/impl-json.md` § Placeholder fallback](plugins/triggers/event/impl-json.md) — node still written; case stays reachable

Each plugin writes one node to `caseplan.json.nodes[]` and appends one entry to `entry-points.json.entryPoints[]` atomically. Capture every `TriggerId` for Step 6.2 — an In-arg's `elementId` resolves to `id-map[<sourceTriggers T-number>].id`, or the primary trigger (T02) when its `sourceTriggers` is blank.

## Step 6.2 — Declare global variables and arguments

For each variable/argument T-entry from `tasks.md §4.2.1`, write entries directly into `caseplan.json` per [`plugins/variables/global-vars/impl-json.md`](plugins/variables/global-vars/impl-json.md). This step populates top-level `variables` (inputs, outputs, inputOutputs) and trigger output mappings. Execute these before adding stages — downstream tasks and conditions reference variables via `=vars.<id>`.

## Step 6.3 — Refresh entry-points.json input/output

After Step 6.2, project the declared In/Out arguments onto every `entry-points.json` entry's `input`/`output` schema per [entry-points-sync.md](entry-points-sync.md). Triggers (Step 6.1) scaffold each entry with empty `input`/`output` because variables don't exist yet; this back-fills them. Prerequisites — all entries (Step 6.1) + all In/Out args (Step 6.2) — are complete here, and In/Out formal args never change in Phase 3, so the file is correct from the Phase-2 publish branch onward. Idempotent — re-run on regenerate. Verified by Step 12 Check 6.

## Step 7 — Add stages (the skeleton Write)

For each stage in `tasks.md §4.4`, execute per [`plugins/stages/impl-json.md`](plugins/stages/impl-json.md). **Capture the generated `StageId` for every stage** into the name → ID map (and into `id-map.json`) — downstream tasks, conditions, and SLA all reference it.

**This step is the one skeleton Write.** Emit every stage node with its `id`, `data.label`, and empty containers — `data.tasks: []`, empty condition arrays — plus `layout: {}` and `schema.edges: []`. Write nothing else: no task nodes, no conditions, no SLA objects, no bindings. Even for a large case this stays a few KB, so it is safe to emit in one call.

From here `caseplan.json` is **append-only by targeted patch** (`Edit`, or single-hunk `apply_patch`). Step 9 patches task nodes into each stage's `data.tasks`, Steps 10/11 patch conditions and SLA, and Phase 3 patches connector shapes and I/O values. Do not rewrite the whole file again at any point — see [case-editing-primitives.md § Skeleton-then-Edit](case-editing-primitives.md#skeleton-then-edit--the-only-cadence-for-caseplanjson).

`isRequired` from `tasks.md` is planning-only metadata; it is not written into the stage node. It is consumed by case-exit-conditions with `rule-type: required-stages-completed` (Step 10).

## Step 8 — (RETIRED — no edges)

No edge-building step (Rule 20) — stage transitions are entry/exit conditions, written in Phase 2 Step 10. Multi-trigger cases: add extra triggers via the trigger plugin (Step 6.1); any trigger entering the case activates the first stage's `case-entered` condition.

## Step 9 — Add tasks (Phase 2 shape, gather-then-write)

**Phase A — gather. This step is NOT optional, and "the SDD is the sole source of truth" does not excuse it.** Rule 2's SDD authority covers *design* — which tasks exist, what they do, how values flow. It does not cover *schema*: the resource's actual field names, types, and the generated output ids downstream references resolve through. Only the tenant knows those, and only `tasks describe` returns them.

The SDD says so itself: tasks that feed downstream purely by direct reference **self-declare their outputs** and carry no Outputs row. Those outputs exist nowhere in the SDD — an `Action` output referenced only as `vars.$xref('Stage','Task','Action')` is discoverable **only** here. Skip the gather and it is never minted, every `$xref` through it dangles, and the gate that depends on it silently never fires. Observed: three consecutive builds made **zero** `tasks describe` calls and produced, respectively, invented output ids, output ids copied from names, and no outputs at all.

**For each non-connector task in `tasks.md §4.6`, run `uip maestro case tasks describe --type <type> --id <entityKey> --output json` and collect the input schema in reasoning.** Connector tasks (`connector-activity`, `connector-trigger`) skip the gather — `case spec` defers to Phase 3 Step 9.7. Unresolved tasks skip too — they become placeholders per Step 9.1. **Inline-built siblings (agent / api-workflow, Rule 17 Create) also skip the gather** — they were resolved + bound in Phase 1 with I/O read from the sibling's on-disk `entry-points.json`; their `taskTypeId` is a local audit-only key with no tenant resource, so tenant `tasks describe` does not apply. See the per-type Built-inline notes: [`plugins/tasks/agent/impl-json.md`](plugins/tasks/agent/impl-json.md), [`plugins/tasks/api-workflow/impl-json.md`](plugins/tasks/api-workflow/impl-json.md).

**Phase B — batched write.** One Read of `caseplan.json`. Then one Edit per task in §4.6 order, appending the task node to its stage's `data.tasks` structure per the matching plugin's `impl-json.md` and the placement contract below. **Capture each `TaskId`** — Phase 2 conditions and Phase 3 cross-task references need it. Skip the re-Read between sibling Edits. One validate at section end.

Per-class shape inside each Edit:

| Task class | Phase 2 `data` content |
|---|---|
| Non-connector (`process`, `agent`, `rpa`, `action`, `api-workflow`, `case-management`, `wait-for-timer`) | Full `data.inputs[]` schema from the Phase A gather. Each input's `value` is `""`. Outputs populated per plugin. |
| Connector (`connector-activity`, `connector-trigger`) | `data.typeId` + `data.connectionId` set. `data.inputs` omitted. **Do NOT call `case spec` in Phase 2** — schema discovery happens in Phase 3. |
| Unresolved (any class) | Placeholder task per Step 9.1 — empty `data: {}` plus action-only extras. |

**Do NOT bind input `value` fields in Step 9.** All literals, expressions, and cross-task references written in Phase 3 Step 9.8 per [`plugins/variables/io-binding/impl-json.md`](plugins/variables/io-binding/impl-json.md).

On context-compaction mid-gather: re-Read `caseplan.json`, scan for §4.6 tasks not yet appended, re-run Phase A for those only.

**Task placement contract.** Placement is determined by `activation-mode` + `entry-rule` from `tasks.md`; `lane` is only the planned task-set index after the mode decision. If the values conflict, task mode wins and the completion report must mention the lane correction.

- `activation-mode: sequential` or `entry-rule: runs-sequentially` → append according to the planned task-set order. Strict chains use new single-task inner arrays in declaration order (`[[A], [B], [C]]`); `parallel-after-predecessor` siblings share the same later inner array (`[[A], [B, C], [D]]`).
- `activation-mode: adhoc`, `event-triggered`, `fan-in`, `conditional-gate`, or any standalone non-parallel task → append as its own single-task inner array.
- Only `activation-mode: parallel` or `parallel-after-predecessor` with an explicit same-lane intent and rationale may share an inner array (`[[A, B], [C]]` or `[[A], [B, C], [D]]`). This is the only case where appending to an existing `data.tasks[laneIndex][]` is valid.

**Parallel-after-predecessor guard.** If two or more independent tasks share the same immediate predecessor task or predecessor task set, write them into the same next inner array and keep `activation-mode: parallel-after-predecessor`; do not convert them into separate event-triggered tasks with duplicate `selected-tasks-completed("<previous>")` entry rules. Duplicate selected-task gates on the immediate predecessor are a planning defect to repair before write.

> **`validate` cannot catch a wrong grouping.** Strict-sequential and parallel-after-predecessor emit the same entry rule (`runs-sequentially`); only the `data.tasks` grouping differs. `uip maestro case validate` returns `Valid` for a strict chain, a shared set, a shared set at index 0, and even mixed entry rules inside one set (as of uip 1.198, 2026-08-02). Grouping is enforced only here — get it right at write time; a clean validate is not evidence it is correct.

**Pass `lane: <n>` on every task** only when required by the artifact contract. Default: increment per task within a stage starting at 0; lane is a `data.tasks` task-set index. A strict sequential chain is represented as consecutive single-task sets (`[[A], [B], [C]]`) plus `runs-sequentially` on each task. Reuse the same lane only for intentionally parallel siblings, including stage-start siblings (`[[A, B], [C]]`) and siblings after a predecessor (`[[A], [B, C], [D]]`). Sequencing comes from the task's `entryConditions` and the order of task sets in `data.tasks`, not from lane-sharing alone.

**Task envelope fields.** Write `isRequired` and `shouldRunOnlyOnce` from `tasks.md`. If `runOnlyOnce` is omitted, default `shouldRunOnlyOnce` to `false` to match frontend new-task behavior. Do not infer `true` from task type; re-entry semantics from the SDD are the source of truth.

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

## Step 11 — Write SLA and escalation objects (per-target Edit batch)

One Read of `caseplan.json` at Step 11 entry. Group `tasks.md §4.8` entries by target (root or stage). For each target, compose and write the complete `slaRules[]` array per [`plugins/sla/impl-json.md`](plugins/sla/impl-json.md).

Mint each stable `sla_` / `esc_` ID while composing its object, write the object and its `id-map.json` entry in the same section, and reject collisions before the Edit. An escalation-only target still receives the documented synthetic default SLA object. There is no separate ID-preallocation pass: Step 10 resolves `sla-status-change` references against the objects already present in `caseplan.json`, with `id-map.json` as a cross-check. One validate at section end.

## Step 10 — Add conditions (per (scope, target) Edit batch)

One Read of `caseplan.json` at Step 10 entry. Group `tasks.md §4.7` entries by `(scope, target)` pair: each pair becomes one Edit replacing the relevant conditions array on its target node.

| Scope | Target | Edit replaces |
|---|---|---|
| Stage entry | one stage | `nodes[stage].data.entryConditions` |
| Stage exit | one stage | `nodes[stage].data.exitConditions` |
| Task entry | one task | `data.entryConditions` on the task object |
| Case exit | root | `metadata.caseExitRules` |

Per-scope composition rules live in the matching plugin's `impl-json.md`. Skip the re-Read between sibling Edits; run one validate at section end.

For every `wait-for-connector` rule, write the canonical stub `uipath` from [`connector-trigger-impl.md § Placeholder fallback`](connector-trigger-impl.md#placeholder-fallback) in Phase 2 **even when its connector resolved in planning**. Do not call `case spec` and do not add Connection/Folder bindings here. Its T-entry's `id-map.json` value must include `{kind:"condition", id:"<conditionId>", ruleId:"<ruleId>", scope:"<scope>", targetId:"<containerId>"}` so Phase 3 can locate the exact stub without matching display text (`targetId` is the stage ID, task ID, or `root`; task-entry entries also retain `stageId`). Phase 3 Step 10.5 upgrades only `rule.uipath`; a truly unresolved connector keeps the same stub and is reported at completion.

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

---

**This file covers Phase 2 only.** Execution continues in:

- [implementation-phase-3.md](implementation-phase-3.md) — Phase 3 (Steps 9.6 – 11.5) and the Step 12 end-of-Phase-3 validator checks
- [implementation-phase-4-7.md](implementation-phase-4-7.md) — Phase 4 validate, Phase 5 publish, Phase 6 debug, Phase 7 Orchestrator

Read the file for the phase you are in, to its own END marker. Rule 24 applies per file.

<!-- END: implementation.md -->
