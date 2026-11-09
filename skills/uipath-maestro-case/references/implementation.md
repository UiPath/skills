# Phases 2–7 — Execution: sdd.md → caseplan.case

Build `caseplan.case` from `sdd.md` by direct per-plugin JSON edits; use `tasks/registry-resolved.json` only for tenant identities. Execute **2 Prototyping**, **3 Implementation**, **4 Validate**, **5 Publish**, **6 Debug**, and **7 Publish to Orchestrator**. Existing-case targeted edits skip this pipeline; see [brownfield.md](brownfield.md).

> **Prerequisite:** [Phase 1 Resolution](planning.md) produced `tasks/registry-resolved.json`; Phase 1 runs automatically unless the request explicitly stops before build. Use `sdd.md` alone for structure, activation modes, entry rules, inputs, outputs, and rationale; use `tasks/registry-resolved.json` only for tenant identities. Never author an intermediate plan.

Process `sdd.md` in order, with one write section per class: **variables** (Case Variables) → **triggers** (Case Triggers) → **stages** (Section 2 headings) → **tasks** (per-stage Tasks tables and `##### Task N.M` blocks) → **conditions** (Stage Entry / Stage Exit / Task Entry / Case Exit) → **SLA** (case, stage, task).

Emit every SDD declaration one-to-one: never filter defaults, merge rows, or omit `is-interrupting: false`, `runOnlyOnce: true`, or `marks-stage-complete: true`. Each stage/task has one `description`: copy `**Description:**` word-for-word and send `**Design Rationale:**` to `tasks/build-issues.md`; if only rationale exists, use it as `description`; send SLA rationale to the issue log. **When in doubt, emit.** For ambiguity/unrecognized rows, use **AskUserQuestion** with row content, ambiguity, and bounded options — silent omission is a defect. Step 12 `validate --strict --sdd sdd.md` reports omissions as `STRICT_SDD_*`.

Read [phased-execution.md](phased-execution.md) for phase contracts, informational Phase 2 validation, hard stops, re-entry, retries, aborts, and stable step order. Hard stops gate Phase 2→3, Phase 4 retry exhaustion, and Phase 5/6/7 entry.

## Per-plugin execution

Write directly through each plugin’s `impl-json.md`; use [case-editing-operations.md](case-editing-operations.md) for IDs, primitive operations, pre-flight, and canonical writes. Read each plugin reference once per plugin type while grouping that section’s rows; after compaction reread only the current section’s plugin.

**Per-section batched writes — mandatory.** At each section: `Read` once; for `<10` elements, one sequential `Edit` per element without sibling rereads; for `≥10`, one whole-section `Edit`/`Write` replacing its container; untouched siblings MUST be copied verbatim — drop nothing. Validate once at the boundary. Flush buffered issues once to `tasks/build-issues.md` per [`plugins/logging/impl-json.md` § Flush](plugins/logging/impl-json.md), then clear; flush even with zero issues so the file exists after the first section. Mark each SDD element `in_progress` before composing its mutation and `completed` after successful write; section writes preserve this audit trail.

Bundle status text with the next `tool_use` in the same assistant turn. No standalone text between Edits; status ≤1 sentence/~20 tokens; no text block >200 tokens or >500 for completion reports, AskUserQuestion preambles, and validate summaries. Do not start status with `Building`, `Composing`, `Writing`, `Drafting`, `Generating`, `Now I'll`, `Next:`, `Approach:`, `Strategy:`, `Plan:`, `Caveman push:`, `Big single Write:`, `Let me`, or equivalent narration.

Cap one Write at ~15K output tokens/~40KB. If exceeded, write root/nodes/vars and task shapes, then Phase 2 SLA/conditions, then Phase 3 connector/value details. For ≥40 tasks or ≥8 stages never write the complete populated plan in one Write. Build-assembler scripts such as `/tmp/build-caseplan.js` are forbidden by Rule 14. CLI-gated sections use gather-then-write: run all CLI calls, collect results, then Read → write → validate. Use full recovery/scope rules in [case-editing-operations.md § Per-section batch write contract](case-editing-operations.md#per-section-batch-write-contract--canonical); Phase 1 uses the same contract per [planning.md Step 4](planning.md).

Per-node references: root `plugins/case/impl-json.md`; stages `plugins/stages/impl-json.md`; tasks `plugins/tasks/<type>/impl-json.md`; triggers `plugins/triggers/<type>/impl-json.md`; conditions `plugins/conditions/<scope>/impl-json.md`; SLA `plugins/sla/impl-json.md`; variables `plugins/variables/global-vars/impl-json.md`; I/O `plugins/variables/io-binding/impl-json.md`; logging `plugins/logging/impl-json.md`.

## Issue Log — Initialize Before Step 6

Before any build step initialize an in-reasoning, not-file, not-subprocess buffer:

```text
issues = []
```

Plugins append during the current section; flush and clear at each boundary. See [`plugins/logging/impl-json.md`](plugins/logging/impl-json.md) for format, severities, mechanics, and schema. Incremental flushing limits context loss to one section.

## Seed Phase 2 progress todos — Before Step 6

Before Step 6 replace Phase 1 todos with TodoWrite items, marking each `in_progress` on entry and `completed` on exit:

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

There is no edge step (Rule 21; see Step 8). Seed one named sub-item per SDD element and use it as the audit trail per [case-editing-operations.md § Per-section batch write contract](case-editing-operations.md#per-section-batch-write-contract--canonical).

# Phase 2 — Prototyping (Steps 6 – 11.9)

Order: 6 → 6.1 → 6.2 → 6.3 → 7 → 9 → 9.4 → 11 → 10 → 11.9. SLA precedes conditions so `sla-status-change` can reference IDs. Preview includes complete flow and SLA model; values, connector schemas, and final connector rules remain deferred. See [phased-execution.md § Phase 2](phased-execution.md#phase-2--prototyping).

## Step 6 — Create the Case project structure

<!--skill-flavor:step-six-intro:start-->
The case lives in a solution/project. Run `uip solution init <SolutionName>`; inside the solution run `uip maestro case init <ProjectName> --output json`, which seeds the project and registers it in `.uipx` (SKILL.md Rule 24). T01 writes only unseeded scaffold files. The root comes from `sdd convert` (SKILL.md Rule 4); follow T01 for shape/fallback. Never use `uip maestro case cases add` or another case mutation for the root; execute T01 direct JSON so `intsvcActivityConfig` is emitted. If `case init` is unavailable, T01 writes the scaffold and Step 6.0b registers it; see [`case-commands.md` § uip maestro case init](case-commands.md#uip-maestro-case-init).
<!--skill-flavor:step-six-intro:end-->

<!--skill-flavor:step-six-zero:start-->
1. **Step 6.0 (CLI):** Run `uip solution init <SolutionName>`. Skip only when Rule 18 **Create** already produced exact `<SolutionDir>/<SolutionName>.uipx` at the canonical working-root location per [registry-discovery.md § Create-on-Missing → 0 Prerequisite](registry-discovery.md#create-on-missing-build-and-rediscovery) and [plugins/case/planning.md § Naming](plugins/case/planning.md#project-structure-prerequisites); rerunning errors or forks the solution.
   - **Step 6.0a (CLI):** Run `cd <SolutionDir>`, then `uip maestro case init <ProjectName> --output json`. Confirm `Data.SolutionRegistration.Status` is `Registered` or `AlreadyRegistered`. Run `cd` first; chaining after `uip solution init` can create a second solution. Run before `sdd convert`; `case init` refuses a non-empty directory.
<!--skill-flavor:step-six-zero:end-->
2. **T01:** Execute [`plugins/case/impl-json.md`](plugins/case/impl-json.md) in full.
<!--skill-flavor:step-six-t01-scaffold:start-->
   - Scaffold inventories `<SolutionDir>/<ProjectName>/` and writes only unseeded boilerplate: `project.uiproj`, `operate.json`, `entry-points.json`, `bindings_v2.json`, `package-descriptor.json`.
<!--skill-flavor:step-six-t01-scaffold:end-->
   - Write `caseplan.case` with root skeleton (`root`, `nodes: []`, `edges: []`).
<!--skill-flavor:step-six-zero-b:start-->
3. **Step 6.0b (CLI, fallback only):** Run `uip solution projects add <AbsolutePathToProjectDir> <AbsolutePathToUipxFile> --output json` only if Step 6.0a reports `Skipped`/`Failed`, or `case init` was unavailable and T01 wrote the scaffold. **Both arguments MUST be absolute paths;** relative arguments fail with `Failed to add project to solution`. Run after `project.uiproj` exists.
<!--skill-flavor:step-six-zero-b:end-->
<!--skill-flavor:step-six-zero-c:start-->
4. **Step 6.0c:** Verify exactly one `.uipx` exists under the working root at `<SolutionDir>/<SolutionName>.uipx`. For a second manifest, read the stray project; delete its solution only if empty, otherwise adopt it as `<SolutionDir>`. Validate cannot detect this because it reads only the supplied caseplan path.
<!--skill-flavor:step-six-zero-c:end-->

Do not emit a trigger at T01. T02’s trigger plugin owns the primary trigger ID and every `entry-points.json.entryPoints[]` insertion; the scaffold array is empty.

## Step 6.1 — Add triggers

For every Case Triggers row, open its plugin: Manual/Timer/resolved Event → `plugins/triggers/<type>/impl-json.md` §3; unresolved Event → [`plugins/triggers/event/impl-json.md § Placeholder fallback`](plugins/triggers/event/impl-json.md). Write one node and one entry-point atomically. Capture every `TriggerId`; In-arg `elementId` resolves through `id-map[<sourceTriggers T-number>].id`, or primary T02 when blank.

## Step 6.2 — Declare global variables and arguments

For each Case Variables row write directly per [`plugins/variables/global-vars/impl-json.md`](plugins/variables/global-vars/impl-json.md), populating top-level `variables.inputs`, `outputs`, `inputOutputs`, and trigger output mappings before stages. Downstream references use `=vars.<id>`.

## Step 6.3 — Refresh entry-points.json input/output

After variables/triggers, project In/Out arguments onto every entry’s `input`/`output` schema per [entry-points-sync.md](entry-points-sync.md). Re-run idempotently on regeneration; formal In/Out args do not change in Phase 3. Step 12 Check 6 verifies it. Class order remains variables → triggers → stages → tasks → conditions → SLA; within classes follow SDD order.

## Step 7 — Add stages

For every Section 2 stage, including `Secondary Stage`, execute [`plugins/stages/impl-json.md`](plugins/stages/impl-json.md). Capture each `StageId` in the name→ID map and `id-map.json`. Do not write planning-only **Required for Case Completion**; Step 10’s `required-stages-completed` case-exit rule consumes it (`rule-type:` maps to JSON key `rule`).

## Step 8 — (RETIRED — no edges)

Do not build edges (Rule 21); transitions are entry/exit conditions in Step 10. Add extra triggers in Step 6.1; any trigger activates the first stage’s `case-entered` condition.

## Step 9 — Add tasks (Phase 2 shape, gather-then-write)

**Gather:** For each non-connector task run `uip maestro case tasks describe --type <type> --id <entityKey> --output json` and retain its input schema in reasoning. Connector tasks skip gather and `case spec` until Step 9.7; unresolved tasks become Step 9.1 placeholders. Inline-built agent/api-workflow/business-rule siblings (Rule 18 Create) skip tenant describe; they were resolved/bound in Phase 1 from sibling `entry-points.json`. See [`plugins/tasks/agent/impl-json.md`](plugins/tasks/agent/impl-json.md), [`plugins/tasks/api-workflow/impl-json.md`](plugins/tasks/api-workflow/impl-json.md), and [`plugins/tasks/business-rule/impl-json.md`](plugins/tasks/business-rule/impl-json.md).

**Write:** Read once; append one task per SDD order with its matching plugin, capture each `TaskId`, and validate once. Non-connectors (`process`, `agent`, `rpa`, `action`, `api-workflow`, `function`, `business-rule`, `case-management`, `wait-for-timer`) get full `data.inputs[]` schema with `value: ""` and plugin outputs. Connectors get `data.typeId` and `data.connectionId`, omit `data.inputs`, and do not call `case spec`. Unresolved tasks use Step 9.1. Do not bind values here; Step 9.8 binds per [`plugins/variables/io-binding/impl-json.md`](plugins/variables/io-binding/impl-json.md). After compaction reread and process only unappended tasks.

**Task placement contract.** Placement is determined by the SDD's **Activation Mode** column plus the task's **Entry Condition** table; the `data.tasks` task-set index is derived from them, never the reverse.

**Activation-mode audit — before writing any task node.** Scan every stage's task list and fix the mode/rule pairing first; an explicit rule in the SDD always wins, and this audit verifies the handoff rather than redesigning it.

- Contiguous ordered work in one stage (`then`, `after`, `before`, `in order`, or an upstream prerequisite) → `sequential` + `runs-sequentially` on every task in the ordered run, including the first, unless the SDD declares another legal rule.
- Independent work that starts with the stage → `parallel` + `current-stage-entered`. A single-task stage or list position never makes a task sequential.
- Connector/event callback wait → `event-triggered`, usually `wait-for-connector`.
- User-launched optional work → `adhoc` + `adhoc` + `isRequired: false`.
- Branch convergence, fan-in, decision-result routing, or a non-immediate dependency → `fan-in` or `conditional-gate` + `selected-tasks-completed`, with the selected tasks named.

Preserve explicit selectors only when every selected task is a non-adhoc sibling in the same stage; repair invalid selectors before writing; never map a valid gate to `sequential`.

`lane` is the zero-based `data.tasks` task-set index, never a label. Same task set means same number: strict chains are `[[A], [B], [C]]`; parallel siblings are `[[A, B], [C]]`; siblings after one predecessor are `[[A], [B, C], [D]]`. `sequential`/`runs-sequentially` append in planned order; `adhoc`, `event-triggered`, `fan-in`, `conditional-gate`, and standalone nonparallel tasks get single-task sets. Only intentional parallel or `parallel-after-predecessor` siblings may share a set. If mode and lane conflict, mode wins and report the correction. Independent tasks sharing an immediate predecessor must share the next inner array and remain `parallel-after-predecessor`; do not convert them to duplicate predecessor gates. Validate cannot detect grouping, including mixed rules or index 0, so enforce it at write time. Pass `lane: <n>` only when required; default increments from 0 within a stage.

Write envelope `isRequired` and `shouldRunOnlyOnce` from the Task envelope. If `runOnlyOnce` is omitted, set `shouldRunOnlyOnce: false`; never infer true from type. Copy `**Description:**` exactly to `description`; never summarize.

### Step 9.1 — Placeholder tasks for unresolved resources

If `taskTypeId`, or connector `typeId`/`connectionId`, is `<UNRESOLVED: …>`, create a placeholder per [placeholder-tasks.md](placeholder-tasks.md). For every class (process / agent / rpa / action / api-workflow / function / business-rule / case-management / connector-activity / connector-trigger), follow matching `plugins/tasks/<type>/planning.md` Unresolved Fallback and `impl-json.md`: write `type`, `displayName`, `id`, `elementId`, `isRequired`, `data: {}`, and no `taskTypeId`/`connectionId`. Skip binding; copy `wiringNotes` from `tasks/registry-resolved.json` to the completion report. Placeholder IDs still serve task-entry and stage-exit selectors; cross-task bindings wait for the real resource.

## Step 9.4 — Regenerate bindings_v2.json (batch)

After Step 9, run `uip maestro case bindings sync "<caseplan.case path>" --output json` once. Never edit `bindings_v2.json`; derive it from root `bindings[]` per [bindings-v2-sync.md](bindings-v2-sync.md). Write resource root `bindings[]` and `data.name`/`data.folderPath` `=bindings.<id>` references in one Edit; otherwise `STRICT_BINDINGS_ABSENT` or `STRICT_BINDINGS_REFERENCE_UNRESOLVED` occurs.

## Step 11 — Write SLA and escalation objects (per-target Edit batch)

Read once. Group case, stage, and task SLA rows by root/stage and replace each target’s complete `slaRules[]` per [`plugins/sla/impl-json.md`](plugins/sla/impl-json.md). Mint stable `sla_`/`esc_` IDs while composing, reject collisions, and write each `id-map.json` entry with its object. Escalation-only targets receive the documented synthetic default SLA. No preallocation; Step 10 resolves `sla-status-change` against emitted objects. Validate once.

## Step 10 — Add conditions (per (scope, target) Edit batch)

Read once; group rows by `(scope,target)` and replace one array per pair:

| Scope | Target | Replace |
|---|---|---|
| Stage entry | stage | `nodes[stage].data.entryConditions` |
| Stage exit | stage | `nodes[stage].data.exitConditions` |
| Task entry | task | task `data.entryConditions` |
| Case exit | root | `metadata.caseExitRules` |

Per-scope composition rules live in the matching plugin's `impl-json.md`. Every rule object is keyed `"rule": "<value>"` — the planning field `rule-type:` becomes the JSON key `rule`, never `ruleType`. Carry the SDD row's **Display Name** cell verbatim onto the condition's `displayName` (never a boilerplate name like `Completion rule 1` or `Entry from previous stage`): the `--sdd` audit joins rows to conditions by that name for the Exit Type / Interrupting / Marks cells, and a renamed row is silently unaudited there. A rule keyed otherwise fails the default profile with `INVALID_RULE_DISCRIMINATOR` (no `--strict` needed); rename the key, keep its value. Skip the re-Read between sibling Edits; run one validate at section end. For every `wait-for-connector`, write the canonical Phase 2 stub from [`connector-trigger-impl.md § Placeholder fallback`](connector-trigger-impl.md#placeholder-fallback), even when resolved; do not call `case spec` or add bindings. `id-map.json` must contain `{kind:"condition", id:"<conditionId>", ruleId:"<ruleId>", scope:"<scope>", targetId:"<containerId>"}` and task entries retain `stageId`. Step 10.5 changes only `rule.uipath`; unresolved connectors retain the stub and are reported.

## Step 11.9 — Preview validate + Phase 2 boundary

Follow [phased-execution.md § Phase 2 hard stop](phased-execution.md#phase-2-hard-stop). First run:

```bash
uip maestro case validate "<caseplan.case path>" --skeleton-v2 --output json
```

Fall back once to `--skeleton` only if the parser explicitly names `--skeleton-v2` unknown/unsupported, typically `ErrorCode: "invalid_argument"` and exit code 3; exit 3 alone is insufficient because genuine v2 errors do not trigger fallback. Print profile and error/warning counts, then execute Rule 12 boundary. Findings are advisory; never halt solely on them. If legacy `--skeleton` runs, state that rules/SLA remain covered by Phase 4. On either continue choice proceed to Step 9.6.

# Phase 3 — Implementation (Steps 9.6 – 11.5)

Order: 9.6 → 9.7 → 9.8 → 10.5 → 11.5 → 12. See [phased-execution.md § Phase 3](phased-execution.md#phase-3--implementation). Only `"Profile": "strict"` with `Valid` closes Phase 3; default validation does not.

## Step 9.6 — Phase 3 re-entry

Before mutation reread SDD task blocks and `tasks/registry-resolved.json`; reread `caseplan.case` and rebuild maps per [phased-execution.md § Re-entry protocol](phased-execution.md#re-entry-protocol); replace Phase 2 todos with connector schemas (9.7), I/O values (9.8), connector rules (10.5), and `vars.$xref` (11.5). Seed per-element items with the same audit status. Never trust Phase 2 maps after compaction.

## Step 9.7 — Connector task detail (gather-then-write)

For each connector task (`connector-activity`, `connector-trigger`) in the SDD:

1. Run `get-connection` (each task runs its own — never reuse).
2. Run `uip maestro case spec --type <activity|trigger> --activity-type-id <id> --connection-id <id> --input-details '<json>' --output json` per plugin `impl-json.md`.
   > **Connector tasks skip 3–5:** `uip maestro case splice <caseplan> --task-id <taskId> --spec tasks/spec-cache.<elementId>.json --connection-id <id>` (no `--folder-key`: splice takes it from the spec) does the substitution, the id minting, and the root bindings in one call ([connector-activity/impl-json.md § Step 5](plugins/tasks/connector-activity/impl-json.md)). The steps below apply to the event-trigger node and connector-bound rules.
3. Substitute `{{CONN_BINDING_ID}}`/`{{FOLDER_BINDING_ID}}` placeholders in `caseShape.context[*].value` with minted binding ids.
4. Mint `var`/`id`/`elementId` on `caseShape.inputs`/`outputs` per plugin uniqueness rule.
5. Retain caseShape plus root Connection/FolderKey bindings in reasoning.

Skip placeholders. If either call returns `Connector catalog unavailable` (`ErrorCode: server_error`), downgrade every served task to Rule 9 `data: {}`; never retain flat `{name, value}` inputs; see [connector-integration.md § Catalog unavailable](connector-integration.md#catalog-unavailable-typecache-5xx).

Then Read once and Edit each gathered task with `data.context`, `data.inputs`, and `data.outputs` generated by [`io-binding/impl-json.md § Output Binding Shapes`](plugins/variables/io-binding/impl-json.md#output-binding-shapes), including SDD `->`/`=` rows and root bindings. `->` reassigns a connector output; `=` adds `custom: true`; copying `caseShape.outputs` alone loses declared extracts. Populate IS cache per [bindings-v2-sync.md § Populate IS connection cache](bindings-v2-sync.md), run `uip maestro case bindings sync "<caseplan.case path>" --output json` once, then validate. On compaction process only tasks lacking `data.context`.

## Step 9.8 — Bind task input/output values (per-task Edit batch)

Read once; for every non-placeholder resource task run `uip maestro case tasks describe --type <taskType> --id <selected.identifier> --output json`, save it, then run `uip maestro case splice "<caseplan.case>" --task-id "<taskId>" --described "<that file>" --output json` before editing types. `selected.identifier` is action `id`, otherwise `entityKey`; raw planner ledger uses `selected.entityKey`, or `selected.id` for action. Then Edit each task’s full `data.inputs`; skip placeholders. Per [`plugins/variables/io-binding/impl-json.md`](plugins/variables/io-binding/impl-json.md), literal/expression `input = "<value>"` writes `<value>`; cross-task `input <- "Stage"."Task".output` resolves the authoritative output reference ID and writes `=vars.<outputReferenceId>`. Never hand-write a type supplied by splice. Validate once.

A `=js:` value is JavaScript source: a line break inside a string is the two characters `\` and `n`; JSON on disk therefore contains `\\n`. Writing `\n` creates a real line break and Jint rejects it; validate does not parse `=js:` and the packer copies it into `.bpmn`. This holds for every path that writes an `=js:` value into `caseplan.case`, this Edit included. If a source task is absent, halt and report.

## Step 10.5 — Upgrade connector-bound condition-rule stubs (gather-then-write)

Read and scan all four scopes for `wait-for-connector` rules whose `uipath.context` still has `connectorKey: "placeholder"` and `operation: "placeholder"`. Match through the Phase 2 `id-map.json` entry and registry. For resolved connectors run connector-trigger `case spec --type trigger --input-details`, mint IDs, gather root bindings, and Edit only `uipath`; preserve condition array, `id`, `rule`, `conditionExpression`, scope, and placement, then apply output bindings. If unresolved or spec fails, retain/log the stub and report it. Populate IS cache and run `uip maestro case bindings sync "<caseplan.case path>" --output json` once; rescan so resolved rules have no placeholder. See [`connector-trigger-impl.md § Target: connector-bound condition rule`](connector-trigger-impl.md#target-connector-bound-condition-rule).

## Step 11.5 — Resolve in-expression `vars.$xref` markers (whole-file pass)

After 9.8/10.5, Read once and Edit every string containing `vars.$xref('Stage','Task','output')`, resolving via the common output-reference algorithm to bare `vars.<outputReferenceId>` (no leading `=` inside `=js:`). Cover inputs, conditions, SLA, computed outputs, and connector fields. An unresolved triple/ID is an error. See [`plugins/variables/io-binding/impl-json.md § In-Expression Marker Resolution`](plugins/variables/io-binding/impl-json.md#in-expression-marker-resolution-step-115). Validate once.

## Step 12 — End-of-Phase-3 validator pass

Follow [`plugins/variables/io-binding/impl-json.md § Binding Procedure`](plugins/variables/io-binding/impl-json.md#binding-procedure) for algorithms, prompts, and responses. First run `uip maestro case validate "<caseplan.case path>" --strict --sdd sdd.md --output json`; unknown options use [case-commands.md § Version guard](case-commands.md#version-guard----strict----sdd-require-cli-1202). Repair targeted findings through three rounds, then **AskUserQuestion**. Permanent connector-rule-stub errors are excluded; if they alone remain, finish per [connector-trigger-impl.md § What validate reports for a stub](connector-trigger-impl.md#what-validate-reports-for-a-stub). If `--strict` is rejected, run default and report it. `STRICT_*`/`CASE_MGMT_*` meanings are in [validator-codes.md](validator-codes.md).

Run Checks 1–18:

1. Resolve every `=vars.X` in all task, condition, trigger, SLA, and `=js:` strings against `variables.{inputs, inputOutputs}[].id`; unresolved → AskUserQuestion: name variable, remove reference, or best-effort emit with Open Items.
2. For each `variables.outputs[]`, verify producer/default per [`io-binding/impl-json.md § Check 2`](plugins/variables/io-binding/impl-json.md): default without companion → ask; no default with Rule 18 placeholder producer → silently log to `## Open Items for User`; pure orphan → ask add producer, add default, recategorize/remove, or best-effort.
3. Type mismatch is WARN/non-blocking; runtime coercion is tolerated.
4. No `$xref(` survives. Unresolved → present existing outputs and ask rewrite triple, edit SDD/re-run Phase 1, or best-effort; see [`io-binding/impl-json.md § Check 4`](plugins/variables/io-binding/impl-json.md).
5. For each registry task with contract, required inputs have values and every extract `Field` exists; upstream `=vars.<outputReferenceId>` counts bound without §1.5 row. Ask bind/re-point, `<UNRESOLVED>`+review/drop, or best-effort. Skip placeholders; see [`io-binding/impl-json.md § Check 5`](plugins/variables/io-binding/impl-json.md#check-5--resolved-resource-io-completeness).
6. Verify `entry-points.json` parity, keys/types/`required`/`file`/`jsonSchema`, unique `filePath` fragments, and no orphan `inputs[].elementId`; refresh once, then non-interactively log mismatches under `## Open Items for User`; see [`entry-points-sync.md § Check 6`](entry-points-sync.md#check-6--entry-point-schema-parity-step-12-validator).
7. Run `uip maestro case bindings sync "<caseplan.case path>" --output json`; `ResourceCount: 0` with `Result: Success` is valid. Re-run strict validate; repair `STRICT_BINDINGS_ABSENT` in the plan and `STRICT_BINDINGS_SIDECAR_STALE` by sync. `ResourceCount` equals distinct `resourceKey`; `ConnectionCount` equals distinct connection IDs. Repair plan, never sidecar.
8. Build global output uniqueness pool across variables, tasks, triggers, and all rule scopes, including unused/schema outputs (`Error`, `response`); on collision, suffix the later producer, update only that producer's fields and consumers by producer ownership, rerun affected binding/marker steps, and halt before Phase 4 if any duplicate generated `id` or `var` remains. Apply [global uniqueness rule](plugins/variables/global-vars/impl-json.md#uniqueness-rule); validate success is insufficient.
9. For every registry entry with non-null `selected`, matching task exists and is not `data: {}`; non-connectors have `data.name` and `data.folderPath` as complete `=bindings.<id>` references. Never placeholder a selected resource. Repair targeted only under [`case-editing-operations.md § Per-section batch write contract`](case-editing-operations.md#per-section-batch-write-contract--canonical), repeat Checks 7/9. Do not enter Phase 4, report completion, or downgrade this finding to an Open Item while it remains unresolved; `uip maestro case validate` success does not satisfy this check.
10. Every formal `variables.inputs[]`/`outputs[]` ID matches `^v[A-Za-z0-9]{8}$` per [`global-vars/impl-json.md § Formal-arg slot ID format`](plugins/variables/global-vars/impl-json.md#formal-arg-slot-id-format). Non-interactively mint a unique replacement (deduplicated against the Check 8 global pool); update In-arg bridge `source` from old to new; leave `name`, `var`, and `inputOutputs[].id` unchanged; skip placeholder-trigger bridge; rescan and halt if invalid.
11. For non-connectors, each shared root binding pair’s `resourceKey` equals its own defaults: normally `"<folderPath-binding default>.<name-binding default>"`; inline-built sibling with empty folder default uses `solution_folder.<name-binding default>`. Connector pairs and `solution_folder.<Name>` sibling key are excluded. The most common violation is copying a tenant identity value — the SDD's "Resource Identity" column, a `tasks describe --id` argument, or a registry `entityKey` — directly into `resourceKey` instead of constructing the composite string. Repair both pair entries (a pair's two `resourceKey` values must stay identical), resync, rescan, halt if invalid. See [`bindings/impl-json.md § resourceKey construction`](plugins/variables/bindings/impl-json.md#resourcekey-construction--non-connector-tasks).
12. For every resolved connector task (`wait-for-connector` / `execute-connector-activity` / `external-agent` / `external-workflow`), case-level `Intsvc.EventTrigger`, and all four-scope `wait-for-connector` rules, verify nonempty context; selected connectorKey; `context[name="connection"].value = =bindings.<id>`; no placeholders/tokens; complete root bindings (ConnectionId + FolderKey, the latter omitted only when `spec.connection.folderKey` was null); and matching `tasks/spec-cache.<elementId>.json` or `tasks/trigger-spec-cache.json` — its cached `context` matches the written `context` modulo only the placeholder substitutions. A mismatch means the context was composed from agent memory rather than spliced — forbidden per [connector-trigger-impl.md § Step 4](connector-trigger-impl.md#step-4--substitute-placeholders-in-caseshapecontext). Re-run `case spec`, persist cache, splice tasks, or splice trigger/rule fields per [connector-trigger-impl.md § Step 4](connector-trigger-impl.md#step-4--substitute-placeholders-in-caseshapecontext), [§ Step 5](connector-trigger-impl.md#step-5--mint-var--id--elementid-on-inputs-and-outputs), and [§ Root-level bindings](connector-trigger-impl.md#root-level-bindings), then Check 7. `uip maestro case validate` success does not satisfy this check (it reports `Valid` for a connector task with an empty `context` and no root bindings). If `case spec` fails on the retry, retain degraded shape, log the node under `## Open Items for User` as **"connector node <name> is not runnable — `context` unresolved"** and report it — never silently emit it as complete; halt if a resolved node still fails.
13. Every `selected-tasks-completed` rule has nonempty `selectedTasksIds`, each ID resolves within owning stage, and none is adhoc. Repair from exact SDD names via `tasks/id-map.json`; Unresolvable after one pass → **AskUserQuestion** (name the intended task / repair the plan / continue with best-effort emit, logged under Open Items). Also repair every `exitToStageId` and `selectedStageIds` to existing `case-management:Stage` IDs. Halt before Phase 4 while any selector is empty with no user decision or selects an adhoc task. If any resolved task is adhoc, stop and return to the plan: required routing cannot depend on optional user-launched work, and replacing the selector without redesigning that route is forbidden; build-with-best does not waive the adhoc restriction.
14. Every `default` in variables inputs/outputs/inputOutputs is a JSON string regardless of type. Re-encode objects/arrays/numbers/booleans (`{"a":1}`→`"{\"a\":1}"`, `5`→`"5"`, `true`→`"true"`, `{}`→`"{}"`) without changing type; halt if non-string remains. See [`global-vars/impl-json.md § default encoding`](plugins/variables/global-vars/impl-json.md#default-encoding-every-type-mandatory).
15. Every task, including placeholders/connectors/manual tasks, has nonempty `entryConditions` whose first element has nonempty `rules[][]`. Repair from SDD Entry Condition using [`task-entry-conditions/impl-json.md § Rule Types`](plugins/conditions/task-entry-conditions/impl-json.md#rule-types), otherwise Activation Mode; if neither exists ask intended rule or default `current-stage-entered` and log. Do not substitute a `current-stage-entered` default when the SDD specifies something else (`runs-sequentially`, `adhoc`, `selected-tasks-completed`, `wait-for-connector`, `sla-status-change`) — use it only when the SDD specifies it. No best-effort; halt if still empty. Mandatory backstop for Step 10 — do not treat Step 10 having run, or a clean plain `Valid` (the entry-rule finding is only a warning), as evidence this check passed.
16. Condition `displayName` is unique case-wide across all four scopes and matches SDD names exactly when declared once. A name the SDD declares once must reach the plan exactly as written — never rename it for consistency; decide per name, never per case: prefix only names the SDD repeats. `validate` enforces both, so repair what it reports. A name you write must not repeat; `validate` reports a repeat it will not accept as `CASE_MGMT_RULE_NAME_DUPLICATE`, a hard error on every profile. It accepts a repeated frontend default name — any name the frontend generates, in any locale, such as `Entry rule 1`, `Tasks completed rule` or `Entry from '<stage>'` — because the platform renumbers repeated defaults itself when the plan loads. The set is large and exact-spelled (`Entry Rule 1`, capital `R`, is not in it), so do not decide from memory or a list: run `validate` and repair only what it reports, and leave a repeated default it accepts alone. Repeated semantic names require AskUserQuestion or noninteractive stage/task prefix and issue-log entry. A clean `Valid` IS evidence rule 1 passed; rule 2 needs `--strict --sdd`. **Never repair a name collision by emptying an `entryConditions[]`** — it turns the build green while destroying behaviour. See [case-schema.md § Condition name uniqueness](case-schema.md#condition-name-uniqueness).
17. Each In-arg’s bound trigger has a bridge in `data.inputs.outputs[]` with matching `name` and `var`, exact `source: "=vars.<id>"`, and no `value`; skip placeholder triggers. Create the bridge if absent (creating `data.inputs = {"outputs": []}` on a bare manual trigger node first), set `source` to `"=vars.<the entry's id>"`, and delete any `value` key on it, per [`global-vars/impl-json.md § In argument`](plugins/variables/global-vars/impl-json.md#in-argument) and [`triggers/manual/impl-json.md`](plugins/triggers/manual/impl-json.md); halt if still missing.
18. Every task whose SDD block has `**Description:**`, or only `**Design Rationale:**`, MUST carry that line word-for-word in `description`. Repair targeted and rerun strict validate; otherwise log missing tasks and why. `STRICT_SDD_TASK_DESCRIPTION_MISSING` is a warning, not proof of compliance; count the `STRICT_SDD_TASK_DESCRIPTION_MISSING` codes rather than reading the status.

For best-effort picks in Checks 1, 2, 4, 5, or 13, append `## Open Items for User` to `tasks/build-issues.md` and proceed. Checks 14/15 have no best-effort escape. At Phase 4 end, count that section from disk; if N>0 print exactly `Open Items: <N> entry/entries — review tasks/build-issues.md § Open Items for User before publishing.` using `entry` only for 1, before stage/task summary. End Phase 3 mutations and proceed directly to Phase 4.

# Phase 4 — Validate (Steps 12 – 12.1)

See [phased-execution.md § Phase 4](phased-execution.md#phase-4--validate) for contract, retries, and prompts.

## Step 12 — Strict validate with the SDD audit

**Run `uip maestro case validate "<caseplan.case path>" --strict --sdd sdd.md --output json` — mandatory.** `--sdd` audits every stage, task/type, condition row, SLA, trigger, and variable; missing entry rules and resolved placeholders are errors. `STRICT_SDD_FILE_NOT_FOUND` means fix the path, never remove `--sdd`. Unknown `--strict`/`--sdd` alone invokes [case-commands.md § Version guard](case-commands.md#version-guard----strict----sdd-require-cli-1202); if `--sdd` is unsupported, run `--strict`, manually audit six classes, and report it. Extra caseplan elements and placeholders the SDD also left unresolved come back as warnings — carry them into the completion report's Open Items. Repair targeted findings for up to 3 rounds, then AskUserQuestion. Permanent connector stubs do not count. On strict `Valid`, or only stub errors, continue.

## Step 12.1 — Summarize the issue log

Flush the final buffer, read `tasks/build-issues.md`, and write grouped counts per [`plugins/logging/impl-json.md § Summary`](plugins/logging/impl-json.md). If absent, reconstruct from artifacts and stamp `NOTE:` per [§ Recovery](plugins/logging/impl-json.md). Never take placeholders/`<UNRESOLVED>` to Phase 5 without a log. On success proceed to Phase 5.

# Phase 5 — Publish (Steps 13, 14)

See [phased-execution.md § Phase 5](phased-execution.md#phase-5--publish); this is only the bridge.

## Step 13 — Completion report + Publish prompt

Print required report fields and run AskUserQuestion. `Publish to Studio Web` → Step 14; `Skip to Debug` → Phase 6.

## Step 14 — Publish to Studio Web

Run `uip solution resources refresh`, then `uip solution upload <SolutionDir> --output json --output-filter "{Status: Status, Action: Action, SolutionId: SolutionId, DesignerUrl: DesignerUrl}"` per [phased-execution.md § Publish notes](phased-execution.md#publish-notes). The filter is mandatory. Print `DesignerUrl`, state `Imported` or `Overwritten`, then Phase 6.

# Phase 6 — Debug (Steps 15, 15a)

See [phased-execution.md § Phase 6](phased-execution.md#phase-6--debug).

## Step 15 — Debug prompt + session

<!--skill-flavor:step-fifteen-debug:start-->
Run AskUserQuestion and the debug command per [phased-execution.md § Phase 6](phased-execution.md#phase-6--debug). On `Run debug session`, run `uip solution resources refresh`, then `uip maestro case debug`, looping until `Continue to publish`; then Phase 7. Never auto-run (Rule 13).
<!--skill-flavor:step-fifteen-debug:end-->

### Step 15a — Troubleshoot failed case

On debug/process failure read **[troubleshooting-guide.md](troubleshooting-guide.md)**; prioritize incidents → runtime variables → caseplan correlation → traces. Diagnose → fix → rerun: caseplan defects use targeted plugin edits, `uip maestro case validate`, then Step 15; if already published, AskUserQuestion `Re-publish the fixed build`/`Skip re-publish`, with republish rerunning Step 14. External defects (connection, task registration, asset, permissions) halt agent edits. Report exact resource + remediation steps to user via **AskUserQuestion** with options — `Resource fixed, re-run debug`, `Abort`. Inconclusive rounds follow policy.

Inline-built agent/api-workflow fault `170007` and business-rule fault `300400` under `case debug` are expected because debug does not provision siblings; do not troubleshoot them; offer full solution deployment through AskUserQuestion per [phased-execution.md § Debug notes](phased-execution.md#debug-notes).

Allow up to 3 troubleshoot→fix→debug rounds per failed run; each must add context or use a different fix, with no identical command/fix. A run over 10 minutes is inconclusive and counts; do not hard-kill. Track rounds.

<!--skill-flavor:troubleshoot-halt-report:start-->
After the 3rd inconclusive or post-fix failure, halt and AskUserQuestion. Report instance ID, folder key, incident IDs/messages, faulting element ID, variable snapshot, and every round’s actions. Offer `Provide additional context` (one targeted round), `Pause for manual investigation`, or `Abort`. Do not propose caseplan edits without a confirmed cause.
<!--skill-flavor:troubleshoot-halt-report:end-->

# Phase 7 — Publish to Orchestrator (Step 16)

<!--skill-flavor:phase-seven-bridge:start-->
Optional `case pack` (BPMN recompile) + `solution pack` + `solution publish` to the tenant solution feed. See [phased-execution.md § Phase 7](phased-execution.md#phase-7--publish-to-orchestrator); it owns prompts, commands, versioning, and failures.
<!--skill-flavor:phase-seven-bridge:end-->

## Step 16 — Publish to Orchestrator

<!--skill-flavor:step-sixteen:start-->
Run AskUserQuestion per [phased-execution.md § Phase 7](phased-execution.md#phase-7--publish-to-orchestrator). On `Publish to Orchestrator`, run `uip solution resources refresh`, then `uip maestro case pack "<SolutionDir>/<ProjectName>" "<SolutionDir>/dist" --output json`, `uip solution pack "<SolutionDir>" "<SolutionDir>/dist" --output json`, and `uip solution publish "<packagePath>" --wait --output json`. Never skip `case pack`; it compiles `caseplan.case` → `caseplan.case.bpmn` every pass. Publish the `solution pack` `.zip`, never the `case pack` `.nupkg`. Read `<packagePath>` from `solution pack` response `Data.Packages`; never guess. On `Done`, exit. Never auto-run (Rule 13).
<!--skill-flavor:step-sixteen:end-->

Stops at publish; `uip solution deploy run` is out of scope.
<!-- END: implementation.md -->