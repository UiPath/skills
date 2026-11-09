# Phased Execution: Phase 2 → Phase 3 → Phase 4 → Phase 5 → Phase 6 → Phase 7

Authoritative post-resolution flow. Read before writing any `caseplan.case` element from `sdd.md`.

> **Editing an existing case?** Targeted edits to an existing `caseplan.case` skip these phases — see [brownfield.md](brownfield.md).

> **Relationship to other docs.** This document defines phase boundaries and hard-stop contracts. Per-plugin detail is in `plugins/<name>/impl-json.md`; ordering and file-system mutations are in [implementation.md](implementation.md).

## Downstream CLI compatibility

Emit the `32.0.3` shape `{ id, version, name, metadata, bindings, variables, nodes, edges, layout }`. JSON-shape correctness is in scope; downstream CLI accept-correctness is not.

| Phase | Contract |
|---|---|
| 2 — Prototyping | Informational validate; never halt on errors. |
| 4 — Validate | `uip maestro case validate` accepts the shape. Retry-and-fix while each fix reduces errors; halt only after two consecutive unchanged fix→validate rounds or 12 rounds. |
| 5 — Publish | `uip solution upload` accepts it. On failure, rerun once without `--output-filter`, dump the unfiltered response to `tasks/upload-response.json`, report the CLI error verbatim, and re-show the Phase 5 prompt. |
| 6 — Debug | `uip maestro case debug` accepts it; failure concerns the case/resources, not schema. Record the CLI error verbatim in `build-issues.md`. |
| 7 — Publish to Orchestrator | Packs/publishes the whole solution, carrying the shape unvalidated by this step. On `pack`/`publish` failure, report the CLI error verbatim, note it in `build-issues.md`, and re-show the Phase 7 prompt. |

## Why phased

Do not build the full case in one pass. Phase 2 runs `sdd convert` and creates a reviewable preview; Phase 3 adds connector `case spec` detail and task-value binding. SKILL.md Rule 12 controls only whether the preview pauses: pause-at-preview stops for visual review; straight-through narrates and continues. Phases 4–7 and publish/debug/Orchestrator gates are unconditional. Publish precedes Debug so Debug exercises the Studio Web build; Orchestrator publish is last so only an exercised build reaches the tenant solution feed.

## Phase summary

| Phase | Build/output | Exit stop |
|---|---|---|
| **2 — Prototyping** | `sdd convert` output (fallback: hand authoring), solution/project, structure, triggers, task shapes, all 4 condition scopes, SLA/escalation; connector rules use canonical stubs. Emits `caseplan.case`; attempts `--skeleton-v2`, falling back to `--skeleton` if unsupported. | Pause-at-preview: `Publish for review` / `Skip publish and continue` / `Abort`. Straight-through: none; report counts and continue (Rule 12). |
| **3 — Implementation** | Connector schemas, task I/O binding, resolved connector-rule stubs; authoritative `caseplan.case`. | None; continue to Phase 4. |
| **4 — Validate** | Strict `uip maestro case validate`; summarize `build-issues.md` (journal already on disk). → `caseplan.case` passes full validation. | On 3rd validate failure: `Retry with fix` / `Pause for manual edit` / `Abort`. |
| **5 — Publish** | Optional Studio Web upload; print `DesignerUrl`. | `Publish to Studio Web` / `Skip to Debug`. |
<!--skill-flavor:phase-table-six-row:start-->
| **6 — Debug** | Optional real CLI debug (emails, API calls, etc.); stream output. | `Run debug session` / `Continue to publish`; re-publish after a fix requires separate confirmation. |
<!--skill-flavor:phase-table-six-row:end-->
<!--skill-flavor:phase-table-seven-row:start-->
| **7 — Publish to Orchestrator** | Optional `case pack` + `solution pack` + `solution publish` to tenant solution feed; `.zip` packed; publish result printed. | `Publish to Orchestrator` / `Done` |
<!--skill-flavor:phase-table-seven-row:end-->

## Phase 2 — Prototyping

### Convert first — emit from the document before authoring

**Run `uip maestro case sdd convert` before writing any Phase 2 element by hand.**

```bash
uip maestro case sdd convert "<SDD_PATH>" --resolved tasks/registry-resolved.json --out "<CASEPLAN_PATH>" --output json
```

Run it **after** the Phase 1 registry gate and [planning.md Step 4](planning.md#step-4--complete-registry-resolvedjson), never before. `--resolved` binds each `selected` resource's name/folder; without it or before the gate, resolution is lost. If convert rejects ledger/SDD disagreement, rerun `sdd resolve`, re-apply Step 4 additions with Edit, then convert; never edit `sdd.md` or the ledger to force agreement.

If the response names `sdd` or `convert` unknown (typically `ErrorCode: "invalid_argument"`, exit 3), author Phase 2 by hand, say so once, and continue. Exit 3 without that command-specific message is a real failure: report it and do not fall back.

Read the authoritative `UnresolvedItem` union in CLI `sdd-convert/types.ts`; never retype it. Only these kinds have downstream closers (plus `placeholder`); all others close through Phase 4 using `detail`:

| `kind` | Closure |
|---|---|
| `resource-binding` | Close with Phase 1 bindings; project `selected` into root bindings (Step 12 Check 7). |
| `output-type` | Close at Step 9 via `uip maestro case tasks describe` or `case spec`. |
| `connector-context` | Close with Phase 3 connector context (Step 12 Check 12): `folderKey` and connector-version `metadata`. |
| `case-role` | Covers Personas mapping, gated permissions (`Assign`, `Tasks*`, `TaskAssignment*`, `TaskSelfAssignment*`), row/plan-role mismatch, unreadable/undeclared/uncarrried roles, and v1 apps with no roles. Never change user design (SKILL.md Rule 2). Show `detail` and planner Personas comment; with approval edit row and rerun convert. For gated permission ask whether tenant flag exists; retain key if yes, remove only with approval. Otherwise follow `detail`: approved row edit, remove role, or move case to V2. Non-interactive: leave rows and list every item in `build-issues.md`. Never guess-edit `metadata.caseRoles`. |
| `task-grouping` | Only when the stage declares no Activation Mode or Task set: shared `runs-sequentially` tasks may be parallel siblings or a strict chain. Closed in Phase 2 — read the stage's intent in the SDD. For a strict chain, move each named task into consecutive single-task sets, retaining `runs-sequentially` as its only entry rule ([case-schema.md § Positioning](case-schema.md)); for siblings, retain the emitted set. |
| `placeholder` | Ledger defers task (`gateDecision: "resolve-at-build"` or `<UNRESOLVED: …>` identity slot per SKILL.md Rule 10); convert emits Rule 9 `data: {}`, retained entry conditions, no binding. Do not re-edit or add `data`. If `where` is an expression (skip/input/condition), it reads a valueless placeholder output; list it in `build-issues.md`. |

This is the sole place this skill names an `Unresolved` kind; verify names against `types.ts`.

Convert maps Personas to `metadata.caseRoles` (role name, description, `case`/`stages` scope with stage IDs, permission literals) and sets `caseAppVersion: v2`. Permissions are not packaged: `bindings sync` writes one `Role` entry per role, `uip solution pack` mints the role resource and writes `spec.actions`, and pack refuses a role lacking `Role` (`case_role_unbound`) until sync. Phase 4 `--strict --sdd` compares roles and rejects unsupported template-shape personas.

Convert emits root `bindings[]` (two entries per resource, `name` and `folderPath` sharing one `resourceKey`), never `bindings_v2.json`. Run `uip maestro case bindings sync` at the end of Step 9 and again at Step 12 Check 7, after resolution can change bindings; derive the sidecar from bindings and `metadata.caseRoles`. Do not sync here.

`Unresolved[]` is a floor, not a ceiling: it omits wrong or silently omitted output. Phase 4 `--strict --sdd` is authoritative; plain-profile `Status: Valid` on convert output does not finish the plan.

**Verify task entry rules before leaving Phase 2, whatever convert emitted** — this check is not optional and nothing upstream covers it. Walk every task in every stage and verify its own `entryConditions`. Empty rules produce only `Task has no entry rules` under plain validate, are absent from `Unresolved[]`, and hang `uip maestro case debug` indefinitely (SKILL.md Rule 7). Write missing rules from SDD §4.6 **Entry Condition** and **Activation Mode** cells, per task, never once per group.

### Structural nodes (full detail)

<!--skill-flavor:structural-scaffolding:start-->
- Run `uip solution init`, then `uip maestro case init` inside the solution directory, and write remaining JSON scaffolding from `plugins/case/impl-json.md`.
<!--skill-flavor:structural-scaffolding:end-->

Create root `caseplan.case` with top-level fields, populated `metadata` (name, `metadata.caseIdentifier`), empty `nodes[]` and `edges[]`; fully declare `variables` (`inputs`, `outputs`, `inputOutputs`) and arguments; generate/capture all StageIds; author no edges (Rule 21), keeping `schema.edges` `[]`; make stage transitions conditions; fully build triggers and output mappings to existing global variables; refresh `entry-points.json` `input`/`output` schemas from declared In/Out arguments (Step 6.3, per [entry-points-sync.md](entry-points-sync.md)).

### Tasks (shape depends on resolution state + task class)

| Class/state | Phase 2 shape |
|---|---|
| Non-connector (`process`, `agent`, `rpa`, `action`, `api-workflow`, `function`, `business-rule`, `case-management`, `wait-for-timer`) with resolved `task-type-id` | Write full `data.inputs[]` from `uip maestro case tasks describe`, every `value` `""`; populate outputs and plugin scalar fields (including `action` `taskTitle`/`priority`/`recipient`/`labels`) per plugin. Final at Step 2 except input values, deferred to Phase 3. |
| Connector (`connector-activity`, `connector-trigger`) with resolved `type-id` + `connection-id` | Set `data.typeId` and `data.connectionId`; omit or empty `data.inputs`. **Do not call `case spec` in Phase 2**; defer schema to Phase 3. |
| Any unresolved (`<UNRESOLVED: …>` in `tasks/registry-resolved.json`) | Rule 9 placeholder: empty `data: {}` plus `data.taskTitle` / `data.priority` / `data.recipient` for `action`; preserve marker. See [placeholder-tasks.md](placeholder-tasks.md). |
| Inline-built `agent` / `api-workflow` / `business-rule`, bound at Phase 1 Rule 18 gate | Not a placeholder. Fully resolved name+folder binding, `resourceKey="solution_folder.<name>"`, **`folderPath` binding `default` = `""`**; `solution_folder` remains only in `resourceKey`. See [registry-discovery.md § Create-on-Missing](registry-discovery.md#create-on-missing-build-and-rediscovery). |

### Rules, SLA, and connector-rule stubs

Write SLA/escalation first, minting stable `sla_*` / `esc_*` IDs with objects. `sla-status-change` conditions use those IDs; do not preallocate in Phase 3. Write stage-entry, stage-exit, task-entry, and case-exit conditions in final scope/position. Every `wait-for-connector` rule gets canonical stub `uipath` in Phase 2, even if resolved; Phase 3 replaces only `rule.uipath` for resolved connectors. Unresolved connectors retain/report the stub.

### What does NOT get written in Phase 2

Do not write task input `value` bindings (literals, expressions, cross-task references), connector task input/output schemas, or final `uipath.context` / inputs / outputs and Connection bindings for connector-bound condition rules.

### Phase 2 informational validate

Run once after Phase 2 mutations:

```bash
uip maestro case validate "<caseplan.case path>" --skeleton-v2 --output json
```

If the response names `--skeleton-v2` unknown/unsupported (typically `ErrorCode: "invalid_argument"`, exit 3), run once with `--skeleton`. Exit 3 without that flag-specific message is insufficient. Do not fall back after genuine v2 findings. Legacy `--skeleton` checks structure only and skips preview conditions/SLA; Phase 4 is authoritative. Do not halt for errors/warnings; capture profile and counts, optionally a few messages. `CONNECTOR_ACTIVITY_MISSING` errors in `skeleton-v2` are expected; do not repair them.

## Phase 2 hard stop

**Use the up-front build-review preference (SKILL.md Rule 12); never introduce a mid-build surprise.** It comes from greenfield design-handoff Case Review Build options or the provided-SDD post-roadmap question.

Always print the Summary. Straight-through continues to Phase 3 without prompt; pause-at-preview presents Prompt; missing preference asks interactively or, non-interactively, continues straight-through without publish and says so. Phase 4 retry-cap, Phase 5 publish, Phase 6 debug-consent, and Phase 7 publish-consent are independent and never bypassed.

Every user-visible stop/handoff after progress includes a short `Suggested next steps` line before prompt/final exit; apply it after straight-through reports, preview summaries, URLs, publish completion, debug results, and abort/done exits.

#### Summary content

Print counts of stages / primary stages / secondary stages / triggers / total tasks / placeholder tasks / unresolved resources; result/profile as `skeleton-v2: <N> errors, <M> warnings` or `skeleton (fallback; rules/SLA deferred to Phase 4): <N> errors, <M> warnings`; and paths `caseplan.case`, `sdd.md`, `registry-resolved.json`. Connector rules remain stubs; `CONNECTOR_ACTIVITY_MISSING` is expected and Phase 3 Step 10.5 upgrades resolved rules. Do not repair it here. Use exactly these suggested lines: straight-through — `Suggested next steps: I'll continue wiring the implementation now; say stop if you want to inspect the skeleton first.`; pause — `Suggested next steps: publish the skeleton for visual review, continue locally without preview, or abort and inspect the files.` Do not enumerate tasks; Studio Web visualizes them after publish.

#### Prompt (pause-at-preview branch only)

Use **AskUserQuestion**: `Publish for review` (upload skeleton to Studio Web), `Skip publish and continue` (Phase 3), `Abort` (stop; retain artifacts).

#### On `Publish for review`

1. Run `uip solution resources refresh --solution-folder "<SolutionDir>" --output json`, then `uip solution upload "<SolutionDir>" --output json --output-filter "{Status: Status, Action: Action, SolutionId: SolutionId, DesignerUrl: DesignerUrl}"`. `--output-filter` is mandatory (see [case-commands.md § uip solution upload](case-commands.md#uip-solution-upload)).
2. Parse `DesignerUrl`.
3. **Before AskUserQuestion, emit plain text on its own line:** `Skeleton published. Review at: <DesignerUrl>`. Never put the URL only in the question.
4. Print `Suggested next steps: inspect the skeleton in Studio Web, then continue implementation here or abort and keep the artifacts for manual review.`
5. Ask **AskUserQuestion**: `Continue to implementation` / `Abort`.

If `DesignerUrl` is absent, rerun once without `--output-filter`, dump the response to `tasks/upload-response.json`, print its path, and continue prompting. This is a second upload and the maximum allowed within consent. Mention once with the URL that Phase 5 re-publish overwrites review-time Studio Web edits with final local state and records replaced contents as a restorable version; Phase 6 fix→re-publish has its own confirmation. Users may compare Studio Web before/after Phase 3.

`Skip publish and continue` proceeds to Phase 3. On `Abort`, append current buffered issues to existing `tasks/build-issues.md`, then fill the summary per [`plugins/logging/impl-json.md` § Flush](plugins/logging/impl-json.md). Never whole-file dump; preserve prior journal rows. If absent, create per § Flush. Print `caseplan.case`, `sdd.md`, `registry-resolved.json`, and solution-directory paths; print `Suggested next steps: inspect tasks/build-issues.md and the generated artifacts, then rerun after editing the design or plan.` Exit without deleting artifacts.

## Phase 3 — Implementation

### Re-entry protocol

Phase 3 begins after straight-through or `Continue to implementation` / `Skip publish and continue`. Before any step:

1. Re-read `sdd.md` (task detail and Inputs/Outputs) and `tasks/registry-resolved.json`.
2. Re-read `caseplan.case`, authoritative for Phase-2 IDs: Stage name→StageId from `schema.nodes[]` where `type === "case-management:Stage"`, keyed by `data.label`; secondary stages have `data.stageType === "secondary"`; trigger IDs from `type === "uipath.case.trigger"`; task name→TaskId per stage from `schema.nodes[<stage>].data.tasks[][]`; variable name→`var` IDs from `variables.{inputs,outputs,inputOutputs}`; SLA/escalation and all condition/rule IDs, including stubbed connector rules.
3. Optionally cross-check `id-map.json`; `caseplan.case` remains source of truth.

Never trust in-memory Phase-2 maps across the stop.

### Phase 3 — Execution order

Carry `tasks describe` / `case spec` results in memory and persisted `tasks/registry-resolved.json`, `tasks/spec-cache.<elementId>.json`, `tasks/trigger-spec-cache.json`. Never rerun an identical same type+ID call in the session; reread the artifact.

1. For each connector task, run plugin detail steps: `case spec --type {activity,trigger} --input-details`; mint `data.context[]` / `data.inputs[]` / `data.outputs[]` from populated `caseShape` (placeholder substitution and var/ID minting), applying SDD `->` / `=` output rows to `data.outputs[]` per [`io-binding/impl-json.md` § Output Binding Shapes](plugins/variables/io-binding/impl-json.md#output-binding-shapes).
2. Bind task I/O for all classes per [`plugins/variables/io-binding/impl-json.md`](plugins/variables/io-binding/impl-json.md). In SDD Inputs order, write literal, expression, or cross-task references into `task.data.inputs[i].value`; resolve references through common `.id` resolver to `=vars.<outputReferenceId>`. Connector schemas exist from step 1; bind values here.
3. Scan all four scopes for canonical connector-rule stubs. For each resolved connector, run `case spec --type trigger --input-details` and replace only `rule.uipath`; preserve rule/condition IDs, expressions, scope, and placement. Report unresolved stubs.
4. After all outputs are minted/deduped, perform one sink-blind whole-file pass per [`plugins/variables/io-binding/impl-json.md § In-Expression Marker Resolution`](plugins/variables/io-binding/impl-json.md): replace every `vars.$xref('Stage','Task','output')` with bare `vars.<outputReferenceId>` in inputs, conditions, SLA, and connector bodies. Unresolved triple or reference ID is ERROR.
5. Run Checks 1–11 from [`implementation.md § Step 12`](implementation.md): `=vars.X`, Out-arg producer, type mismatch, surviving `$xref`, resolved-resource I/O, entry-point parity, bindings sidecar parity, output-ID uniqueness, resolved-resource emission/repair preservation, formal-arg slot ID format, resourceKey self-consistency. AskUserQuestion for unresolved references (including `$xref`), pure orphan Out-args, and unbound required inputs/phantom output fields; option (c)/(d) `continue with best-effort emit` preserves progress. Checks 6–11 are non-interactive: auto rerun/regenerate/remint once where permitted; Check 6 logs continued divergence; Checks 7, 9, 10, 11 halt before Phase 4 if still divergent. Never HALT otherwise.

Phase 3 has no exit gate and proceeds to Phase 4. Sole blockers are Check 7 parity, Check 9 emission/preservation, Check 10 formal-arg slot ID, Check 11 resourceKey, Check 12 resolved connector `context`/root bindings, or Check 15 missing task entry rule after repair; halt per [`implementation.md § Step 12`](implementation.md).

## Phase 4 — Validate

Run at end of detail mutations:

```bash
uip maestro case validate "<caseplan.case path>" --strict --sdd sdd.md --output json
```

`--strict` adds stage/task checks: `STRICT_STAGE_NO_TASKS`; surviving `$xref(`, `<-`/`->` input notation, or unbound `vars.<x>` (`CASE_MGMT_XREF_UNRESOLVED`, `CASE_MGMT_PLANNING_NOTATION`, `CASE_MGMT_REFERENCE_UNBOUND`); hoisted `conditionExpression` (`CASE_MGMT_CONDITION_EXPR_HOISTED`); duplicate output IDs (`CASE_MGMT_OUTPUT_ID_DUPLICATE`); duplicate SLA-rule IDs (`CASE_MGMT_SLA_ID_DUPLICATE`)—these six fail every profile; incomplete connector `caseShape.context`/missing Activity Type ID (`STRICT_CONNECTOR_*`); empty `data` (`TASK_NOT_CONFIGURED`, warning, or with `--sdd`, `STRICT_SDD_PLACEHOLDER_RESOLVED` error when SDD resolved it); malformed outputs/formal slots (`STRICT_OUTPUT_*`); unbound/non-`=vars.<id>` inputs (`STRICT_INPUT_UNBOUND` / `STRICT_INPUT_REF_FORM`). `--sdd <path>` implies `--strict` and audits every declared stage, task, task type, condition row, SLA, trigger, and case variable (`STRICT_SDD_*`). Issues carry code and element path; targeted-Edit the named element and rerun. `--strict` cannot combine with `--skeleton` / `--skeleton-v2`.

If CLI rejects `--strict` as unknown, rerun without it and report `strict validate unavailable`; `Valid` without strict is not evidence. Both flags exist from CLI 1.202; only `invalid_argument` naming them permits plain validate. Apply [case-commands.md § Version guard](case-commands.md#version-guard----strict----sdd-require-cli-1202) and log the fallback.

Success is `{ Result: "Success", Code: "CaseValidate", Data: { File, Status: "Valid", Profile: "strict" } }`; flush/summarize the issue log and proceed to Phase 5. Failure lists `[error]`/`[warning]` with path/message; fix the named issue and rerun.

Permanent connector-rule stubs never validate. Exclude their errors ([connector-trigger-impl.md § What validate reports for a stub](connector-trigger-impl.md#what-validate-reports-for-a-stub)) from repair and counts. If all remaining errors are logged stubs, pass with `strict: <E> errors, all from <N> unresolved connector rules`, list each under Open Items, summarize the issue log, and proceed.

### Validate-loop guard — no re-validate without an intervening edit

Never rerun `uip maestro case validate` unless `caseplan.case` or a validated sidecar changed. Phase 2 informational validate runs once; Phase 4 runs once per fix. `validate → validate` is invalid; only fix → edit → validate is legal.

### Retry policy

Read every `Data.Issues[]` path and repair; do not inspect installed CLI (`node_modules/@uipath/**/dist`). A strict mid-build failure on unbuilt stages is not a stop: each empty declared stage yields `STRICT_STAGE_NO_TASKS`, each missing task `STRICT_SDD_TASK_MISSING`, and each missing condition row `STRICT_SDD_CONDITION_MISSING`. Count only built stages; keep repairing while counts fall. Halt only after two consecutive unchanged fix→validate rounds or 12 rounds. Never drop `--strict --sdd` to pass.

At halt use **AskUserQuestion**, showing remaining errors: `Retry with fix` (fix and rerun; counter does not reset), `Pause for manual edit` (exit mid-flight; user edits `caseplan.case` and reruns), or `Abort` (append current buffer to `build-issues.md`, summarize without replacing it, and retain artifacts).

### Findings whose names mislead

| Code | Actual meaning/repair |
|---|---|
| `CASE_MGMT_ROOT_CASE_CONDITION_RULE_USER_SELECTED_STAGE_MISSING` | Does not inspect selector; checks whether **any other stage** has a `wait-for-user` exit condition. Repair that other stage, not the named one. |
| `STRICT_CONNECTOR_CONTEXT_INCOMPLETE` | Checks presence by name, not values. All seven `connectorKey`, `connection`, `resourceKey`, `folderKey`, `objectName`, `operation`, `metadata` must exist; `""` satisfies presence. Values are checked by `CASE_MGMT_CONNECTOR_RESOURCE_KEY_UNRESOLVED` and `STRICT_CONNECTOR_ACTIVITY_TYPE_ID`. On two-entry `"placeholder"` rule context it means unresolved connector: report, never repair ([connector-trigger-impl.md § What validate reports for a stub](connector-trigger-impl.md#what-validate-reports-for-a-stub)). |
| `CASE_MGMT_STAGE_ALL_EXIT_CONDITIONS_MISSING_ERROR` | Warning, despite `_ERROR`. |
| `TASK_NOT_CONFIGURED` | Fires only when `data` has zero keys; `data: { inputs: [] }` does not fire. Placeholder detector, not completeness check. |

`CASE_MGMT_STAGE_ENTRY_CONDITION_MISSING` and `CASE_MGMT_STAGE_EXIT_CONDITION_MISSING` are suppressed plan-wide when any case-manager stage has tasks; inspect `marksStageComplete` directly. A doubled `CASE_MGMT_ROOT_ROOT_` prefix is the external canvas validator's firing spelling; single-`ROOT_` variants are unreachable from CLI.

### Summarize the issue log

`tasks/build-issues.md` is flushed at every section boundary from Phase 2 per [`plugins/logging/impl-json.md` § Flush](plugins/logging/impl-json.md). After successful validate, flush the final buffer, reread the journal, and fill its grouped summary; counts come from the file. If absent, reconstruct from artifacts and stamp `NOTE:` per [§ Recovery](plugins/logging/impl-json.md). Then proceed to Phase 5.

## Phase 5 — Publish

After Phase 4, report and use **AskUserQuestion**:

- `Publish to Studio Web` — run `uip solution resources refresh --solution-folder "<SolutionDir>" --output json`, then `uip solution upload "<SolutionDir>" --output json --output-filter "{Status: Status, Action: Action, SolutionId: SolutionId, DesignerUrl: DesignerUrl}"`; print `DesignerUrl` on its own line and whether `Action` is `Imported` or `Overwritten`; proceed to Phase 6.
- `Skip to Debug` — proceed without publishing.

Before prompt print `Suggested next steps: publish to Studio Web when you want a designer-visible version, or skip to debug if the local artifacts are enough for now.` After publish print `Suggested next steps: open the Designer URL, verify resources and connections, then run a debug session to exercise the case.`

### Report fields (printed before prompt)

Print: (1) `caseplan.case` path; (2) stages/tasks/conditions/SLA summary; (3) validation pass and warnings; (4) every placeholder (TaskId, type, display-name, stage), external resource needing registration (task-type-id / connection-id), and `wiringNotes` from `tasks/registry-resolved.json`; under **Not covered**, SDD items outside `caseplan.case` such as Data Fabric entity schemas; separately list inline-built agents/API workflows/business rules and built-but-unreferenced reject cases (no user action). See [placeholder-tasks.md § Completion-Report Shape](placeholder-tasks.md#completion-report-shape). (5) missing IS connections; (6) the suggested line, mentioning placeholder/connection fixes before publish; (7) environment gaps with status, endpoint, and time, including connector catalog Studio Web TypeCache `Search/Catalog` HTTP 5xx, separately from missing-resource placeholders. See [placeholder-tasks.md § Completion-Report Shape](placeholder-tasks.md#completion-report-shape).

### Publish notes

`uip solution upload` accepts the solution directory (folder containing `.uipx`); **`--output-filter` is mandatory on every `uip solution upload` call**; see [case-commands.md § uip solution upload](case-commands.md#uip-solution-upload). **Run `uip solution resources refresh` before upload** to sync `bindings_v2.json` (Rule 15). **Do not** run `uip solution pack` + `uip solution publish` here; that is Phase 7 and has its own gate (see [§ Phase 7](#phase-7--publish-to-orchestrator)). Publish is unexercised; Debug follows. If a Phase-6 fix changes the build, ask **AskUserQuestion**: `Re-publish the fixed build` / `Skip re-publish`; on republish rerun this phase's refresh and upload, overwriting current Studio Web state including reviewer edits; on skip leave Studio Web unchanged.

## Phase 6 — Debug

After Phase 5, use **AskUserQuestion**:

<!--skill-flavor:phase-six-run-option:start-->
- `Run debug session` — run `uip solution resources refresh --solution-folder "<SolutionDir>" --output json`, then `uip maestro case debug "<directory>/<solutionName>/<projectName>" --log-level debug --output json`; stream results.
<!--skill-flavor:phase-six-run-option:end-->
- `Continue to publish` — proceed to Phase 7.

> **Debug executes case for real — sends emails, posts messages, calls APIs, writes to databases. Only run when user explicitly asks. Never auto-run** (Rule 13).

<!--skill-flavor:phase-six-requirements:start-->
Requires `uip login`. Uploads to Studio Web, runs in Orchestrator, streams results.
<!--skill-flavor:phase-six-requirements:end-->

After debug, return to this prompt; leave only on `Continue to publish`. Before prompt print `Suggested next steps: run a debug session if you are ready to exercise the case, or continue to the Orchestrator publish gate if validation (and publish) is enough for now.` After results print `Suggested next steps: inspect the debug output, fix and re-run, re-publish with the Phase 5 commands if a fix changed the build, or continue to the Orchestrator publish gate.`

### Debug notes

<!--skill-flavor:phase-six-refresh-note:start-->
- **Run `uip solution resources refresh` before debug** to sync `bindings_v2.json` and Studio Web connector dependencies (Rule 15).
<!--skill-flavor:phase-six-refresh-note:end-->

- Debug verifies end-to-end execution. For fixable failures see [Step 15a — Troubleshoot failed case](implementation.md#step-15a--troubleshoot-failed-case); rerun and republish if already published.
<!--skill-flavor:phase-six-inline-siblings:start-->
- **Inline-built siblings (agent, api-workflow, business-rule) are NOT provisioned by `case debug`**: agent/API workflow faults with incident `170007` ("job's associated process could not be found"); business rule with `300400` ("the job carries no debug session properties"). Runtime verification requires full deploy (`uip maestro case pack` → `uip solution pack` → `uip solution publish` → `uip solution deploy run`), always `case pack` first, beyond [§ Phase 7](#phase-7--publish-to-orchestrator) which stops at publish. Offer via AskUserQuestion, never run unprompted: `Run full solution deploy` / `Skip (mark debug-unverifiable)`. If declined, report debug-unverifiable and continue. See [api-workflow/planning.md § Creating an API workflow inline](plugins/tasks/api-workflow/planning.md#creating-an-api-workflow-inline) / [business-rule/planning.md § Creating a business rule inline](plugins/tasks/business-rule/planning.md#creating-a-business-rule-inline).
<!--skill-flavor:phase-six-inline-siblings:end-->

## Phase 7 — Publish to Orchestrator

After Phase 6, use **AskUserQuestion**:

- `Publish to Orchestrator` — run the four commands below in order.
- `Done` — exit without publishing.

> **Publish to Orchestrator ships the case to the tenant solution feed — a real, outward-facing publish. Only run when user explicitly selects it. Never auto-run** (Rule 13).

<!--skill-flavor:phase-seven-commands:start-->
Requires `uip login`.

### Publish commands

```bash
uip solution resources refresh --solution-folder "<SolutionDir>" --output json
uip maestro case pack "<SolutionDir>/<ProjectName>" "<SolutionDir>/dist" --output json
uip solution pack "<SolutionDir>" "<SolutionDir>/dist" --output json
uip solution publish "<packagePath>" --wait --output json
```

Run `resources refresh` first to sync artefacts/debug overwrites from `bindings_v2.json` (Rule 15). Run `case pack` every time, without exception: it recompiles `caseplan.case` to `caseplan.case.bpmn` in the case project; its `.nupkg` is throwaway. Output must be `<SolutionDir>/dist`, a sibling of the project; never put it inside the project. `case pack` is mandatory per [§ Why `case pack` is mandatory](#why-case-pack-is-mandatory). Run `solution pack` on the solution directory containing `.uipx`, not the case project; it bundles project `.nupkg`s into one `.zip` under `<SolutionDir>/dist`. Add `--version <version>` when user names one; default `1.0.0`. Existing `name+version` is rejected; bump on republish. Run `solution publish` on the `.zip`; add `--personal-workspace` only when requested. Flags: [case-commands.md § uip solution publish](case-commands.md#uip-solution-publish).

Read `<packagePath>` from `solution pack` response `Data.Packages` or list `<SolutionDir>/dist`; never guess. The zip is `<name>_<version>.zip` (underscore); `case pack` emits `<Name>.case.Case.<version>.nupkg`. Never publish the case `.nupkg`.
<!--skill-flavor:phase-seven-commands:end-->

### Why case pack is mandatory

`uip solution pack` only bundles an on-disk `.bpmn`; `uip maestro case validate` does not generate it. Only `uip maestro case pack` compiles `caseplan.case` → `caseplan.case.bpmn`. Run it on every Phase 7 pass whether Phase 5/6 ran or `.bpmn` exists; otherwise the package may contain no or stale `.bpmn` while pack/publish still succeed. `case pack` requires `package-descriptor.json` in the case project (scaffolded by [plugins/case/impl-json.md](plugins/case/impl-json.md)); on `Missing package-descriptor.json`, restore it and do not skip. `case pack` emits one project `.nupkg`; `solution pack` internally creates the project package and wraps it in the publishable `.zip`.

Phase 7 stops at publish. `uip solution deploy run` is out of scope; report the package and tell the user to deploy from Orchestrator.

### On failure

<!--skill-flavor:phase-seven-on-failure:start-->
If `case pack`, `solution pack`, or `publish` fails, print the CLI error verbatim, note it in `build-issues.md`, and re-show the Phase 7 prompt. Do not retry with another pack command or bypass failed `case pack`; that could ship missing/stale `.bpmn`. A `processKey` collision means the `name+version` exists; rerun with bumped `--version`.
<!--skill-flavor:phase-seven-on-failure:end-->

### Suggested next steps

<!--skill-flavor:phase-seven-next-steps:start-->
Before prompt: `Suggested next steps: publish to Orchestrator when you want the case on the tenant solution feed, or stop here if Studio Web and debug are enough.` After success: `Suggested next steps: verify the package with 'uip solution packages list', then deploy it to an Orchestrator folder.` On `Done`: `Suggested next steps: review caseplan.case locally, or update sdd.md and re-run when you want changes.`
<!--skill-flavor:phase-seven-next-steps:end-->

### Publish-to-Orchestrator notes

Phase 7 is last; nothing re-enters the build pipeline. It does not replace Phase 5: Studio Web and solution feed are separate destinations. If a Phase-6 fix follows a Phase-7 publish, rerun Phase 7 with a bumped `--version`; duplicate `name+version` is rejected. Deployment/activation use the platform workflow for `uip solution deploy ...`. For authoring changes, update `sdd.md` and rerun from Phase 1; no in-place incremental edits.

## Placeholder tasks — unchanged semantics

Placeholders are unresolved-resource tasks with empty `data: {}`. Phase 2 creates them; Phase 3 does not type-upgrade them; external registration is required. See [placeholder-tasks.md](placeholder-tasks.md).

> **Agents / API workflows / business rules built inline are not placeholders.** At Rule 18 `Create`, Phase 1 builds/registers/binds the sibling, so Phase 2 receives a fully resolved task. Only declined/skipped or failed builds remain placeholders. See [registry-discovery.md § Create-on-Missing](registry-discovery.md#create-on-missing-build-and-rediscovery).

Phase 3 still wires placeholder TaskIds into task-entry conditions and stage-exit `selected-tasks-completed` rules. It does not write `data.inputs` / `data.outputs`; binding waits for the user's post-build upgrade.

## Abort semantics

Abort is available at the Phase 2 first prompt (pause-at-preview only), Phase 2 post-publish prompt, and Phase 4 retry-cap prompt. In every case append current buffer to `build-issues.md`, fill summary (append-only; never replace), print paths, and exit. Do not delete artifacts or roll back; partial state belongs to the user.

## Out of scope

- **Re-ingesting Studio Web edits.** Review-time edits are not round-tripped into local `caseplan.case`; Phase 3 writes local state and Phase 5 overwrites Studio Web with it.
- **Resuming aborted session.** Rerunning refreshes `registry-resolved.json` in Phase 1 and re-executes Phase 2 onward from `sdd.md` (Rule 7).

<!-- END: phased-execution.md -->