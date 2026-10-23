# Phased Execution: Phase 2 → Phase 3 → Phase 4 → Phase 5 → Phase 6 → Phase 7

Authoritative post-resolution flow. Read before writing any `caseplan.case` element from `sdd.md`.

> **Editing an existing case?** Targeted edits to an existing `caseplan.case` skip these phases — see [brownfield.md](brownfield.md).

> **Relationship to other docs.** This document defines phase boundaries and hard-stop contracts. Per-plugin detail: `plugins/<name>/impl-json.md`. Per-step ordering and filesystem mutations: [implementation.md](implementation.md).

## Downstream CLI compatibility

Emit the `32.0.3` top-level shape `{ id, version, name, metadata, bindings, variables, nodes, edges, layout }`; downstream acceptance is outside skill scope.

| Phase | Contract |
|---|---|
| 2 | Informational validate; never halt on errors. |
| 4 | `uip maestro case validate` accepts the shape. Fix and retry while error count falls; halt only after two consecutive unchanged fix→validate rounds or 12 rounds. |
| 5 | `uip solution upload` accepts it. On failure, upload once without `--output-filter`, dump the unfiltered response to `tasks/upload-response.json`, report the CLI error verbatim, and re-show the Phase 5 prompt. |
| 6 | `uip maestro case debug` accepts it; failure is a case/resource finding, not schema failure. Record the CLI error verbatim in `build-issues.md`. |
| 7 | Whole-solution pack/publish carries it unvalidated. On `pack`/`publish` failure, report the CLI error verbatim, note it in `build-issues.md`, and re-show the Phase 7 prompt. |

## Why phased

After resolution, do not build the full case in one pass. Phase 2 runs `sdd convert` or the specified hand-authoring fallback and emits a reviewable structure/condition/SLA/escalation preview. Phase 3 adds connector `case spec` detail and task value binding. SKILL.md Rule 12 selects pause-at-preview or narrated straight-through continuation. Phases 4–7 retain unconditional validate, publish, debug, and Orchestrator-publish gates: publish precedes Debug so Debug exercises the shipped Studio Web build; Orchestrator publish is last so only an exercised build reaches the tenant solution feed.

## Phase summary

| Phase | Build | Output | Exit stop |
|---|---|---|---|
| **2 — Prototyping** | `sdd convert` or hand authoring; solution/project, structure, triggers, task shapes, four condition scopes, SLA/escalation; canonical connector stubs | `caseplan.case`; attempt `--skeleton-v2`, fallback to `--skeleton` only for unsupported flag | Pause: `Publish for review` / `Skip publish and continue` / `Abort`; straight-through: none, continue (Rule 12) |
| **3 — Implementation** | Connector schemas, task I/O values, connector-rule stub upgrades | Validation-ready `caseplan.case` | None; proceed to 4 |
| **4 — Validate** | Authoritative validate and `build-issues.md` summary | Full validation pass | On 3rd validate failure: `Retry with fix` / `Pause for manual edit` / `Abort` |
| **5 — Publish** | Optional Studio Web upload | `DesignerUrl` | `Publish to Studio Web` / `Skip to Debug` |
<!--skill-flavor:phase-table-six-row:start-->
| **6 — Debug** | Optional real CLI debug (emails, API calls, etc.) | Streamed debug output | `Run debug session` / `Continue to publish`; fix re-publish separately |
<!--skill-flavor:phase-table-six-row:end-->
<!--skill-flavor:phase-table-seven-row:start-->
| **7 — Publish to Orchestrator** | Optional `case pack` + `solution pack` + `solution publish` to tenant solution feed | Packed `.zip`; printed publish result | `Publish to Orchestrator` / `Done` |
<!--skill-flavor:phase-table-seven-row:end-->

## Phase 2 — Prototyping

### Convert first — emit from the document before authoring

**Run `uip maestro case sdd convert` before writing any Phase 2 element by hand.** Run it after the Phase 1 registry gate and [planning.md Step 4](planning.md#step-4--complete-registry-resolvedjson), never before:

```bash
uip maestro case sdd convert "<SDD_PATH>" --resolved tasks/registry-resolved.json --out "<CASEPLAN_PATH>" --output json
```

`--resolved` binds each `selected` resource name/folder; omitting it or running before the gate discards resolution. If convert reports a stage/task/field mismatch, re-run `sdd resolve`, re-apply Step 4 additions with Edit, and convert again; never edit `sdd.md` or the ledger to force agreement.

If the response names `sdd` or `convert` as unknown (typically `ErrorCode: "invalid_argument"`, exit 3), author Phase 2 by hand exactly below, say so once, and continue. Exit 3 without that command-specific message is a real failure: report it and do not fall back.

`Data.Unresolved[]` is the work list; each entry has `kind`, `where`, and `detail`. Authoritative kinds are the `UnresolvedItem` union in CLI `sdd-convert/types.ts` (read it; do not retype it). This table is the sole place this skill names an `Unresolved` kind; verify names against `types.ts`. Other kinds are repaired in Phase 4 from `detail`.

| `kind` | Meaning and closure |
|---|---|
| `resource-binding` | Tenant resource for task; use Phase 1 bindings and project `selected` into root bindings (Step 12 Check 7). |
| `output-type` | Output shape from resolved schema; use Step 9, `uip maestro case tasks describe`, or `case spec`. |
| `connector-context` | `folderKey` and connector-version `metadata`; close with Phase 3 connector context (Step 12 Check 12). |
| `case-role` | Personas row cannot map (scope, stage, permission key, stage-scope permission, name, description, duplicate, nothing left to grant, no name); tenant-gated permission (`Assign`, `Tasks*`, `TaskAssignment*`, `TaskSelfAssignment*`) written as stated; re-convert mismatch, undeclared/unreadable/un-carried plan role; or v1 plan with no roles. Never change the row without approval (SKILL.md Rule 2). Show `detail` and planner-template Personas key fix; with approval edit and re-run convert. For gated permission ask whether tenant has the flag; retain key if yes, remove only with agreement. Otherwise edit with approval, remove role, or move case to V2 in Case Designer. Non-interactive: leave rows and list every entry in `build-issues.md`. Never guess-edit `metadata.caseRoles`. |
| `task-grouping` | Shared `runs-sequentially` tasks may be siblings or strict chain. Read SDD intent. Strict chain: one named task per consecutive single-task set, retaining `runs-sequentially` as sole entry rule ([case-schema.md § Positioning](case-schema.md)); siblings: leave emitted set. |
| `placeholder` | Ledger defers task (`gateDecision: "resolve-at-build"` or `<UNRESOLVED: …>` identity slot per SKILL.md Rule 10); convert already wrote Rule 9 `data: {}` with entry conditions and no binding. Do nothing and do not add `data` or re-edit. If `where` is an expression, it reads a valueless placeholder output; list it in `build-issues.md`. |

Convert maps Personas to `metadata.caseRoles` (name, description, `case`/`stages` scope with stage ids, permission literals), sets `caseAppVersion: v2`, and uses the case app that honours roles. Permissions are not in the package: `bindings sync` writes one `Role` per role, `uip solution pack` mints its resource and `spec.actions`, and pack rejects a role lacking `Role` (`case_role_unbound`) until sync. Phase 4 `--strict --sdd` compares roles and rejects an unhonoured template-shape persona.

Convert emits root `bindings[]` (two entries per resource, `name` and `folderPath` sharing `resourceKey`), never `bindings_v2.json`. Run `uip maestro case bindings sync` at Step 9 end and again at Step 12 Check 7, after resolution can change bindings; do not sync here. `Unresolved[]` is a floor, not a correctness/completeness report; Phase 4 `--strict --sdd` is authoritative, and plain-profile `Status: Valid` is not completion.

Before leaving Phase 2, walk every task in every stage and ensure its own `entryConditions`, using the SDD §4.6 **Entry Condition** and **Activation Mode** cells per task, never once per similar group. This check is not optional and not covered by anything upstream: plain validate only warns `Task has no entry rules`, `Unresolved[]` omits it, and debug can hang indefinitely (SKILL.md Rule 7).

The sections below define what Phase 2 must contain either way. With convert, read the emitted plan against them and fill only the gaps. Without it, they are the authoring instructions.

### Structural nodes (full detail)

<!--skill-flavor:structural-scaffolding:start-->
- Run `uip solution init`, then run `uip maestro case init` inside the solution directory; add remaining JSON scaffolding from `plugins/case/impl-json.md`.
<!--skill-flavor:structural-scaffolding:end-->
- Root `caseplan.case`: top-level fields and populated `metadata` (name, `metadata.caseIdentifier`, empty `nodes[]`, empty `edges[]`).
- Declare all global `inputs`, `outputs`, and `inputOutputs` in top-level `variables`.
- Generate and capture all StageIds.
- Author no edges (Rule 21); `schema.edges` remains `[]`; write stage transitions through conditions.
- Fully build triggers and output mappings (global variables already exist).
- Refresh `entry-points.json` `input`/`output` schemas from In/Out arguments (Step 6.3, per [entry-points-sync.md](entry-points-sync.md)); this idempotently makes the Phase-2 publish-for-review contract correct.

### Tasks (shape depends on resolution state + task class)

| Class | Resolution | Phase 2 shape |
|---|---|---|
| Non-connector (`process`, `agent`, `rpa`, `action`, `api-workflow`, `function`, `business-rule`, `case-management`, `wait-for-timer`) | `task-type-id` resolved | Write full `data.inputs[]` from `uip maestro case tasks describe`, each `value` `""`; populate outputs and task scalars (for example `action` `taskTitle`/`priority`/`recipient`/`labels`) per plugin. Final at Step 2 except input values, deferred to Phase 3. |
| Connector (`connector-activity`, `connector-trigger`) | `type-id` + `connection-id` resolved | Set `data.typeId` and `data.connectionId`; omit or empty `data.inputs`; make **no `case spec` call**; defer schema to Phase 3. |
| Any | Unresolved `<UNRESOLVED: …>` in ledger | Rule 9 placeholder: empty `data: {}` (for `action` tasks only, plus `data.taskTitle` / `data.priority` / `data.recipient`); preserve marker. See [placeholder-tasks.md](placeholder-tasks.md). |
| Inline `agent` / `api-workflow` / `business-rule` | Built and bound at Phase 1 Rule 18 gate | Not placeholder: name+folder binding, `resourceKey="solution_folder.<name>"`, `folderPath` binding `default` = `""`; `solution_folder` only in `resourceKey`. Treat as resolved. See [registry-discovery.md § Create-on-Missing](registry-discovery.md#create-on-missing-build-and-rediscovery). |

### Rules, SLA, and connector-rule stubs

Write SLA/escalation first and mint stable `sla_*`/`esc_*` IDs with objects; `sla-status-change` conditions use those IDs, with no Phase 3 preallocation. Write stage-entry, stage-exit, task-entry, and case-exit conditions in final scope/position. Every `wait-for-connector` rule gets canonical `uipath` in Phase 2, even when resolved; Phase 3 replaces only `rule.uipath` for resolved connectors. Keep/report unresolved stubs.

Do not write task input `value` bindings, connector task input/output schemas, or final `uipath.context`/inputs/outputs and Connection bindings for connector-bound condition rules in Phase 2.

### Phase 2 informational validate

Run once after Phase 2 mutations:

```bash
uip maestro case validate "<caseplan.case path>" --skeleton-v2 --output json
```

If the response names `--skeleton-v2` unknown/unsupported (typically `ErrorCode: "invalid_argument"`, exit 3), run once with `--skeleton`. Exit 3 without that flag-specific message is insufficient. Do not fall back after genuine v2 findings. Legacy `--skeleton` checks structure only and skips conditions/SLA; Phase 4 is authoritative. Do not halt on errors/warnings; capture profile and error/warning counts, optionally first messages.

### Phase 2 hard stop

Use the up-front SKILL.md Rule 12 preference; never introduce a mid-build surprise. Always print the Summary. Straight-through continues to Phase 3 with no prompt and uses the summary as milestone narration. Pause-at-preview presents the Prompt and requires a response. If no preference (resumed/legacy), interactive asks Prompt; non-interactive continues straight-through, does not publish, and says so once. Phase 4 retry, Phase 5 publish, Phase 6 debug-consent, and Phase 7 publish-consent are independent and never bypassed.

Every user-visible stop/handoff after progress includes `Suggested next steps` before prompt/final exit: after straight-through report, pause summary, preview URL, publish, debug, abort/done. Make it concrete: inspect preview, continue, publish, debug, fix placeholders/connections, or edit the named artifact and rerun.

#### Summary content

Print: (1) stages / primary stages / secondary stages / triggers / total tasks / placeholder tasks / unresolved resources; (2) `skeleton-v2: <N> errors, <M> warnings` or `skeleton (fallback; rules/SLA deferred to Phase 4): <N> errors, <M> warnings`; (3) paths `caseplan.case`, `sdd.md`, `registry-resolved.json`; (4) exactly one suggested-next-step line:

- Straight-through: `Suggested next steps: I'll continue wiring the implementation now; say stop if you want to inspect the skeleton first.`
- Pause-at-preview: `Suggested next steps: publish the skeleton for visual review, continue locally without preview, or abort and inspect the files.`

Do not enumerate tasks.

#### Prompt (pause-at-preview branch only)

Use **AskUserQuestion**: `Publish for review` (upload skeleton to Studio Web), `Skip publish and continue` (Phase 3), `Abort` (stop; leave artifacts).

#### On `Publish for review`

1. Run `uip solution resources refresh --solution-folder "<SolutionDir>" --output json`, then run `uip solution upload "<SolutionDir>" --output json --output-filter "{Status: Status, Action: Action, SolutionId: SolutionId, DesignerUrl: DesignerUrl}"`; `--output-filter` is mandatory (see [case-commands.md § uip solution upload](case-commands.md#uip-solution-upload)).
2. Parse `DesignerUrl`.
3. Before AskUserQuestion, emit on its own plain-text line: `Skeleton published. Review at: <DesignerUrl>`; never put the URL only in the question.
4. Emit `Suggested next steps: inspect the skeleton in Studio Web, then continue implementation here or abort and keep the artifacts for manual review.`
5. AskUserQuestion: `Continue to implementation` / `Abort`.

If `DesignerUrl` is missing, run upload once without `--output-filter`, dump the unfiltered response to `tasks/upload-response.json`, print its path, and continue to the prompt. This second upload/overwrite/version is allowed once within this consent. Alongside the URL, once state that Phase 5 re-publish overwrites review-time Studio Web edits with final local state and records replaced contents as a restorable version; do not repeat it as a standing warning (Phase 6 fix→re-publish has its own confirmation). Users may compare Studio Web before/after Phase 3.

`Skip publish and continue`: proceed to Phase 3. `Abort`: append buffered issues to existing `tasks/build-issues.md`, fill summary per [`plugins/logging/impl-json.md` § Flush](plugins/logging/impl-json.md); never whole-file dump/replace; create it if abort precedes first boundary. Print `caseplan.case`, `sdd.md`, `registry-resolved.json`, and solution directory; print `Suggested next steps: inspect tasks/build-issues.md and the generated artifacts, then rerun after editing the design or plan.`; exit. Do not delete artifacts.

## Phase 3 — Implementation

### Re-entry protocol

Before any Phase 3 step, re-read `sdd.md` task details and Inputs/Outputs, `tasks/registry-resolved.json`, and `caseplan.case`. The SDD is contract; ledger carries identities; `caseplan.case` is authoritative for:

- Stage name → StageId from `schema.nodes[]` with `type === "case-management:Stage"`, keyed by `data.label`; secondary has `data.stageType === "secondary"`.
- Trigger ID from `schema.nodes[]` with `type === "uipath.case.trigger"`.
- Task name → TaskId per stage from `schema.nodes[<stage>].data.tasks[][]`.
- Variable name → `var` ID from top-level `variables.{inputs,outputs,inputOutputs}`.
- SLA/escalation and every condition/rule ID, including canonical-stub connector rules.

Optionally cross-check `id-map.json` if JSON plugins wrote it; it is only a speed-up. Never trust Phase-2 in-memory maps after the hard stop.

### Phase 3 — Execution order

Carry same-session `tasks describe`/`case spec` results in memory and persisted `tasks/registry-resolved.json`, `tasks/spec-cache.<elementId>.json`, and `tasks/trigger-spec-cache.json`. NEVER repeat an identical describe/spec call in-session (same type + id); re-read the artifact instead.

1. For every connector task, run plugin detail steps: `case spec --type {activity,trigger} --input-details`; mint `data.context[]`, `data.inputs[]`, and `data.outputs[]` from populated `caseShape` with placeholder substitution and var/id minting; apply SDD `->`/`=` output rows over `data.outputs[]` per [`io-binding/impl-json.md` § Output Binding Shapes](plugins/variables/io-binding/impl-json.md#output-binding-shapes).
2. For all task classes, bind Inputs-table rows in SDD order per [`plugins/variables/io-binding/impl-json.md`](plugins/variables/io-binding/impl-json.md): literal, expression, or cross-task reference resolved through common `.id` resolver to `=vars.<outputReferenceId>`, written to `task.data.inputs[i].value`. Connector schemas exist from step 1; values are still step 2.
3. Scan all four scopes for canonical stubs. For each resolved connector, run `case spec --type trigger --input-details` and replace only `rule.uipath`; preserve rule/condition IDs, expressions, scope, and placement. Keep/report unresolved stubs.
4. After all outputs are minted/deduped, run the whole-file sink-blind pass per [`plugins/variables/io-binding/impl-json.md § In-Expression Marker Resolution`](plugins/variables/io-binding/impl-json.md). Resolve every `vars.$xref('Stage','Task','output')` in inputs, conditions, SLA, and connector bodies to bare `vars.<outputReferenceId>`; unresolved triple/reference ID → ERROR.
5. Run end-of-Phase-3 validation per [`implementation.md § Step 12`](implementation.md): Checks 1–11 (`=vars.X`, Out-arg producer, type mismatch, `$xref`, resolved-resource I/O, entry-point parity, bindings sidecar parity, output-ID uniqueness, resource emission/repair preservation, formal-arg slot ID, resourceKey self-consistency). AskUserQuestion for unresolved references (including `$xref`), pure orphan Out-args, unbound required inputs, and phantom output fields; option (c)/(d) `continue with best-effort emit` preserves progress. Checks 6–11 are non-interactive: where allowed, auto re-run/regenerate/re-mint once; Check 6 logs if divergent, Checks 7, 9, 10, 11 halt before Phase 4 if still divergent.

No Phase-3 exit gate; proceed to Phase 4. Sole blockers are Check 7 parity, Check 9 emission/preservation, Check 10 malformed formal-arg slot ID, Check 11 resourceKey inconsistency, Check 12 missing resolved connector `context`/root bindings, or Check 15 missing task entry rule after repair; halt per [`implementation.md § Step 12`](implementation.md).

## Phase 4 — Validate

Run at end of detail mutations:

```bash
uip maestro case validate "<caseplan.case path>" --strict --sdd sdd.md --output json
```

`--strict` adds case-wide/per-task checks: empty stage (`STRICT_STAGE_NO_TASKS`); `$xref(`, `<-`/`->`, or unbound `vars.<x>` (`CASE_MGMT_XREF_UNRESOLVED`, `CASE_MGMT_PLANNING_NOTATION`, `CASE_MGMT_REFERENCE_UNBOUND`); hoisted `conditionExpression` (`CASE_MGMT_CONDITION_EXPR_HOISTED`); duplicate output IDs (`CASE_MGMT_OUTPUT_ID_DUPLICATE`) and SLA IDs (`CASE_MGMT_SLA_ID_DUPLICATE`) (these six fail every profile); incomplete connector `caseShape.context` or missing Activity Type ID (`STRICT_CONNECTOR_*`); empty `data` (`TASK_NOT_CONFIGURED`, warning; with `--sdd`, `STRICT_SDD_PLACEHOLDER_RESOLVED` error when SDD resolved it); malformed output/formal-argument shape (`STRICT_OUTPUT_*`); unbound/non-`=vars.<id>` input (`STRICT_INPUT_UNBOUND`/`STRICT_INPUT_REF_FORM`). `--sdd <path>` implies `--strict` and audits every SDD-declared stage, task, task type, condition row, SLA, trigger, and case variable (`STRICT_SDD_*`). Issues include code, path, and message; fix the named element with targeted Edit and rerun. `--strict` cannot combine with `--skeleton`/`--skeleton-v2`.

If CLI rejects `--strict` unknown, rerun without it and record `strict validate unavailable`; `Valid` without `--strict` is not evidence strict checks passed. Both flags exist from CLI 1.202; only `invalid_argument` naming them permits plain validate. Apply [case-commands.md § Version guard](case-commands.md#version-guard----strict----sdd-require-cli-1202) and log fallback.

Success is `{ Result: "Success", Code: "CaseValidate", Data: { File, Status: "Valid", Profile: "strict" } }`; proceed to issue-log summary. Failure lists `[error]`/`[warning]` with path/message; fix and rerun.

### Validate-loop guard — no re-validate without an intervening edit

Never run `uip maestro case validate` unless `caseplan.case` or a validated sidecar changed since the last run. Applies every phase: Phase 2 informational validate once; Phase 4 once per fix. `validate → validate` is illegal; only `fix → edit → validate`.

### Retry policy

Read each `Data.Issues[]` path and repair it; do not inspect installed CLI (`node_modules/@uipath/**/dist`). A partial strict build is not a stop: unbuilt stages produce `STRICT_STAGE_NO_TASKS`, one `STRICT_SDD_TASK_MISSING` per declared task, and one `STRICT_SDD_CONDITION_MISSING` per row; judge only built stages. Keep repairing while errors fall. Each retry requires a fix edit. A complete build may need six to nine rounds. Halt only after two consecutive unchanged fix→validate rounds or 12 rounds; never drop `--strict --sdd`. At halt AskUserQuestion with:

- `Retry with fix` — attempt fix and rerun; counter does not reset.
- `Pause for manual edit` — exit mid-flight; user edits `caseplan.case` and reruns.
- `Abort` — append current buffer to `build-issues.md`, summarize, never replace; leave artifacts.

### Findings whose names mislead

| Code | Actual meaning |
|---|---|
| `CASE_MGMT_ROOT_CASE_CONDITION_RULE_USER_SELECTED_STAGE_MISSING` | Does not inspect selector; checks whether any other stage has a `wait-for-user` exit condition. Repair that other stage, not the named stage. |
| `STRICT_CONNECTOR_CONTEXT_INCOMPLETE` | Tests presence by name, not values. All seven `connectorKey`, `connection`, `resourceKey`, `folderKey`, `objectName`, `operation`, `metadata` must exist; `""` satisfies presence. Values are checked by `CASE_MGMT_CONNECTOR_RESOURCE_KEY_UNRESOLVED`, `STRICT_CONNECTOR_ACTIVITY_TYPE_ID`. |
| `CASE_MGMT_STAGE_ALL_EXIT_CONDITIONS_MISSING_ERROR` | Warning; `_ERROR` is upstream naming. |
| `TASK_NOT_CONFIGURED` | Fires only when `data` has zero keys; `data: { inputs: [] }` does not. Placeholder detector, not completeness check. |

`CASE_MGMT_STAGE_ENTRY_CONDITION_MISSING` and `CASE_MGMT_STAGE_EXIT_CONDITION_MISSING` are plan-wide suppressed when any case-manager stage has tasks; read `marksStageComplete` directly. `CASE_MGMT_ROOT_ROOT_` (doubled) is the external canvas spelling that fires; single-`ROOT_` forms of those three codes are unreachable from CLI.

### Summarize the issue log

`tasks/build-issues.md` is flushed at every section boundary from Phase 2 per [`plugins/logging/impl-json.md` § Flush](plugins/logging/impl-json.md). After successful validate, flush the final buffer, read the journal, and fill grouped summary; file is source of truth. If absent, reconstruct from artifacts and stamp `NOTE:` per [§ Recovery](plugins/logging/impl-json.md). Then Phase 5.

## Phase 5 — Publish

After Phase 4, report and AskUserQuestion:

- `Publish to Studio Web`: run `uip solution resources refresh --solution-folder "<SolutionDir>" --output json`, then run `uip solution upload "<SolutionDir>" --output json --output-filter "{Status: Status, Action: Action, SolutionId: SolutionId, DesignerUrl: DesignerUrl}"`; print `DesignerUrl` alone and whether `Action` was `Imported` or `Overwritten`; proceed to Phase 6.
- `Skip to Debug`: proceed without publishing.

Before prompt print `Suggested next steps: publish to Studio Web when you want a designer-visible version, or skip to debug if the local artifacts are enough for now.` After success print `Suggested next steps: open the Designer URL, verify resources and connections, then run a debug session to exercise the case.`

Report before prompt: (1) `caseplan.case` path; (2) stages/tasks/conditions/SLA summary; (3) validate pass and warnings; (4) every placeholder (TaskId, type, display-name, stage), external resource requiring registration (task-type-id / connection-id), and `wiringNotes` from `tasks/registry-resolved.json`; under **Not covered**, every SDD item outside `caseplan.case` (for example Data Fabric entity schemas); separately list inline-built agents/API workflows/business rules and built-but-unreferenced (reject case), which need no user action. See [placeholder-tasks.md § Completion-Report Shape](placeholder-tasks.md#completion-report-shape). (5) missing IS connections; (6) suggested line, mentioning placeholder/connection fixes before publish when present.

### Publish notes

`uip solution upload` accepts the solution directory (folder containing `.uipx`) directly; no intermediate bundling. `--output-filter` is mandatory on every upload (see [case-commands.md § uip solution upload](case-commands.md#uip-solution-upload)); run `uip solution resources refresh` first to sync `bindings_v2.json` (Rule 15). Do **not** run `uip solution pack` + `uip solution publish` here; that is Phase 7. Publish is unexercised; Debug follows. If Phase 6 fix changes the build, AskUserQuestion `Re-publish the fixed build` / `Skip re-publish`; on republish rerun refresh + upload, overwriting current Studio Web state; on skip leave it.

## Phase 6 — Debug

After Phase 5, AskUserQuestion:

<!--skill-flavor:phase-six-run-option:start-->
- `Run debug session` — run `uip solution resources refresh --solution-folder "<SolutionDir>" --output json`, then run `uip maestro case debug "<directory>/<solutionName>/<projectName>" --log-level debug --output json`; stream results.
<!--skill-flavor:phase-six-run-option:end-->
- `Continue to publish` — proceed to Phase 7.

> **Debug executes case for real — sends emails, posts messages, calls APIs, writes to databases. Only run when user explicitly asks. Never auto-run** (Rule 13).

<!--skill-flavor:phase-six-requirements:start-->
Requires `uip login`. Uploads to Studio Web, runs in Orchestrator, streams results.
<!--skill-flavor:phase-six-requirements:end-->

Before prompt: `Suggested next steps: run a debug session if you are ready to exercise the case, or continue to the Orchestrator publish gate if validation (and publish) is enough for now.` After results: `Suggested next steps: inspect the debug output, fix and re-run, re-publish with the Phase 5 commands if a fix changed the build, or continue to the Orchestrator publish gate.` Return to prompt after debug; leave only on `Continue to publish`.

### Debug notes

Run `uip solution resources refresh` before debug (Rule 15). Debug verifies end-to-end execution; for fixable failures see [Step 15a — Troubleshoot failed case](implementation.md#step-15a--troubleshoot-failed-case), then rerun and republish if already published.

Inline-built siblings are NOT provisioned by `case debug`: agent/API workflow faults incident `170007` ("job's associated process could not be found"), business rule faults `300400` ("the job carries no debug session properties"). Runtime verification requires full deploy: `uip maestro case pack` → `uip solution pack` → `uip solution publish` → `uip solution deploy run`; `case pack` first, always, per [§ Phase 7](#why-case-pack-is-mandatory), and beyond [§ Phase 7](#phase-7--publish-to-orchestrator), which stops at publish. Offer via AskUserQuestion, never unprompted: `Run full solution deploy` / `Skip (mark debug-unverifiable)`. If skipped, report debug-unverifiable and continue. See [api-workflow/planning.md § Creating an API workflow inline](plugins/tasks/api-workflow/planning.md#creating-an-api-workflow-inline) / [business-rule/planning.md § Creating a business rule inline](plugins/tasks/business-rule/planning.md#creating-a-business-rule-inline).

## Phase 7 — Publish to Orchestrator

After Phase 6, AskUserQuestion: `Publish to Orchestrator` (run all commands in order) / `Done` (exit without publishing).

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

Run `resources refresh` first to sync artefacts/debug overwrites from `bindings_v2.json` (Rule 15). Run `case pack` every time, with output `<SolutionDir>/dist` (a sibling of the project dir — stray folders under the solution root are not bundled; never point it inside the case project directory); it recompiles `caseplan.case` to `caseplan.case.bpmn` in the case project. Its `.nupkg` is throwaway; only `.bpmn` matters. Run `solution pack` on the solution directory (folder containing `.uipx`), not case project; it bundles project `.nupkg` files into one `<SolutionName>_<version>.zip` in `<SolutionDir>/dist`. Add `--version <version>` when named; default `1.0.0`; duplicate `name+version` is rejected, so bump on redeploy. Run `solution publish` on the zip with `--wait`; add `--personal-workspace` only when requested. Flags: [case-commands.md § uip solution publish](case-commands.md#uip-solution-publish).

Read `<packagePath>` from `solution pack` response `Data.Packages` or list `<SolutionDir>/dist`; never guess. Zip uses underscore (`<name>_<version>.zip`), never dot. `case pack` output is `<Name>.case.Case.<version>.nupkg`; never publish it.

### Why `case pack` is mandatory

`uip solution pack` bundles on-disk `.bpmn` and never compiles it; validate does not compile it. Only `uip maestro case pack` compiles `caseplan.case` → `caseplan.case.bpmn`. Run it on every Phase 7 pass whether Phases 5/6 ran or `.bpmn` exists. Skipping can publish absent or stale `.bpmn` while pack/publish succeed and deployment later fails. `case pack` requires `package-descriptor.json` in the case project (written at scaffold, [plugins/case/impl-json.md](plugins/case/impl-json.md)); if `Missing package-descriptor.json`, restore it, never skip. `case pack` is not the publish artifact; always publish the `solution pack` zip.
<!--skill-flavor:phase-seven-commands:end-->

Phase 7 stops at publish. `uip solution deploy run` is out of scope; report package and tell user to deploy from Orchestrator.

### On failure

<!--skill-flavor:phase-seven-on-failure:start-->
If `case pack`, `solution pack`, or `publish` fails, print CLI error verbatim, note it in `build-issues.md`, and re-show Phase 7 prompt. Do not retry with a different pack command or bypass failed `case pack`; that risks missing/stale `.bpmn`. A `processKey` collision means existing `name+version`; rerun with bumped `--version`.
<!--skill-flavor:phase-seven-on-failure:end-->

### Suggested next steps

<!--skill-flavor:phase-seven-next-steps:start-->
Before prompt: `Suggested next steps: publish to Orchestrator when you want the case on the tenant solution feed, or stop here if Studio Web and debug are enough.` After success: `Suggested next steps: verify the package with 'uip solution packages list', then deploy it to an Orchestrator folder.` On `Done`: `Suggested next steps: review caseplan.case locally, or update sdd.md and re-run when you want changes.`
<!--skill-flavor:phase-seven-next-steps:end-->

### Publish-to-Orchestrator notes

Phase 7 is last; nothing re-enters the build pipeline. It does not replace Phase 5; Studio Web and solution feed are separate destinations. If a Phase 6 fix follows a Phase 7 publish, rerun Phase 7 with bumped `--version`; duplicate `name+version` is rejected. Deployment/activation uses platform lifecycle workflow and `uip solution deploy ...` commands. For authoring changes, update `sdd.md` and rerun from Phase 1; no in-place incremental edits.

## Placeholder tasks — unchanged semantics

Placeholders are unresolved-resource tasks with empty `data: {}`. Phase 2 creates them; Phase 3 does not type-upgrade them; external registration is required. See [placeholder-tasks.md](placeholder-tasks.md). Inline-created agents/API workflows/business rules are not placeholders: Rule 18 Create builds, registers, and binds them as resolved Phase-2 tasks; only declined/skipped/failed builds are placeholders. See [registry-discovery.md § Create-on-Missing](registry-discovery.md#create-on-missing-build-and-rediscovery).

Phase 3 still wires placeholder TaskIds into task-entry conditions and stage-exit `selected-tasks-completed` rules. It does not write placeholder `data.inputs`/`data.outputs`; binding waits for user upgrade.

## Abort semantics

Abort is possible at the Phase 2 first prompt (pause only), Phase 2 post-review prompt, and Phase 4 retry-cap prompt. For every abort: append current buffer to `build-issues.md` and fill summary (append-only, never whole-file replacement), print paths, exit; never delete or roll back artifacts. User owns partial state.

## Out of scope

- **Re-ingesting Studio Web edits.** Published placeholder edits are not round-tripped to local `caseplan.case`; Phase 3 writes local state and Phase 5 overwrites Studio Web with completed local build.
- **Resuming aborted session.** Rerun repeats Phase 1 resolution (refreshing `registry-resolved.json`) and executes Phase 2 onward from `sdd.md` (Rule 7).

<!-- END: phased-execution.md -->