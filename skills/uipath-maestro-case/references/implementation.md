# Phases 2–6 — Execution: tasks.md → caseplan.json

Execute approved `tasks.md` plan, building `caseplan.json` via direct JSON edits per plugin. Validate, then optionally debug and publish. Five phases: **Phase 2 Prototyping** → **Phase 3 Implementation** → **Phase 4 Validate** → **Phase 5 Debug** → **Phase 6 Publish**.

> **Editing an existing case?** Targeted edits to an existing `caseplan.json` skip this execution pipeline — see [brownfield.md](brownfield.md).

> **Prerequisite:** User must have explicitly approved `tasks.md` from [Phase 1 Planning](planning.md) before starting.
>
> **Input:** `tasks/tasks.md` — the complete handoff artifact.

> **Five phases follow planning.** Execution splits into **Phase 2 — Prototyping** (skeleton build), **Phase 3 — Implementation** (detail build), **Phase 4 — Validate** (authoritative validate + dump), **Phase 5 — Debug** (optional CLI debug run), **Phase 6 — Publish** (optional Studio Web upload). Hard stops gate Phase 2→3, Phase 4 retry exhaustion, Phase 5 entry, and Phase 6 entry. Read [phased-execution.md](phased-execution.md) for full phase contracts, informational Phase 2 validate, hard-stop prompts, re-entry protocol, retry policy, and abort semantics. Step numbering below marks phase boundaries.

## Per-plugin execution

Every plugin uses direct JSON writes via its `impl-json.md`. Cross-cutting mechanics (ID generation, Pre-flight Checklist, primitive ops, the canonical write contract) are in [case-editing-operations.md](case-editing-operations.md).

**Greenfield stage-batched Edits — mandatory.** After T01, `caseplan.json` is mutated only with Edit. Gather schemas first, then use the owning stage as the write unit:

1. Phase 2: one stage-array Edit appends every complete stage plus all task shapes; split by complete stage only above 30KB.
2. Phase 3: one Edit replaces each complete stage with connector detail, task I/O, conditions, SLA, and resolved cross-references included.
3. One bounded root Edit finalizes case-level rules/SLA and accumulated bindings.
4. No Read between sibling stage Edits; validate only at the Phase 2 and Phase 3 boundaries.

Use one progress item per phase/stage pass. `tasks.md` and `id-map.json` provide the T-by-T audit; do not create TaskUpdate items per T-entry.

**Bundle status text with tool_use.** Any progress text emitted alongside writes MUST share the same assistant turn as the next tool_use (text block + tool_use block in one content array). Standalone text-only turns between Edits are forbidden — they each cost ~5s inference + full cache replay for no work. Cap inline status to ≤1 sentence / ~20 tokens. **Hard token cap:** any single text block >200 tokens (or >500 tokens for allow-listed exceptions — completion reports, AskUserQuestion preambles, validate result summaries) is a planning monologue, forbidden regardless of content. **Forbidden announcement verbs** at any length: text blocks starting with `Building`, `Composing`, `Writing`, `Drafting`, `Generating`, `Now I'll`, `Next:`, `Approach:`, `Strategy:`, `Plan:`, `Caveman push:`, `Big single Write:`, `Let me`, or any other narration of the imminent tool call. The tool_use input IS the announcement.

**Cap one stage Edit at ~30KB.** If one final stage exceeds that size, use at most two Edits for that stage: its full `data.tasks` slice, then its conditions/SLA slice. Do not split into per-task/per-condition writes. Build-assembler helper scripts remain forbidden.

For schema-gated data, use **cache-then-write**: consume `tasks/schema-cache.json`; gather an exact miss once and persist it before any stage Edit.

Full contract — mutation budget, recovery, size exception, and brownfield boundary — in [case-editing-operations.md § Greenfield stage-batched write contract](case-editing-operations.md#greenfield-stage-batched-write-contract--canonical). Schema request equality and cache consumption live in [schema-cache-guide.md](schema-cache-guide.md).

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

Before Step 6, seed TodoWrite with the phase-level items below. Mark each `in_progress` on entry, `completed` on exit. Replace any Phase 1 todos — do not append.

1. Scaffold solution + project + root case (Step 6)
2. Add root-owned triggers, variables, and entry-point shapes (Steps 6.1–6.3)
3. Append complete Phase 2 stages and task shapes (Steps 7–9)
4. Regenerate bindings_v2.json (Step 9.4)
5. Skeleton validate + hard stop (Step 9.5)

(No edge step — edges are retired; stage transitions are condition-driven and written in Phase 3 Step 10.)

Do not seed per-T-entry sub-items. The T-numbered plan and `id-map.json` are the durable element-level audit.

---

# Phase 2 — Prototyping (Steps 6 – 9.5)

Steps 6 through 9.5 build structural skeleton: solution, project, root case, global variables, stages, triggers, and tasks without value binding. Full contract in [phased-execution.md § Phase 2](phased-execution.md#phase-2--prototyping).

## Step 6 — Create the Case project structure

The case file must live inside a solution + project. The case plugin owns project scaffolding **and** the root caseplan write. Solution setup and project registration are the only CLI calls:

1. **Step 6.0 (CLI)** — `uip solution init <SolutionName>` — creates the solution directory + `.uipx`. **Idempotent w.r.t. a Phase 1 Create:** if the Rule 17 **Create** flow already scaffolded the solution in Phase 1 (per [registry-discovery.md § Create-on-Missing → 0 Prerequisite](registry-discovery.md#create-on-missing-build-and-rediscovery)), the `.uipx` already exists — **skip this call iff that exact `<SolutionDir>/<SolutionName>.uipx` is present** (same canonical name + working-root location — [plugins/case/planning.md § Naming](plugins/case/planning.md#project-structure-prerequisites)). Re-running `init` over an existing solution errors, and a differently-named or -located `init` would fork the solution.
2. **T01 (plugin)** — execute [`plugins/case/impl-json.md`](plugins/case/impl-json.md) in full:
   - § Scaffold writes 5 boilerplate files (`project.uiproj`, `operate.json`, `entry-points.json`, `bindings_v2.json`, `package-descriptor.json`) directly into `<SolutionDir>/<ProjectName>/`.
   - § Write caseplan.json writes the root skeleton (`root` + empty `nodes: []` + empty `edges: []`).
3. **Step 6.0b (CLI)** — `uip solution project add <AbsolutePathToProjectDir> <AbsolutePathToUipxFile> --output json` — registers the project in `.uipx.Projects[]`. **Both arguments MUST be absolute paths.** Relative form `uip solution project add <ProjectName> <SolutionName>.uipx` fails with `Failed to add project to solution` regardless of CWD. Runs after `project.uiproj` exists.

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

## Step 7 — Prepare owning-stage batches

For each stage in `tasks.md §4.4`, execute the composition rules in [`plugins/stages/impl-json.md`](plugins/stages/impl-json.md) and mint its `StageId`, but do not issue a stage-only Edit. Associate every §4.6 task with its owning stage, read its schema entry from `tasks/schema-cache.json`, and compose the complete Phase 2 stage node for Step 9.

`isRequired` from `tasks.md` is planning-only metadata; it is not written into the stage node. It is consumed later by case-exit-conditions with `rule-type: required-stages-completed` (Step 10).

## Step 8 — (RETIRED — no edges)

Edges are retired; there is no edge-building step. `schema.edges` stays `[]`. Stage transitions are expressed as entry/exit conditions, written in Phase 3 Step 10. The case start comes from the first stage's `case-entered` entry condition, not a Trigger→stage edge.

For multi-trigger cases, add the additional triggers via the appropriate trigger plugin (Step 6.1) — no edge wiring is needed; any trigger entering the case activates the first stage's `case-entered` condition.

## Step 9 — Append complete Phase 2 stages

All non-connector schemas were gathered in Phase 1 and live under each T-entry's `schema-cache-key`. Do not run `tasks describe` here. Connector tasks consume their resolved type/connection fields and defer populated `caseShape` consumption to Phase 3. Inline-built agent/API schemas are cached from their sibling `entry-points.json` rather than tenant CLI output.

Read `caseplan.json` once. Compose all complete stage nodes in stage order, already containing every owned task, and accumulate/deduplicate all non-connector root bindings. Replace the `schema.nodes` slice in one Edit while preserving existing triggers verbatim, then apply the complete Phase 2 root `bindings[]` slice in one Edit. **Capture every StageId and TaskId** in the same batch and update all `id-map.json` entries together. If the node replacement exceeds 30KB, use one Edit per complete stage. Do not issue separate stage-only, task-only, or per-binding Edits, and do not validate between split stage Edits.

Per-class shape inside each owning-stage Edit:

| Task class | Phase 2 `data` content |
|---|---|
| Non-connector (`process`, `agent`, `rpa`, `action`, `api-workflow`, `case-management`, `wait-for-timer`) | Full `data.inputs[]` schema from the cached `Nxx` response. Each input's `value` is `""`. Outputs populated per plugin. |
| Connector (`connector-activity`, `connector-trigger`) | `data.typeId` + `data.connectionId` set. `data.inputs` omitted. Do not call `case spec` during the stage pass. |
| Unresolved (any class) | Placeholder task per Step 9.1 — empty `data: {}` plus action-only extras. |

**Do NOT bind input `value` fields in Step 9.** All literals, expressions, and cross-task references written in Phase 3 Step 9.8 per [`plugins/variables/io-binding/impl-json.md`](plugins/variables/io-binding/impl-json.md).

On context compaction, re-Read `caseplan.json`, `tasks.md`, `id-map.json`, and `schema-cache.json`; if the single stage-array Edit was not applied, recompose it from cached state. If a size split was required, resume at the first stage not yet appended. Reuse cached responses.

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
2. **Re-read `schema-cache.json`.** Verify every schema key against its stored exact request before any mutation.
3. **Re-read `caseplan.json`** — rebuild name → ID maps from authoritative artifact. See [phased-execution.md § Re-entry protocol](phased-execution.md#re-entry-protocol) for which fields to index.
4. **Seed Phase 3 progress todos** with three items: gather missing configured connector responses; finalize stages; finalize root + sidecars. Do not add per-T sub-items.

Never trust in-memory maps from Phase 2 without re-reading `caseplan.json` — context may be compacted across hard stop.

## Step 9.7 — Complete the schema cache before mutation

For every resolved connector task, event trigger, and connector-bound condition rule, locate its exact populated request in `connectorShapes` using `connector-shape-key`.

- Cache hit with matching request: consume it; do not call CLI.
- Missing populated entry: execute that exact `case spec --input-details` once, persist its complete response, and attach the new key to every exact-match consumer.
- Reuse `connections.Kxx`; do not run `get-connection` again on a cache hit.
- Placeholder targets need no populated response.

Finish this gather pass before the first stage Edit. Do not substitute binding placeholders or mint consumer IDs in the shared cache; those remain per-consumer composition steps.

## Steps 9.8–11.5 — Compose and finalize owning stages

These steps are one two-pass operation, not four mutation sections. First precompute all generated input/output/rule IDs, the global output dedup pool, and every `$xref` target across tasks, triggers, and connector rules. Then compose each final stage from the authoritative Phase 2 node and issue one Edit replacing that stage.

For each task, apply [`plugins/variables/io-binding/impl-json.md`](plugins/variables/io-binding/impl-json.md):

1. Literals / expressions (`input = "<value>"`): write `<value>` to `input.value`.
2. Cross-task references (`input <- "Stage"."Task".output`): resolve source output's `var` field from the just-Read `caseplan.json`, then write `=vars.<var>` to the target input's `value`.

If a cross-task reference points to a task that does not exist in the re-read Phase 2 artifact, halt and report the invalid plan before mutation.

## Step 10 — Fold conditions into the owning stage

Group `tasks.md §4.7` entries by scope/target and compose them with the matching plugin. Stage-entry, stage-exit, and task-entry results are included in that stage's single final Edit; they are not written separately.

| Scope | Target | Composed field |
|---|---|---|
| Stage entry | one stage | `nodes[stage].data.entryConditions` |
| Stage exit | one stage | `nodes[stage].data.exitConditions` |
| Task entry | one task | `data.entryConditions` on the task object |
| Case exit | root | `metadata.caseExitRules` |

Per-scope composition rules live in the matching plugin's `impl-json.md`:

- Stage entry → [`plugins/conditions/stage-entry-conditions/impl-json.md`](plugins/conditions/stage-entry-conditions/impl-json.md)
- Stage exit → [`plugins/conditions/stage-exit-conditions/impl-json.md`](plugins/conditions/stage-exit-conditions/impl-json.md)
- Task entry → [`plugins/conditions/task-entry-conditions/impl-json.md`](plugins/conditions/task-entry-conditions/impl-json.md)
- Case exit → [`plugins/conditions/case-exit-conditions/impl-json.md`](plugins/conditions/case-exit-conditions/impl-json.md)

> **Connector-bound rules consume cache.** Their `uipath` blocks come from the matching `Cxx` response gathered in Step 9.7. Perform placeholder substitution and consumer-specific ID minting during stage composition. Accumulate Connection/Folder bindings for root finalization; do not issue a condition-only Edit or an extra schema call.

Case-exit conditions are root-owned. Hold their composed result for the single root finalization Edit.

## Step 11 — Fold SLA and escalation into the owning target

Group `tasks.md §4.8` entries by target. Include stage/task SLA in the owning stage's final Edit per [`plugins/sla/impl-json.md`](plugins/sla/impl-json.md). Hold case-level SLA for root finalization. Supports conditional rules, secondary-stage SLA, and multi-recipient rules without SLA-only Edits.

## Step 11.5 — Resolve in-expression markers before the stage Edit

After the precompute pass fixes every task/trigger/rule output ID and deduped `var`, replace every `vars.$xref('Stage','Task','output')` marker while composing its owning stage or root slice. Substitute bare `vars.<var>` inside the surrounding `=js:` expression. Do not run a later per-string Edit pass. An unresolved name triple is an error handled by Check 4 below.

After all stages are composed, Edit each complete stage once in stage order. Then issue one root-owned Edit containing case-exit conditions, case-level SLA, and all accumulated bindings. Populate the IS connection cache and regenerate `bindings_v2.json` once after this root finalization. Run no full validate until Phase 4.

## Step 12 — End-of-Phase-3 validator pass

> **Algorithm reference:** the per-check pseudocode + AskUserQuestion prompt templates + skill-response-per-pick details all live in [`plugins/variables/io-binding/impl-json.md § Binding Procedure`](plugins/variables/io-binding/impl-json.md#binding-procedure). This step is the orchestration hook; that doc is the algorithm. When in doubt, follow the impl-json doc.

After all value bindings (Step 9.8), conditions (Step 10), SLA (Step 11), and marker resolution (Step 11.5) are written, invoke the end-of-Phase-3 validator — Checks 1, 2, 3, 4, 5, 6.

- **Check 1** — Resolve every `=vars.X` reference against `variables.{inputs, inputOutputs}[].id`. Scan all task input `value` fields, entry/exit condition expressions (stage and task), case-exit and trigger rule expressions, SLA expressions, and `=js:` expressions anywhere they appear. On unresolved → **AskUserQuestion** offering: (a) name the intended variable, (b) remove the reference, (c) continue with best-effort emit (entry logged under Open Items, runtime returns undefined).
- **Check 2 — Out-arg producer presence** — For every formal Out-arg in `variables.outputs[]`, verify the producer/Default situation per [`io-binding/impl-json.md` § Check 2](plugins/variables/io-binding/impl-json.md):
  - **Has Default but no companion** → AskUserQuestion.
  - **No Default + producer declared in SDD on a Rule 17 placeholder task** (declared-but-unresolvable) → no prompt; silent log to `## Open Items for User` in `tasks/build-issues.md`. Rule 17 already prompted the author for this task.
  - **No Default + no producer declared anywhere (pure orphan)** → AskUserQuestion offering 4 options: (a) add producer task output, (b) add Default value, (c) recategorize as Variable / remove, (d) continue with best-effort emit (entry logged under Open Items).
- **Check 3** — Type mismatch between `=vars.X` reference and consumer slot → log WARN inline (non-blocking; string coercion is runtime-tolerant).
- **Check 4 — No surviving `$xref` markers** — Scan every string value in `caseplan.json` for the literal `$xref(`. Step 11.5 resolves all; any survivor means its name-triple failed (typo'd stage / task / output) — the same class of failure as a Check 1 unresolved `=vars.X`, so it gets the same interactive remediation. On unresolved → **AskUserQuestion** (present the outputs that DO exist on the named task as candidates): (a) name the intended source output — skill rewrites the triple, re-resolves, substitutes `vars.<var>`; (b) edit the SDD expression + re-run the Phase 1 dispatcher (when the output genuinely doesn't exist); (c) continue with best-effort emit (token left unsubstituted, entry logged under Open Items; `vars.$xref(...)` throws at runtime until fixed). Detail: [`io-binding/impl-json.md` § Check 4](plugins/variables/io-binding/impl-json.md).
- **Check 5 — Resolved-resource I/O completeness** — For each task with a persisted contract in `tasks/registry-resolved.json`, verify every **required** declared input has a bound `value` and every extract output `Field` exists in the resolved output contract. An upstream-output-fed input (`=vars.<var>` / resolved `$xref`) counts as bound with NO §1.5 row. On unbound-required-input or phantom-output-field → **AskUserQuestion**: (a) bind / re-point, (b) `<UNRESOLVED>`+review-item / drop row, (c) continue with best-effort emit (entry logged under Open Items; runtime null until fixed). Tasks with no contract (placeholder / `<UNRESOLVED>`) are skipped. Detail: [`io-binding/impl-json.md` § Check 5](plugins/variables/io-binding/impl-json.md#check-5--resolved-resource-io-completeness).
- **Check 6 — Entry-point schema parity** — Verify every `entry-points.json` entry's `input`/`output` matches the In/Out args projected at Step 6.3 (keys, type mapping, `required`, `file`/`jsonSchema` shapes), plus unique `filePath` fragments and no orphaned `inputs[].elementId`. **Non-interactive:** on mismatch re-run the Step 6.3 refresh once; if still divergent (or a uniqueness/orphan finding) log to `## Open Items for User` and continue. No AskUserQuestion. Algorithm: [`entry-points-sync.md § Check 6`](entry-points-sync.md#check-6--entry-point-schema-parity-step-12-validator).

**Build-with-best policy:** for any user pick of "continue with best-effort emit" on a Check 1, Check 2, Check 4, or Check 5 AskUserQuestion, append a `## Open Items for User` entry to `tasks/build-issues.md` and proceed to Phase 4. AskUserQuestion is the surface; build-with-best is the escape. The skill conservatively emits what it has; Phase 4 validate stays green (structural validity is intact); runtime concerns are listed for pre-publish review.

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

> **Known by-design debug fault:** an inline-built api-workflow sibling's task failing with incident `170007` ("job's associated process could not be found") under `case debug` is expected — debug does not provision Api siblings (agent siblings do resolve). Do not spend troubleshoot rounds on it; runtime verification needs a full solution deploy, offered via AskUserQuestion per [phased-execution.md § Debug notes](phased-execution.md#debug-notes) (the contract owner).

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
