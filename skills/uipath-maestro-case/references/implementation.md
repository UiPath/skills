# Phases 2–6 — Execution: tasks.md → caseplan.json

Execute the `tasks.md` plan, building `caseplan.json` via direct JSON edits per plugin. Validate, then optionally publish and debug. Five phases: **Phase 2 Prototyping** → **Phase 3 Implementation** → **Phase 4 Validate** → **Phase 5 Publish** → **Phase 6 Debug**.

> **Editing an existing case?** Targeted edits to an existing `caseplan.json` skip this execution pipeline — see [brownfield.md](brownfield.md).

> **Prerequisite:** [Phase 1 Planning](planning.md) produced `tasks.md`. Phase 1 auto-proceeds into execution (plan treated as approved) — it stops before Phase 2 only when the request explicitly asked for a plan-only / review-first run.
>
> **Input:** `tasks/tasks.md` — the complete handoff artifact.

> **Five phases follow planning.** Execution splits into **Phase 2 — Prototyping** (reviewable preview: structure, conditions, SLA/escalation, and connector-rule stubs), **Phase 3 — Implementation** (connector schemas, task values, and connector-rule upgrades), **Phase 4 — Validate** (authoritative validate + dump), **Phase 5 — Publish** (optional Studio Web upload), **Phase 6 — Debug** (optional CLI debug run). Read [phased-execution.md](phased-execution.md) for all phase boundaries, prompts, re-entry, retries, and aborts. Step numbers are stable labels; follow the order stated by each phase.

## Per-plugin execution

Every plugin uses direct JSON writes via its `impl-json.md`. Cross-cutting mechanics (ID generation, Pre-flight Checklist, primitive ops, the canonical write contract) are in [case-editing-operations.md](case-editing-operations.md).

**Per-section batched writes — mandatory.** Process `tasks.md` one **section** at a time (Phase 2: §4.2.1 vars, §4.3 triggers, §4.4 stages, §4.6 task-shapes, §4.8 SLA, §4.7 conditions; Phase 3: §9.7 connector schema, §9.8 I/O binding, §10.5 connector-rule upgrades):

1. **One Read** of `caseplan.json` at section entry.
2. **Writes sized to section** — pick by T-entry count:
   - **<10 T-entries** — N Edits in sequence, one per T-entry. Skip the re-Read between sibling Edits.
   - **≥10 T-entries** — single whole-section Edit or Write replacing the section's container (e.g., `schema.nodes`, a stage's `data.tasks`). Compose the complete post-section state in reasoning from the section-entry Read, then emit one write. Untouched siblings (other sections, root fields, unrelated nodes) MUST be copied verbatim — drop nothing.
3. **One validate** at section boundary.

TaskUpdate items keyed by T-number are the audit trail — mark each `in_progress` before composing the entry's mutation, `completed` after the write returns success. The audit trail stays T-by-T even when the file diff collapses to one whole-section write.

**Bundle status text with tool_use.** Any progress text emitted alongside writes MUST share the same assistant turn as the next tool_use (text block + tool_use block in one content array). Standalone text-only turns between Edits are forbidden — they each cost ~5s inference + full cache replay for no work. Cap inline status to ≤1 sentence / ~20 tokens. **Hard token cap:** any single text block >200 tokens (or >500 tokens for allow-listed exceptions — completion reports, AskUserQuestion preambles, validate result summaries) is a planning monologue, forbidden regardless of content. **Forbidden announcement verbs** at any length: text blocks starting with `Building`, `Composing`, `Writing`, `Drafting`, `Generating`, `Now I'll`, `Next:`, `Approach:`, `Strategy:`, `Plan:`, `Caveman push:`, `Big single Write:`, `Let me`, or any other narration of the imminent tool call. The tool_use input IS the announcement.

**Cap single Write at ~15K out tok / ~40KB.** When a section's whole-section Write would exceed this, keep the per-section cadence: root/nodes/vars and task shapes first, then Phase 2 SLA and conditions, then Phase 3 connector/value details. For cases with ≥40 tasks or ≥8 stages, NEVER emit the full populated caseplan.json in one Write. A single 15K-out-tok Write turn pays ~150s inference; smaller turns let validate gates catch field drops between phases. Build-assembler helper scripts (`/tmp/build-caseplan.js` etc.) are forbidden — they violate Rule 13 regardless of `/tmp` placement or framing.

For §4.6 non-connector schema, use **gather-then-write**: run its CLI calls first, collect those small schemas in reasoning, then enter the Read → writes → validate batch. Section §9.7 instead uses **cache-then-write**: after each target-local CLI call, immediately Write the complete response to that target's raw cache; only after the eligible caches exist may its mutation batch begin. Never collect a connector payload in reasoning.

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
4. Refresh entry-points.json input/output (Step 6.3)
5. Add stages (Step 7)
6. Write task shapes (Step 9)
7. Regenerate bindings_v2.json (Step 9.4)
8. Write SLA + escalation objects (Step 11)
9. Add conditions with connector-rule stubs (Step 10)
10. Preview validate + boundary (Step 11.9)

(No edge step — Rule 20; see Step 8.)

**Per-T-entry sub-items.** Inside each section, also seed one TodoWrite item per T-entry the section will Edit (e.g., `T04 stage "Intake"`, `T05 stage "Review"`). Mark each `in_progress` before composing the entry's mutation in reasoning, `completed` after the Edit returns success. These per-T-entry items are the audit trail — section-level Edits collapse the file diff, but the todo log preserves T-by-T progress for reviewers (per [case-editing-operations.md § Per-section batch write contract](case-editing-operations.md#per-section-batch-write-contract--canonical)).

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

For each trigger T-entry in `tasks.md §4.3`, open the matching plugin's `impl-json.md`:

- Manual / Timer → `plugins/triggers/<type>/impl-json.md`; Event (resolved) → [`plugins/triggers/event/impl-json.md`](plugins/triggers/event/impl-json.md) Phase 2 envelope only
- Event (UNRESOLVED) → [`plugins/triggers/event/impl-json.md` § Placeholder fallback](plugins/triggers/event/impl-json.md) — node still written; case stays reachable

Each plugin writes one node to `caseplan.json.nodes[]` and appends one entry to `entry-points.json.entryPoints[]` atomically. Capture every `TriggerId` for Step 6.2 — an In-arg's `elementId` resolves to `id-map[<sourceTriggers T-number>].id`, or the primary trigger (T02) when its `sourceTriggers` is blank. A resolved connector event is only scaffolded here; its own Phase 3 spec/cache/splice runs in Step 9.7.

## Step 6.2 — Declare global variables and arguments

For each variable/argument T-entry from `tasks.md §4.2.1`, write entries directly into `caseplan.json` per [`plugins/variables/global-vars/impl-json.md`](plugins/variables/global-vars/impl-json.md). This step populates top-level `variables` and spec-independent trigger argument bridges before stages are added. Defer only the connector-event spec-output dispatcher and its spec-dependent validation until Step 9.7 creates `tasks/trigger-spec-cache.json`; do not fabricate a sidecar in Phase 2.

## Step 6.3 — Refresh entry-points.json input/output

After Step 6.2, project the declared In/Out arguments onto every `entry-points.json` entry's `input`/`output` schema per [entry-points-sync.md](entry-points-sync.md). Triggers (Step 6.1) scaffold each entry with empty `input`/`output` because variables don't exist yet; this back-fills them. Prerequisites — all entries (Step 6.1) + all In/Out args (Step 6.2) — are complete here, and In/Out formal args never change in Phase 3, so the file is correct from the Phase-2 publish branch onward. Idempotent — re-run on regenerate. Verified by Step 12 Check 6.

## Step 7 — Add stages

For each stage in `tasks.md §4.4`, execute per [`plugins/stages/impl-json.md`](plugins/stages/impl-json.md). **Capture the generated `StageId` for every stage** into the name → ID map (and into `id-map.json`) — downstream tasks, conditions, and SLA all reference it.

`isRequired` from `tasks.md` is planning-only metadata; it is not written into the stage node. It is consumed by case-exit-conditions with `rule-type: required-stages-completed` (Step 10).

## Step 8 — (RETIRED — no edges)

No edge-building step (Rule 20) — stage transitions are entry/exit conditions, written in Phase 2 Step 10. Multi-trigger cases: add extra triggers via the trigger plugin (Step 6.1); any trigger entering the case activates the first stage's `case-entered` condition.

## Step 9 — Add tasks (Phase 2 shape, gather-then-write)

**Phase A — gather.** For each non-connector task in `tasks.md §4.6`, run `uip maestro case tasks describe --type <type> --id <entityKey> --output json` and collect the input schema in reasoning. Connector tasks (`connector-activity`, `connector-trigger`) skip the gather — `case spec` defers to Phase 3 Step 9.7. Unresolved tasks skip too — they become placeholders per Step 9.1. **Inline-built siblings (agent / api-workflow, Rule 17 Create) also skip the gather** — they were resolved + bound in Phase 1 with I/O read from the sibling's on-disk `entry-points.json`; their `taskTypeId` is a local audit-only key with no tenant resource, so tenant `tasks describe` does not apply. See the per-type Built-inline notes: [`plugins/tasks/agent/impl-json.md`](plugins/tasks/agent/impl-json.md), [`plugins/tasks/api-workflow/impl-json.md`](plugins/tasks/api-workflow/impl-json.md).

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

For every `wait-for-connector` rule, write the canonical stub `uipath` from [`connector-trigger-common.md § Placeholder fallback`](connector-trigger-common.md#placeholder-fallback) in Phase 2 **even when its connector resolved in planning**. Do not call `case spec` and do not add Connection/Folder bindings here. Its T-entry's `id-map.json` value must include `{kind:"condition", id:"<conditionId>", ruleId:"<ruleId>", scope:"<scope>", targetId:"<containerId>"}` so Phase 3 can locate the exact stub without matching display text (`targetId` is the stage ID, task ID, or `root`; task-entry entries also retain `stageId`). Phase 3 Step 10.5 upgrades only `rule.uipath`; a truly unresolved connector keeps the same stub and is reported at completion.

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

1. **Re-read `tasks.md`** — per Rule 7 of `SKILL.md`.
2. **Re-read `caseplan.json`** — rebuild name → ID maps from authoritative artifact. See [phased-execution.md § Re-entry protocol](phased-execution.md#re-entry-protocol) for which fields to index.
3. **Seed Phase 3 progress todos** — call TodoWrite with the section-level items below. Mark each `in_progress` on entry, `completed` on exit. Phase 2 todos (if any) are stale — replace, do not append.
   1. Configure connector event/task targets (Step 9.7)
   2. Bind task I/O values (Step 9.8)
   3. Upgrade resolved connector-bound condition rules (Step 10.5)
   4. Resolve in-expression `vars.$xref` markers (Step 11.5)

   Inside each section, also seed per-T-entry sub-items (one per T-entry that section will Edit). Mark each `in_progress` before composing the entry's mutation in reasoning, `completed` after the Edit returns success. Per-T-entry items are the audit trail under the per-section batched contract (per [case-editing-operations.md § Per-section batch write contract](case-editing-operations.md#per-section-batch-write-contract--canonical)).

Never trust in-memory maps from Phase 2 without re-reading `caseplan.json` — context may be compacted across hard stop.

## Step 9.7 — Connector event/task detail (raw-cache gather then splice)

Process resolved targets in this order: case-level connector events, connector activities, then in-stage connector waits. Skip target placeholders.

**Phase A — target-local cache.** For each target, follow its selected owner:

| Target | Owner |
|---|---|
| Event trigger | [`plugins/triggers/event/impl-json.md`](plugins/triggers/event/impl-json.md) + trigger [common](connector-trigger-common.md#phase-3-implementation--single-cli-call) |
| Connector activity | [`plugins/tasks/connector-activity/impl-json.md`](plugins/tasks/connector-activity/impl-json.md) |
| In-stage wait | [`plugins/tasks/connector-trigger/impl-json.md`](plugins/tasks/connector-trigger/impl-json.md) + trigger common |

Every target runs its own Phase 3 `get-connection` and `case spec --input-details --output json`. Immediately Write the complete unmodified response to `tasks/spec-cache.<elementId>.json` and record cache path + target identity. Do not reuse or substitute another target's response, and never keep this payload only in reasoning. After the selected owner's post-spec gate, also record whether the cache is eligible for enrichment or retained for audit only.

**Phase B — cache-derived mutation.** One Read of `caseplan.json` at section entry. For each successfully gated, enrichment-eligible target, Read its cache immediately before that target's Edit. Splice the complete `Data.CaseShape.Context`, `Inputs`, and `Outputs` subtrees required by its owner; recursively lower-case only the first character of object keys; then apply only mutations explicitly permitted by that owner: placeholder substitution, ID minting, output projection/deduplication, envelope placement, and the activity owner's multipart file-value binding. Preserve all other values, including JSON-string values. Append that target's root bindings and skip a caseplan re-Read between sibling Edits. Never splice a cache retained only for audit after placeholder fallback.

For every enrichment-eligible event target, derive its unminted `tasks/trigger-spec-cache.json[T<N>]` view from the raw cache. After all event entries exist, run only the global-variable owner's deferred connector-event spec-output dispatch and spec-dependent validation; merge outputs with Phase 2 argument bridges rather than replacing them.

**Phase C — sync + validate.** Populate the IS connection cache, regenerate `bindings_v2.json` once (including non-connector bindings from Step 9), and validate.

On context compaction, re-Read `caseplan.json` and the relevant raw cache. A populated target without its recorded full-response cache is not proof of a safe resume; rerun that target's spec and replace only its cache before continuing.

## Step 9.8 — Bind task input/output values (per-task Edit batch)

One Read of `caseplan.json` at Step 9.8 entry. Then **one Edit per non-connector task** replacing that task's full `data.inputs` array. Skip the re-Read between sibling Edits. Skip placeholders and both persisted connector task types (`execute-connector-activity`, `wait-for-connector`) entirely: their owners already passed resolved values through `case spec`, and replacing `data.inputs` would destroy CLI-authored sink forms.

Per-task composition (in reasoning, before that task's Edit) per [`plugins/variables/io-binding/impl-json.md`](plugins/variables/io-binding/impl-json.md):

1. Literals / expressions (`input = "<value>"`): write `<value>` to `input.value`.
2. Cross-task references (`input <- "Stage"."Task".output`): resolve the source output reference ID from the just-Read `caseplan.json` using [`io-binding/impl-json.md` § Output reference ID](plugins/variables/io-binding/impl-json.md#output-reference-id-authoritative), then write `=vars.<outputReferenceId>` to the target input's `value`.

If a cross-task reference points to a task that does not exist in the just-Read `caseplan.json`, halt — `tasks.md` ordering is wrong; report to the user.

One validate at section end.

## Step 10.5 — Upgrade connector-bound condition-rule stubs (gather-then-write)

Read `caseplan.json` and scan all four condition scopes for `wait-for-connector` rules whose `uipath.context` still contains the canonical `connectorKey: "placeholder"` and `operation: "placeholder"` entries. Match each rule to its `tasks.md` connector fields through its Phase 2 `id-map.json` entry.

For each matched rule whose connector resolved in planning, run the connector-trigger `case spec --type trigger --input-details` procedure, mint its output IDs/element IDs, and gather its root Connection/Folder bindings. Then Edit **only that rule's `uipath` block**. Preserve the enclosing condition array plus the rule's `id`, `rule`, `conditionExpression`, scope, and placement. Apply declared rule-output bindings after the real outputs exist.

Each rule runs its own target-local spec call and immediately Writes the complete unmodified response to `tasks/spec-cache.<ownerNodeId>-<ruleId>.json`. Only after the common required-field gate succeeds may that exact cache be Read and its complete PascalCase `Data.CaseShape.Context`, `Inputs`, and `Outputs` subtrees be normalized and spliced into `rule.uipath`; a cache retained for placeholder audit is never mutation input. No rule may reuse a sibling response.

If the connector is `<UNRESOLVED>`, `case spec` fails, or the required-field gate is declined, leave the stub unchanged, log it, and list it in the completion report. After all successful upgrades, populate the IS cache and regenerate `bindings_v2.json` once. Re-scan: every resolved rule must be free of `"placeholder"`; any remaining stub must map to a reported unresolved connector. Full procedure and scope-specific `elementId` rules: [`connector-trigger-common.md § Target: connector-bound condition rule`](connector-trigger-common.md#target-connector-bound-condition-rule).

## Step 11.5 — Resolve in-expression `vars.$xref` markers (whole-file pass)

Runs after bindings (9.8) and connector-rule upgrades (10.5), when every task / trigger / rule output is minted and deduped. Conditions and SLA were already written in Phase 2. Resolve every `vars.$xref('Stage','Task','output')` marker in `caseplan.json` in ONE pass: one Read, then Edit each string value holding a marker — resolve the source through the common output-reference-ID algorithm and substitute bare `vars.<outputReferenceId>` (no leading `=`; the marker already sits inside `=js:`). Sink-blind: covers composite input payloads, `conditionExpression`, SLA `expression`, computed `=` outputs, and connector body fields in one place. An unresolved name-triple or reference ID is an ERROR under Step 12 Check 4. Algorithm + pseudocode: [`plugins/variables/io-binding/impl-json.md § In-Expression Marker Resolution`](plugins/variables/io-binding/impl-json.md#in-expression-marker-resolution-step-115). One validate at section end.

## Step 12 — End-of-Phase-3 validator pass

After value bindings (Step 9.8), connector-rule upgrades (Step 10.5), and the whole-artifact marker pass (Step 11.5) are complete, Step 12 starts. Directly load both owners now:

- [End-of-Phase-3 Case Validation](case-validation-guide.md) for Checks 1–11 ordering, repair sequencing, halt/build-with-best policy, and reporting; and
- [I/O Binding Exit Validation](plugins/variables/io-binding/validation-guide.md) for the canonical Checks 1–5 algorithms.

Do not load either guide earlier, and do not rely on one guide to discover the other. Run Checks 1 through 11 in order; Phase 2 conditions and SLA remain in place. Follow the case guide's repair/recheck order and clear every blocking result before Phase 4.

End of Phase 3 mutations. Proceed directly to Phase 4 — no hard stop between Phase 3 and Phase 4.

---

# Phase 4 — Validate (Steps 12 – 12.1)

Authoritative validation. Full contract — command, retry policy, AskUserQuestion options — in [phased-execution.md § Phase 4](phased-execution.md#phase-4--validate). This section is a bridge — do NOT duplicate contract here.

## Step 12 — Full validate

Run validate per [phased-execution.md § Phase 4](phased-execution.md#phase-4--validate). On success: proceed to Step 12.1. On 3rd failure: hard-stop prompt per the same section.

## Step 12.1 — Dump issue log

Write issue list to `tasks/build-issues.md` per [`plugins/logging/impl-json.md`](plugins/logging/impl-json.md). On Phase 4 success → proceed to Phase 5.

---

# Phase 5 — Publish (Steps 13, 14)

Optional Studio Web upload. Full contract — report fields, prompt options, publish commands, pack/publish warning — in [phased-execution.md § Phase 5](phased-execution.md#phase-5--publish). This section is a bridge — do NOT duplicate contract here.

## Step 13 — Completion report + Publish prompt

Print report fields and run AskUserQuestion per [phased-execution.md § Phase 5](phased-execution.md#phase-5--publish). On `Publish to Studio Web` → Step 14. On `Skip to Debug` → Phase 6.

## Step 14 — Publish to Studio Web

Run `uip solution resources refresh` then `uip solution upload <SolutionDir> --output json --output-filter "{Status: Status, SolutionId: SolutionId, DesignerUrl: DesignerUrl}"` per [phased-execution.md § Publish notes](phased-execution.md#publish-notes) — the filter is mandatory or `DesignerUrl` is lost to response truncation. Print `DesignerUrl`, then proceed to Phase 6.

---

# Phase 6 — Debug (Steps 15, 15a)

Optional CLI debug run. Full contract — prompt options, debug command, safety warning, loop behavior — in [phased-execution.md § Phase 6](phased-execution.md#phase-6--debug). This section is a bridge — do NOT duplicate contract here.

## Step 15 — Debug prompt + session

Run AskUserQuestion + debug command per [phased-execution.md § Phase 6](phased-execution.md#phase-6--debug). On `Run debug session` → run `uip solution resources refresh` then `uip maestro case debug`, loop until `Done`. On `Done` → exit skill. Never auto-run (Rule 12).

## Step 15a — Troubleshoot failed case

When a debug or deployed Case run fails, read [troubleshooting-guide.md](troubleshooting-guide.md) directly. It owns diagnosis, classification, targeted repair, validate/debug retry, conditional re-publish, incident `170007`, round/timeout limits, and escalation; do not load it for successful execution.
