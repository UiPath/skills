# Phases 2–7 — Execution: sdd.md → caseplan.case

Build `caseplan.case` from `sdd.md` by direct per-plugin JSON edits, using `tasks/registry-resolved.json` only for tenant identities. Validate, optionally publish, debug, and publish to Orchestrator: **2 Prototyping**, **3 Implementation**, **4 Validate**, **5 Publish**, **6 Debug**, **7 Publish to Orchestrator**.

> Existing-case targeted edits skip this pipeline: see [brownfield.md](brownfield.md).
>
> **Prerequisite:** [Phase 1 Resolution](planning.md) produced `tasks/registry-resolved.json`; Phase 1 auto-proceeds unless explicitly told to stop before the build.
>
> **Inputs:** `sdd.md` is the sole source of structure, activation modes, entry rules, inputs, outputs, and rationale. `tasks/registry-resolved.json` supplies tenant identities only. Never author an intermediate plan.
>
> **Element classes, in order:** variables (Case Variables) → triggers (Case Triggers) → stages (Section 2 headings) → tasks (per-stage Tasks tables and `##### Task N.M` blocks) → conditions (Stage Entry / Stage Exit / Task Entry / Case Exit) → SLA (Case-Level, Stage, and Task SLA). Each class is one write section.
>
> **Completeness:** emit every SDD declaration 1-to-1. Never filter default-looking rows (`is-interrupting: false`, `runOnlyOnce: true`, `marks-stage-complete: true`), merge similar rows, or omit implicit/default items. Copy `**Description:**` word for word into element `description`; write `**Design Rationale:**` to `tasks/build-issues.md`. If rationale has no Description, put it in `description`; SLA rationale goes to `tasks/build-issues.md`. Ambiguous or unrecognized rows require **AskUserQuestion** with row content, ambiguity, and bounded options; never omit silently. `validate --strict --sdd sdd.md` enforces missing declarations as `STRICT_SDD_*` findings.
>
> Phase 2 previews structure, conditions, SLA/escalation, and connector-rule stubs; Phase 3 adds connector schemas, task values, and connector-rule upgrades; Phase 4 validates and dumps; Phase 5 optionally uploads to Studio Web; Phase 6 optionally debugs; Phase 7 optionally runs `case pack` + `solution pack` + `solution publish`. Hard stops gate Phase 2→3, Phase 4 retry exhaustion, and entry to Phases 5–7. Read [phased-execution.md](phased-execution.md) for phase contracts, informational validation, prompts, re-entry, retries, and aborts.

## Per-plugin execution

Use direct JSON writes via each plugin's `impl-json.md`. Cross-cutting ID generation, pre-flight, primitives, and write contract are in [case-editing-operations.md](case-editing-operations.md). Read each plugin `impl-json.md` once per plugin type per section; group rows by plugin and execute all rows from that read. After compaction, reread only the plugin for the section in progress.

For every section: (1) read `caseplan.case` once; (2) for `<10` elements emit N sequential Edits, one per element, with no sibling re-Read; for `≥10`, emit one whole-section Edit or Write replacing its container (for example `schema.nodes` or `data.tasks`) and copy untouched siblings verbatim; (3) validate once at the boundary; (4) flush the section buffer to `tasks/build-issues.md` per [`plugins/logging/impl-json.md` § Flush](plugins/logging/impl-json.md), then clear it. Flush even with zero issues; the first section creates the file and later sections append to its Journal table.

TaskUpdate items keyed by SDD element must be `in_progress` before mutation composition and `completed` after successful write, including whole-section writes. Bundle status text with the next `tool_use` in the same assistant turn; standalone text-only turns are forbidden. Inline status is ≤1 sentence / ~20 tokens; no text block may exceed 200 tokens (or 500 for completion reports, AskUserQuestion preambles, or validate summaries). Do not start status with `Building`, `Composing`, `Writing`, `Drafting`, `Generating`, `Now I'll`, `Next:`, `Approach:`, `Strategy:`, `Plan:`, `Caveman push:`, `Big single Write:`, `Let me`, or other imminent-call narration.

Cap a single Write at ~15K output tokens / ~40KB. If larger, write root/nodes/vars and task shapes, then Phase 2 SLA/conditions, then Phase 3 connector/value details. With ≥40 tasks or ≥8 stages, never emit the full populated caseplan in one Write. Build-assembler scripts such as `/tmp/build-caseplan.js` are forbidden under Rule 14. For CLI-gated sections (non-connector schema at Step 9 and connector schema at Step 9.7), gather all CLI results first, then Read → write batch → validate.

See [case-editing-operations.md § Per-section batch write contract](case-editing-operations.md#per-section-batch-write-contract--canonical) for recovery, primitive selection, audit trail, and scope. Phase 1 uses the same contract per [planning.md Step 4](planning.md). Per-node detail: root `plugins/case/impl-json.md`; stages `plugins/stages/impl-json.md`; tasks `plugins/tasks/<type>/impl-json.md`; triggers `plugins/triggers/<type>/impl-json.md`; conditions `plugins/conditions/<scope>/impl-json.md`; SLA `plugins/sla/impl-json.md`; global variables `plugins/variables/global-vars/impl-json.md`; I/O `plugins/variables/io-binding/impl-json.md`; logging `plugins/logging/impl-json.md`.

## Issue Log — Initialize Before Step 6

Before any build step, initialize the in-reasoning, per-section buffer (not a file or subprocess):

```text
issues = []
```

Plugins append during the section; flush at every boundary and clear. [`plugins/logging/impl-json.md`](plugins/logging/impl-json.md) defines format, severities, flush, and schema. Incremental flush bounds context-loss to one section.

## Seed Phase 2 progress todos — Before Step 6

Before Step 6, replace Phase 1 todos with TodoWrite items, marking each `in_progress` on entry and `completed` on exit:

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

There is no edge step (Rule 21; see Step 8). Also seed one per-element item per section, named for its SDD element, and update it around the mutation.

# Phase 2 — Prototyping (Steps 6 – 11.9)

Order: 6 → 6.1 → 6.2 → 6.3 → 7 → 9 → 9.4 → 11 → 10 → 11.9. SLA precedes conditions so `sla-status-change` can reference emitted IDs. See [phased-execution.md § Phase 2](phased-execution.md#phase-2--prototyping).

## Step 6 — Create the Case project structure

<!--skill-flavor:step-six-intro:start-->
The case must be inside a solution and project. Run `uip solution init <SolutionName>`; from inside the solution run `uip maestro case init <ProjectName> --output json`. The latter seeds the project and registers it in `.uipx`; the case plugin writes only unseeded scaffold files. `sdd convert` emits the root caseplan (SKILL.md Rule 4). Never use `uip maestro case cases add` or another case mutation command to create the root: execute the T01 direct-JSON recipe so metadata such as `intsvcActivityConfig` is emitted. If `case init` is unavailable, T01 writes the scaffold and Step 6.0b registers the project; see [`case-commands.md` § uip maestro case init](case-commands.md#uip-maestro-case-init).
<!--skill-flavor:step-six-intro:end-->

<!--skill-flavor:step-six-zero:start-->
1. **Step 6.0 (CLI):** run `uip solution init <SolutionName>`. If Rule 18 Create already produced the exact `<SolutionDir>/<SolutionName>.uipx` at the canonical working-root location, skip this call; otherwise do not rerun it over an existing solution or use a different name/location.
   - **Step 6.0a (CLI):** run `cd <SolutionDir>`, then `uip maestro case init <ProjectName> --output json`. Confirm `Data.SolutionRegistration.Status` is `Registered` or `AlreadyRegistered`. `cd` first: chaining after `uip solution init` runs outside the new solution and can create a second scaffold. Run this before `sdd convert` because `case init` refuses a non-empty directory (Rule 4).
<!--skill-flavor:step-six-zero:end-->
2. **T01:** execute [`plugins/case/impl-json.md`](plugins/case/impl-json.md) in full:
<!--skill-flavor:step-six-t01-scaffold:start-->
   - Inventory `<SolutionDir>/<ProjectName>/` and write only unseeded boilerplate: `project.uiproj`, `operate.json`, `entry-points.json`, `bindings_v2.json`, and `package-descriptor.json`; leave seeded files untouched.
<!--skill-flavor:step-six-t01-scaffold:end-->
   - Write the root skeleton: `root` plus empty `nodes: []` and `edges: []`.
<!--skill-flavor:step-six-zero-b:start-->
3. **Step 6.0b (CLI, fallback only):** run `uip solution projects add <AbsolutePathToProjectDir> <AbsolutePathToUipxFile> --output json` only if Step 6.0a reports `Skipped` or `Failed`, or `case init` was unavailable and T01 wrote the scaffold. Both arguments MUST be absolute; relative arguments fail with `Failed to add project to solution`. Run after `project.uiproj` exists.
<!--skill-flavor:step-six-zero-b:end-->
<!--skill-flavor:step-six-zero-c:start-->
4. **Step 6.0c:** verify exactly one `.uipx` exists under the working root at `<SolutionDir>/<SolutionName>.uipx`. For a stray manifest, read its project first; delete that solution only if it has no work, otherwise adopt it as `<SolutionDir>`. Validate cannot detect this because it reads only the supplied caseplan path.
<!--skill-flavor:step-six-zero-c:end-->

T01 emits no trigger. The trigger plugin adds the primary trigger at T02 and owns every `entry-points.json.entryPoints[]` insertion; the scaffold starts with `entryPoints[]` empty.

## Step 6.1 — Add triggers

For each Case Triggers row, open the matching plugin: Manual / Timer / resolved Event → `plugins/triggers/<type>/impl-json.md` §3; unresolved Event → [`plugins/triggers/event/impl-json.md` § Placeholder fallback](plugins/triggers/event/impl-json.md). Write one node and one `entry-points.json.entryPoints[]` entry atomically. Capture every `TriggerId` for Step 6.2; an In-arg `elementId` resolves to `id-map[<sourceTriggers T-number>].id`, or primary T02 when `sourceTriggers` is blank.

## Step 6.2 — Declare global variables and arguments

For every Case Variables row, write directly per [`plugins/variables/global-vars/impl-json.md`](plugins/variables/global-vars/impl-json.md), populating top-level `variables.inputs`, `outputs`, `inputOutputs`, and trigger output mappings. Do this before stages; downstream references use `=vars.<id>`.

## Step 6.3 — Refresh entry-points.json input/output

After Steps 6.1–6.2, project In/Out arguments onto every entry's `input`/`output` schema per [entry-points-sync.md](entry-points-sync.md). This back-fills trigger entries, is idempotent, and remains correct through Phase 3. Step 12 Check 6 verifies it. Always process variables → triggers → stages → tasks → conditions → SLA, in SDD order within each class; ordering has no execution semantics, while activation mode and entry rule do.

## Step 7 — Add stages

For every Section 2 stage heading, including `Secondary Stage`, execute [`plugins/stages/impl-json.md`](plugins/stages/impl-json.md). Capture each generated `StageId` in the name→ID map and `id-map.json`. Do not write SDD **Required for Case Completion** into the stage; Step 10 consumes it through case-exit `required-stages-completed` (`rule-type:` is planning syntax; JSON key is `rule`).

## Step 8 — (RETIRED — no edges)

Do not build edges (Rule 21); transitions use entry/exit conditions in Step 10. Add extra triggers through Step 6.1; any trigger entering the case activates the first stage's `case-entered` condition.

## Step 9 — Add tasks (Phase 2 shape, gather-then-write)

**Gather:** for each non-connector task run `uip maestro case tasks describe --type <type> --id <entityKey> --output json` and retain its schema in reasoning. Skip connector tasks (`connector-activity`, `connector-trigger`) until Step 9.7, unresolved tasks (placeholders), and inline-built agent / api-workflow / business-rule siblings from Rule 18 Create; their I/O came from sibling `entry-points.json`, and their local `taskTypeId` is audit-only. See [`plugins/tasks/agent/impl-json.md`](plugins/tasks/agent/impl-json.md), [`plugins/tasks/api-workflow/impl-json.md`](plugins/tasks/api-workflow/impl-json.md), and [`plugins/tasks/business-rule/impl-json.md`](plugins/tasks/business-rule/impl-json.md).

**Write:** read once, then one Edit per task in SDD order, appending to the correct stage `data.tasks`; capture each `TaskId`; validate once. Non-connectors (`process`, `agent`, `rpa`, `action`, `api-workflow`, `function`, `business-rule`, `case-management`, `wait-for-timer`) receive full gathered `data.inputs[]` with every `value` `""` and plugin-defined outputs. Connectors receive only `data.typeId` and `data.connectionId`, with `data.inputs` omitted; do not call `case spec`. Placeholders receive Step 9.1 shape. Do not bind values in Step 9; Step 9.8 does it. After compaction, reread and gather only tasks not yet appended.

Placement comes from Activation Mode plus Entry Condition, never existing `data.tasks` indexes. Audit these pairings: ordered work → `sequential` + `runs-sequentially` on every task, including first, unless SDD declares another legal rule; independent stage-start work → `parallel` + `current-stage-entered`; connector callback wait → `event-triggered` + usually `wait-for-connector`; user-launched optional work → `adhoc` + `adhoc` + `isRequired: false`; convergence/fan-in/decision/non-immediate dependency → `fan-in` or `conditional-gate` + `selected-tasks-completed`, naming selected tasks.

Preserve explicit `selected-tasks-completed` rows only after confirming every selector is a non-adhoc sibling in the same stage; repair invalid selectors before writing and never convert a valid gate to `sequential`.

`lane` is the zero-based `data.tasks` task-set index, never a label. Shared task-set members share one number; strict chains use consecutive single-task lanes (`[[A], [B], [C]]`); `parallel-after-predecessor` siblings share the next set (`[[A], [B, C], [D]]`). `sequential` / `runs-sequentially` append in planned order; `adhoc`, `event-triggered`, `fan-in`, `conditional-gate`, and standalone non-parallel tasks get their own inner array. Only `parallel` or `parallel-after-predecessor` with explicit same-lane intent and rationale may share an array (`[[A, B], [C]]`). If mode and lane conflict, mode wins and the completion report names the correction. If independent tasks share an immediate predecessor, place them together and retain `parallel-after-predecessor`; do not create duplicate predecessor `selected-tasks-completed` gates. `validate` cannot catch grouping errors, including mixed rules or lane 0; enforce grouping here. Pass `lane: <n>` only when required by the artifact contract; default increments per stage from 0.

Write `isRequired` and `shouldRunOnlyOnce` from the Task envelope (`Required`, `Run Only Once`). If `runOnlyOnce` is omitted, write `shouldRunOnlyOnce: false`; never infer true from type. Copy `**Description:**` exactly into `description`, never summarize.

### Step 9.1 — Placeholder tasks for unresolved resources

If `taskTypeId`, or connector `typeId` / `connectionId`, is `<UNRESOLVED: …>`, use [placeholder-tasks.md](placeholder-tasks.md) and the matching `plugins/tasks/<type>/planning.md` Unresolved Fallback. For every task class write directly per `plugins/tasks/<type>/impl-json.md`: `type`, `displayName`, `id`, `elementId`, `isRequired`, `data: {}`, and no `taskTypeId` / `connectionId` keys. Skip input binding. Copy intended wiring from `wiringNotes` in `tasks/registry-resolved.json` into the completion report. Task-entry and stage-exit selectors use the placeholder `TaskId`; cross-task bindings wait until the resource is attached.

## Step 9.4 — Regenerate bindings_v2.json (batch)

After Step 9, run `uip maestro case bindings sync "<caseplan.case path>" --output json` once. Never author `bindings_v2.json`; derive it from root `bindings[]` per [bindings-v2-sync.md](bindings-v2-sync.md). In the same Edit, write each resource task's root `bindings[]` entries and `data.name` / `data.folderPath` references `=bindings.<id>`; otherwise `STRICT_BINDINGS_ABSENT` or `STRICT_BINDINGS_REFERENCE_UNRESOLVED` occurs.

## Step 11 — Write SLA and escalation objects (per-target Edit batch)

Read once. Group Case-Level, Stage, and Task SLA rows by root/stage target; replace each target's complete `slaRules[]` per [`plugins/sla/impl-json.md`](plugins/sla/impl-json.md). Mint collision-free `sla_` / `esc_` IDs while composing and write each matching `id-map.json` entry in the same section. Escalation-only targets receive the documented synthetic default SLA. Do not preallocate IDs; Step 10 resolves `sla-status-change` against emitted objects. Validate once.

## Step 10 — Add conditions (per (scope, target) Edit batch)

Read once. Group rows by `(scope, target)` and replace:

| Scope | Target | Array |
|---|---|---|
| Stage entry | stage | `nodes[stage].data.entryConditions` |
| Stage exit | stage | `nodes[stage].data.exitConditions` |
| Task entry | task | task `data.entryConditions` |
| Case exit | root | `metadata.caseExitRules` |

Use matching condition plugins. Every object uses JSON key `"rule": "<value>"`, never `ruleType`; copy SDD Display Name verbatim into `displayName`, because `--sdd` joins by that name. A wrong discriminator yields `INVALID_RULE_DISCRIMINATOR`. For every `wait-for-connector`, write the canonical Phase 2 stub from [`connector-trigger-impl.md § Placeholder fallback`](connector-trigger-impl.md#placeholder-fallback), even when resolved; do not call `case spec` or add bindings. Its `id-map.json` value must be `{kind:"condition", id:"<conditionId>", ruleId:"<ruleId>", scope:"<scope>", targetId:"<containerId>"}`; task-entry entries also retain `stageId`. Phase 3 changes only `rule.uipath`; unresolved connectors retain the stub and are reported. Validate once.

## Step 11.9 — Preview validate + Phase 2 boundary

See [phased-execution.md § Phase 2 hard stop](phased-execution.md#phase-2-hard-stop) for summary, prompt, publish branch, cleanup, continue, and abort.

1. Run `uip maestro case validate "<caseplan.case path>" --skeleton-v2 --output json`.
2. Fall back once to `--skeleton` only when the parser names `--skeleton-v2` unknown/unsupported, typically `ErrorCode: "invalid_argument"` and exit code 3. Exit 3 alone is insufficient; genuine v2 case errors do not trigger fallback.
3. Print selected profile and error/warning counts, then execute Rule 12 boundary. Findings are advisory; legacy `--skeleton` checks structure only and its summary must say rules/SLA remain covered by Phase 4.

On either continue option, proceed to Step 9.6.

# Phase 3 — Implementation (Steps 9.6 – 11.5)

Order: 9.6 → 9.7 → 9.8 → 10.5 → 11.5 → 12. Close with `uip maestro case validate "<caseplan.case path>" --strict --sdd sdd.md --output json`; only `Profile: "strict"` with `Valid` closes Phase 3. See [phased-execution.md § Phase 3](phased-execution.md#phase-3--implementation).

## Step 9.6 — Phase 3 re-entry

Before mutation, reread task detail blocks and `tasks/registry-resolved.json`; reread `caseplan.case` and rebuild maps from the artifact per [phased-execution.md § Re-entry protocol](phased-execution.md#re-entry-protocol). Replace Phase 2 todos with:

1. Wire connector task schemas (Step 9.7)
2. Bind task I/O values (Step 9.8)
3. Upgrade resolved connector-bound condition rules (Step 10.5)
4. Resolve in-expression `vars.$xref` markers (Step 11.5)

Seed per-element items and update them around each mutation. Never trust Phase 2 in-memory maps.

## Step 9.7 — Connector task detail (gather-then-write)

1. Run `get-connection` (each task runs its own — never reuse).
2. Run `uip maestro case spec --type <activity|trigger> --activity-type-id <id> --connection-id <id> --input-details '<json>' --output json` per the plugin's `impl-json.md`.
   > **Connector tasks skip 3–5:** `uip maestro case splice <caseplan> --task-id <taskId> --spec tasks/spec-cache.<elementId>.json --connection-id <id>` (no `--folder-key`: splice takes it from the spec) does the substitution, the id minting, and the root bindings in one call ([connector-activity/impl-json.md § Step 5](plugins/tasks/connector-activity/impl-json.md)). The steps below apply to the event-trigger node and connector-bound rules.
3. Substitute `{{CONN_BINDING_ID}}` / `{{FOLDER_BINDING_ID}}` placeholders in `caseShape.context[*].value` with minted binding ids; mint `var` / `id` / `elementId` on `caseShape.inputs` / `outputs` per the plugin's uniqueness rule.

Hold shapes and root Connection/FolderKey bindings in reasoning; skip placeholders.

Read once, then Edit each task with `data.context = caseShape.context`, `data.inputs = caseShape.inputs`, and `data.outputs` from [`io-binding/impl-json.md` § Output Binding Shapes](plugins/variables/io-binding/impl-json.md#output-binding-shapes) plus SDD `->` / `=` rows; write matching root bindings. Do not copy `caseShape.outputs` unchanged: `->` reassigns connector outputs and `=` adds `custom: true` outputs. Populate IS connection cache per [bindings-v2-sync.md § Populate IS connection cache](bindings-v2-sync.md), run `uip maestro case bindings sync "<caseplan.case path>" --output json` once, then validate. After compaction reread and gather only connector tasks without `data.context`.

## Step 9.8 — Bind task input/output values (per-task Edit batch)

Read once; run one Edit per task replacing full `data.inputs`; skip placeholders and sibling re-Reads. First, for every non-placeholder resource task (`process`, `agent`, `rpa`, `action`, `api-workflow`, `function`, `business-rule`, `case-management`), save `uip maestro case tasks describe --type <taskType> --id <selected.identifier> --output json` and run `uip maestro case splice "<caseplan.case>" --task-id "<taskId>" --described "<that file>" --output json`. Use `selected.identifier`: action app `id`, others `entityKey` per `identifierField`; raw planner ledger uses `selected.entityKey`, or `selected.id` for action. Never hand-write a CLI-provided `type` or `_jsonSchema`.

Compose per [`plugins/variables/io-binding/impl-json.md`](plugins/variables/io-binding/impl-json.md): literal/expression `input = "<value>"` → `input.value = <value>`; cross-task `input <- "Stage"."Task".output` → resolve the source output reference ID from the just-read artifact using [`io-binding/impl-json.md § Output reference ID](plugins/variables/io-binding/impl-json.md#output-reference-id-authoritative), then write `=vars.<outputReferenceId>`. A `=js:` string's internal line break must be the two characters `\` and `n`; on disk JSON contains `\\n`, never a decoded line break. Missing producer in the just-read artifact is an error: halt and report the SDD ordering defect. Validate once.

## Step 10.5 — Upgrade connector-bound condition-rule stubs (gather-then-write)

Read and scan all four scopes for `wait-for-connector` rules whose `uipath.context` retains `connectorKey: "placeholder"` and `operation: "placeholder"`. Match through Phase 2 `id-map.json` to `tasks/registry-resolved.json`. For each resolved match, run connector-trigger `case spec --type trigger --input-details`, mint IDs, gather root Connection/Folder bindings, and Edit only that rule's `uipath`; preserve condition array, `id`, `rule`, `conditionExpression`, scope, and placement. Apply declared output bindings after outputs exist. If unresolved or spec fails, leave the stub, log it, and report it. Populate cache, run `uip maestro case bindings sync "<caseplan.case path>" --output json` once, then rescan. Resolved rules may not retain placeholders. See [`connector-trigger-impl.md § Target: connector-bound condition rule`](connector-trigger-impl.md#target-connector-bound-condition-rule).

## Step 11.5 — Resolve in-expression `vars.$xref` markers (whole-file pass)

After Steps 9.8 and 10.5, Read once and Edit every string containing `vars.$xref('Stage','Task','output')` in one pass, resolving through the common output-reference algorithm and substituting bare `vars.<outputReferenceId>` (no leading `=`). This covers composite inputs, `conditionExpression`, SLA `expression`, computed `=` outputs, and connector bodies. Unresolved triples/IDs are errors. See [`plugins/variables/io-binding/impl-json.md § In-Expression Marker Resolution`](plugins/variables/io-binding/impl-json.md#in-expression-marker-resolution-step-115). Validate once.

## Step 12 — End-of-Phase-3 validator pass

First run `uip maestro case validate "<caseplan.case path>" --strict --sdd sdd.md --output json`; unknown-option handling is [case-commands.md § Version guard](case-commands.md#version-guard----strict----sdd-require-cli-1202). Repair reported elements with targeted Edits, max 3 rounds, then AskUserQuestion with remaining codes. If `--strict` is rejected, run default and say so in the report. Use [`plugins/variables/io-binding/impl-json.md § Binding Procedure`](plugins/variables/io-binding/impl-json.md#binding-procedure) and [validator-codes.md](validator-codes.md); then run Checks 1–18.

- **Check 1:** Resolve every `=vars.X` against `variables.{inputs, inputOutputs}[].id` across all task values, stage/task entry/exit, case-exit, trigger, SLA, and `=js:` expressions. AskUserQuestion: name variable / remove reference / continue best-effort (log Open Item; runtime undefined).
- **Check 2:** For every `variables.outputs[]` formal Out-arg, verify producer/default per [`io-binding/impl-json.md` § Check 2](plugins/variables/io-binding/impl-json.md). Default without companion → ask. No default plus Rule 18 placeholder producer → silently log to `## Open Items for User`. Pure orphan → ask: add producer / add Default / recategorize or remove / best-effort with Open Item.
- **Check 3:** Reference/consumer type mismatch is WARN, non-blocking.
- **Check 4:** No `$xref(` may survive anywhere. On failure AskUserQuestion: name intended output and rewrite; edit SDD and rerun Phase 1; or best-effort leaving token and logging it. Candidates are outputs on the named task. See [`io-binding/impl-json.md` § Check 4](plugins/variables/io-binding/impl-json.md).
- **Check 5:** For every persisted non-placeholder registry contract, all required inputs have values and every extract `Field` exists. Upstream `=vars.<outputReferenceId>` counts without a §1.5 row. Ask: bind/re-point / `<UNRESOLVED>`+review-item/drop / best-effort with Open Item. See [`io-binding/impl-json.md` § Check 5](plugins/variables/io-binding/impl-json.md#check-5--resolved-resource-io-completeness).
- **Check 6:** Verify every entry-point `input`/`output` against Step 6.3, including keys, types, `required`, `file`/`jsonSchema`, unique `filePath` fragments, and no orphan `inputs[].elementId`. Refresh once; if still divergent, log Open Item and continue; no AskUserQuestion. See [`entry-points-sync.md § Check 6`](entry-points-sync.md#check-6--entry-point-schema-parity-step-12-validator).
- **Check 7:** Run `uip maestro case bindings sync "<caseplan.case path>" --output json`; `ResourceCount: 0` with `Result: Success` is valid. Then strict validate. `STRICT_BINDINGS_ABSENT` requires root bindings; `STRICT_BINDINGS_SIDECAR_STALE` requires sync. `ResourceCount` equals distinct `resourceKey` values and `ConnectionCount` distinct connection IDs; repair plan bindings, never sidecar.
- **Check 8:** Build one owner-keyed global uniqueness pool over root variables and every task, trigger, and condition-scope connector output, including unused `Error` and `response`. Apply [global uniqueness rule](plugins/variables/global-vars/impl-json.md#uniqueness-rule); suffix later producer on collision and update only its consumers, then rerun affected binding/marker steps. Halt if any generated `id` or `var` remains duplicated; validate success is insufficient.
- **Check 9:** Read registry, SDD, caseplan, and sidecar. Every non-null `selected` must locate its declared `(stage, task)`, with nonempty data; non-connectors must use `data.name` and `data.folderPath` as `=bindings.<id>` to complete root bindings. Selected resources never become placeholders. Repair only targeted; whole-file repair follows [`case-editing-operations.md § Per-section batch write contract`](case-editing-operations.md#per-section-batch-write-contract--canonical). Repeat Checks 7 and 9; do not proceed or downgrade to Open Item.
- **Check 10:** Every `variables.inputs[]`/`outputs[]` `id` matches `^v[A-Za-z0-9]{8}$` per [`global-vars/impl-json.md` § Formal-arg slot ID format](plugins/variables/global-vars/impl-json.md#formal-arg-slot-id-format). Non-interactively mint a deduplicated replacement, update only formal slot `id`; for In-args update bound trigger bridge `source == "=vars.<old id>"` to new source, unless trigger placeholder. Leave `name`, `var`, and `inputOutputs[]` companion ID unchanged. Halt if any remains invalid.
- **Check 11:** For each non-connector task binding pair, `resourceKey` equals the pair's own defaults: normally `"<folderPath-binding default>.<name-binding default>"`; inline sibling with empty folder default uses `"solution_folder.<name-binding default>"`. Connector pairs and sibling `solution_folder.<Name>` are outside this pair check. Never copy tenant identity, SDD Resource Identity, `tasks describe --id`, or registry `entityKey`. Recompute both pair entries, rerun Check 7, and halt if still wrong. `CASE_MGMT_BINDING_KEY_MISMATCH` is the machine half; validate alone otherwise misses it.
- **Check 12:** Enumerate connector tasks typed `wait-for-connector` / `execute-connector-activity` / `external-agent` / `external-workflow`, case-level `Intsvc.EventTrigger`, and all `wait-for-connector` rules. For each non-null `selected`, require nonempty context; `connectorKey` equal selected value; `context[name="connection"].value = =bindings.<id>`; no `"placeholder"` or `{{CONN_BINDING_ID}}` / `{{FOLDER_BINDING_ID}}` / `{{TRIGGER_REGISTRATION_KEY}}`; complete root bindings; and matching `tasks/spec-cache.<elementId>.json` or `tasks/trigger-spec-cache.json` context modulo substitutions. Re-run `case spec --type trigger` or `--type activity`, persist cache, splice tasks, or write trigger/rule context/inputs/outputs per [connector-trigger-impl.md § Step 4](connector-trigger-impl.md#step-4--substitute-placeholders-in-caseshapecontext), [§ Step 5](connector-trigger-impl.md#step-5--mint-var--id--elementid-on-inputs-and-outputs), and [§ Root-level bindings](connector-trigger-impl.md#root-level-bindings); rerun Check 7. If retry fails, retain degraded shape, log exactly **"connector node <name> is not runnable — `context` unresolved"**, and report it; halt if resolved node still fails after one repair. `uip maestro case validate` success does not satisfy this check (it reports `Valid` for an empty `context` with no root bindings).
- **Check 13:** Every `selected-tasks-completed` rule has nonempty `selectedTasksIds`, each resolves in the owning stage, and none is adhoc. Repair missing IDs from exact SDD display names via `tasks/id-map.json`; unresolved after one pass → AskUserQuestion: intended task / repair plan / best-effort Open Item. If any resolved task is adhoc, stop and return to the plan: required routing cannot depend on optional user-launched work, and replacing the selector without redesigning that route is forbidden. Halt before Phase 4 while any selector is empty with no user decision or selects an adhoc task; build-with-best does not waive the adhoc restriction. Also resolve every `exitToStageId` and `selectedStageIds` to a `case-management:Stage` node, using the same method.
- **Check 14:** Every `default` in `variables.inputs[]`, `outputs[]`, and `inputOutputs[]` is a JSON string regardless of type. Re-encode objects/arrays/numbers/booleans in place (`{"a":1}` → `"{\"a\":1}"`, `5` → `"5"`, `true` → `"true"`, `{}` → `"{}"`); do not drop or change type. Halt before Phase 4 if any non-string `default` remains. See [`global-vars/impl-json.md` § `default` encoding](plugins/variables/global-vars/impl-json.md#default-encoding-every-type-mandatory).
- **Check 15:** Every task in every stage, including placeholders and connectors, has nonempty top-level `entryConditions`, whose first element has nonempty `rules[][]`. Repair from SDD Entry Condition using [`task-entry-conditions/impl-json.md § Rule Types`](plugins/conditions/task-entry-conditions/impl-json.md#rule-types); if absent use Activation Mode and Step 9 audit; if both absent AskUserQuestion: name rule or default `current-stage-entered` and log Open Item. Never substitute a `current-stage-entered` default when the SDD specifies something else. No best-effort option; halt before Phase 4 if still empty. This check is the mandatory backstop for Step 10 — do not treat Step 10 having run as sufficient evidence this check passes. This includes adhoc tasks and is not satisfied by validate's warning.
- **Check 16:** Condition `displayName` is a case-wide, trimmed, case-sensitive unique pool across all four scopes. Validate enforces `CASE_MGMT_RULE_NAME_DUPLICATE`; accepted frontend-generated defaults may repeat (for example `Entry rule 1`, `Tasks completed rule`, `Entry from '<stage>'`). A condition declared once in SDD must retain exact spelling; strict audit reports `STRICT_SDD_CONDITION_RENAMED`. Repeated non-default SDD names require AskUserQuestion; non-interactively prefix each with stage/task and log every rename. Do not decide from memory or a list: run `validate` and repair only what it reports; decide per name, never per case. Do not empty arrays to hide collisions. Non-interactively renumber duplicate default-pattern `Entry rule <n>` / `Completion rule <n>` / `Exit rule <n>` case-wide by label kind using highest+1. See [case-schema.md § Condition name uniqueness](case-schema.md#condition-name-uniqueness).
- **Check 17:** Each `variables.inputs[]` bound trigger must have `data.inputs.outputs[]` bridge with matching `name` and `var`, exact `source: "=vars.<the entry's id>"`, and no `value`; skip placeholder triggers. Create `data.inputs = {"outputs": []}` on bare manual triggers per [`triggers/manual/impl-json.md`](plugins/triggers/manual/impl-json.md). Leave name/var/type, formal slot, and companion unchanged; halt if still missing.
- **Check 18:** Every task whose SDD block has `**Description:**`, or `**Design Rationale:**` without Description, must carry that line word-for-word in `description`. Strict warning `STRICT_SDD_TASK_DESCRIPTION_MISSING` is not proof of success. Targeted-copy missing prose and rerun strict validate; otherwise record affected tasks and reason in `build-issues.md`.

For best-effort picks on Checks 1, 2, 4, 5, or 13, append `## Open Items for User` and proceed. Checks 14 and 15 have no best-effort escape. At Phase 4 end reread `tasks/build-issues.md` and count `## Open Items for User` entries. If count > 0, the completion report MUST include a literal line of the form:

```text
Open Items: <N> entry/entries — review tasks/build-issues.md § Open Items for User before publishing.
```

Use `entry` only for N == 1 and place the line above the stage/task summary. End Phase 3 mutations and proceed directly to Phase 4.

# Phase 4 — Validate (Steps 12 – 12.1)

See [phased-execution.md § Phase 4](phased-execution.md#phase-4--validate) for command, retry, and prompts.

## Step 12 — Strict validate with the SDD audit

**Run `uip maestro case validate "<caseplan.case path>" --strict --sdd sdd.md --output json` — mandatory.** `--sdd` implies `--strict` and audits every SDD stage, task, type, condition row, SLA, trigger, and variable. `STRICT_SDD_FILE_NOT_FOUND` means fix the path; do not remove `--sdd`. Only an `invalid_argument` identifying `--strict` or `--sdd` permits the [case-commands.md § Version guard](case-commands.md#version-guard----strict----sdd-require-cli-1202); log it. Repair errors with targeted Edits, max 3 rounds, then AskUserQuestion per [phased-execution.md § Phase 4](phased-execution.md#phase-4--validate). On `Status: "Valid"` and `Profile: "strict"`, run Step 12.1. If `--sdd` is rejected, run `--strict`, manually audit all six classes, and report the fallback. Carry unresolved placeholders and extra elements into Open Items.

## Step 12.1 — Summarize the issue log

Flush the final buffer, read the journal, and write grouped counts per [`plugins/logging/impl-json.md` § Summary](plugins/logging/impl-json.md). Counts must come from disk. If absent, reconstruct from artifacts and stamp `NOTE:` per [§ Recovery](plugins/logging/impl-json.md); unresolved markers/placeholders may not reach Phase 5 without a log. Then proceed to Phase 5.

# Phase 5 — Publish (Steps 13, 14)

See [phased-execution.md § Phase 5](phased-execution.md#phase-5--publish).

## Step 13 — Completion report + Publish prompt

Print required report fields and run AskUserQuestion. `Publish to Studio Web` → Step 14; `Skip to Debug` → Phase 6.

## Step 14 — Publish to Studio Web

Run `uip solution resources refresh`, then `uip solution upload <SolutionDir> --output json --output-filter "{Status: Status, Action: Action, SolutionId: SolutionId, DesignerUrl: DesignerUrl}"` per [phased-execution.md § Publish notes](phased-execution.md#publish-notes). The filter is mandatory. Print `DesignerUrl`, state whether `Action` is `Imported` or `Overwritten`, then proceed to Phase 6.

# Phase 6 — Debug (Steps 15, 15a)

See [phased-execution.md § Phase 6](phased-execution.md#phase-6--debug).

## Step 15 — Debug prompt + session

Run AskUserQuestion and the debug command per the phase contract. On `Run debug session`, run `uip solution resources refresh` and `uip maestro case debug`; loop until `Continue to publish`. On that choice proceed to Phase 7. Never auto-run (Rule 13).

## Step 15a — Troubleshoot failed case

When a debug/process run fails, read **[troubleshooting-guide.md](troubleshooting-guide.md)**. Diagnose in priority order: incidents → runtime variables → caseplan correlation → traces.

Diagnose → fix → rerun: (1) caseplan defects use the matching plugin, targeted fix, `uip maestro case validate`, and Step 15; if already published, AskUserQuestion `Re-publish the fixed build` / `Skip re-publish`; republish with Step 14, noting overwrite. (2) External defects (connection, task registration, Orchestrator asset, permissions) halt agent edits; AskUserQuestion `Resource fixed, re-run debug` / `Abort`. (3) Inconclusive advances under retry policy.

Inline agent/api-workflow incident `170007` and business-rule incident `300400` under `case debug` are expected because debug does not provision in-solution siblings; do not spend troubleshoot rounds on them. Offer full-solution deployment through AskUserQuestion per [phased-execution.md § Debug notes](phased-execution.md#debug-notes).

Allow up to 3 rounds; each adds new context or a different fix, never identical commands/fixes. A run exceeding 10 minutes wall-clock is inconclusive and counts; do not hard-kill. After three inconclusive/failing rounds, AskUserQuestion with instance ID, folder key, incident IDs/messages, faulting element ID, variable snapshot, attempts, and options `Provide additional context`, `Pause for manual investigation`, `Abort`. Do not propose edits without confirmed cause.

# Phase 7 — Publish to Orchestrator (Step 16)

<!--skill-flavor:phase-seven-bridge:start-->
Optional `case pack` (BPMN recompile) + `solution pack` + `solution publish` to the tenant solution feed. See [phased-execution.md § Phase 7](phased-execution.md#phase-7--publish-to-orchestrator) for prompts, commands, versioning, failures, and handling. This is a bridge; do not duplicate that contract here.
<!--skill-flavor:phase-seven-bridge:end-->

## Step 16 — Publish to Orchestrator

<!--skill-flavor:step-sixteen:start-->
Run AskUserQuestion per [phased-execution.md § Phase 7](phased-execution.md#phase-7--publish-to-orchestrator). On `Publish to Orchestrator`, run `uip solution resources refresh`, then `uip maestro case pack "<SolutionDir>/<ProjectName>" "<SolutionDir>/dist" --output json`, then `uip solution pack "<SolutionDir>" "<SolutionDir>/dist" --output json`, then `uip solution publish "<packagePath>" --wait --output json`. Never skip `case pack`; it compiles `caseplan.case` → `caseplan.case.bpmn` every pass. Publish the `solution pack` `.zip`, never the `case pack` `.nupkg`. Read `<packagePath>` from `solution pack` response `Data.Packages`; never guess it. On `Done`, exit. Never auto-run (Rule 13).
<!--skill-flavor:step-sixteen:end-->

Stop at publish; `uip solution deploy run` is out of scope.
<!-- END: implementation.md -->