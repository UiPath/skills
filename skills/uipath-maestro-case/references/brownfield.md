# Brownfield — Edit an Existing Case

Edit an existing `caseplan.case` in place. Skip design handoff and Phase 1–7 build pipeline; stop at `validate`, then hand off to Phase 5 (publish), Phase 6 (debug), or Phase 7 (publish to Orchestrator).

> **Greenfield (new case from `sdd.md`) uses a different journey.** If `caseplan.case` does not exist or the user wants to (re)build from a spec, see [planning.md](planning.md) → [implementation.md](implementation.md) → [phased-execution.md](phased-execution.md).

## When this journey applies

Use this journey when `caseplan.case` exists and the user requests a targeted edit (adding a stage, removing a task, changing a condition, swapping a trigger, etc.). Do not use `sdd.md`, resolution, planning, or prototyping hard stops. Route via [SKILL.md](../SKILL.md#routing--greenfield-vs-brownfield).

## Kickoff — set dev expectations first

Before the first edit, present this flow once, including its decision points; do not repeat it. Emit verbatim in tone (adjust wording to fit; keep the checkpoint markers). This is an allow-listed standalone text block (see [case-editing-operations.md § Hard token cap](case-editing-operations.md)).

> This is a targeted edit to an existing case (no full rebuild). Here's the flow:
> - I confirm where the case lives and **pull the latest** if it's in Studio Web (so a re-publish can't clobber server changes).
> - I make the edit, then **validate** and fix errors.
> - **Debug** (optional) — **you choose** whether to run the case for real (live emails / API calls).
> - **Publish** (optional) — **you choose** whether to upload to Studio Web.
> - **Publish to Orchestrator** (optional) — **you choose** whether to publish the case to Orchestrator.

## Pull latest first (before editing)

Reconcile Studio Web cases before editing: stale local `caseplan.case` re-published with Phase 5 `uip solution upload` silently overwrites server changes without diff or conflict checking.

1. **Determine where the case lives.** If unknown, AskUserQuestion: `Edit my Studio Web case (pull latest first)` (default) / `Edit a local-only project (no pull)`.
2. **Studio Web (has a SolutionId):** pull server state before editing:
   - Standalone export: run `uip solution download <SolutionId> -d <WorkingDir> --extract --output json`; this exports the `.uis` archive and unpacks it for editing.
   - Linked local solution project: run `uip solution projects resync --project-name <ProjectName> --sync-option Sync --output json`.
   - If SolutionId is unknown, ask the user; never guess.
   - `--extract` / `resync` overwrite the destination. Run before any edit; if local edits already occurred this session, confirm before pulling because they will be discarded.
3. **Local-only (no SolutionId):** proceed without a pull.
4. The pull is a CLI boundary operation (like `uip solution upload`), not a Rule 14 artifact mutation; run it once before editing. Thereafter use only Read/Write/Edit for edits.
5. Find the plan by Studio Web names, newest first: `caseplan.case`, `caseplan.json`, `case.stage.json`, `default.stage.json`. Studio Web renames the plan to `caseplan.case` on first save, with a `caseplan.case.bpmn` sidecar, and reads the newest name present. Edit and validate that pulled plan; never create `caseplan.case` beside another-named plan, or vice versa, because Studio Web reads only the newest and silently ignores the other. Every `caseplan.case` path below means the plan found here.
6. If `validate` fails with `CASE_MGMT_VERSION_NEWER_THAN_SCHEMA`, stop and report that the CLI cannot validate it. Never lower the `version` field; Studio Web would read a document misstating its schema.
7. A Studio Web-saved project may have stale `bindings_v2.json`: Designer rewrites it on publish/debug, but save rewrites it only when an entry point, file name, or BPMN changes, so a Designer-added task may be absent. Packing ships it as-is. After a pull, or when the user says the project was just pulled, run `uip maestro case bindings sync "<ProjectName>/caseplan.case" --output json` before validate, pack, upload, or debug. Never edit `bindings_v2.json` by hand (Rule 14). `validate --strict` reports lag as `STRICT_BINDINGS_SIDECAR_STALE`.

Record whether the project was pulled from SW at `<SolutionId>` or was local-only for [Completion Output](#completion-output).

> **Do NOT regenerate from scratch.** SKILL.md Rule 7 ("always regenerate from scratch") is greenfield/planning only. Brownfield edits in place and preserves every node `id` / `elementId`; re-minting IDs breaks `=vars.*` references, conditions, and `entry-points.json`.

## Large or sweeping edits

Edit size does not change the journey: remain brownfield, edit in place, and preserve IDs. Batch multi-edit passes under [case-editing-operations.md § Per-section batch write contract](case-editing-operations.md#per-section-batch-write-contract--canonical), with one `validate` at the end.

For many-node or “rebuild this case” requests, confirm with AskUserQuestion: `Edit in place` (default) or `Rebuild from an updated spec` (greenfield via [planning.md](planning.md), re-mints IDs). Only an explicit rebuild choice or a new/updated `sdd.md` escalates.

## Read this first

- **Mutate only via Read/Write/Edit** (Rule 14). CLI never mutates the case file in place: metadata fetches (`uip maestro case tasks describe`, `uip maestro case spec`, `is resources/triggers describe`), `uip maestro case validate`, the pre-edit pull (`uip solution download` / `solution projects resync`—see [§ Pull latest first](#pull-latest-first-before-editing)), and handoff commands (`uip solution resources refresh` / `uip solution upload` / `uip maestro case debug`). Never use `python`/`node`/`jq`/`sed`/`awk`/helper scripts to touch the file.
- **`id-map.json` may be absent.** For a case not built this session, read node IDs directly from `caseplan.case`; do not assume or synthesize the sidecar.
- **Fetch connector metadata first.** Before adding/altering a connector-activity task or connector-bound rule, run `uip maestro case spec --type ...` (or `tasks describe`); never hand-author connector schemas. See [connector-integration.md](connector-integration.md).
- Cross-cutting mechanics (ID generation, Pre-flight Checklist, expression prefixes, and batch contract) are in [case-editing-operations.md](case-editing-operations.md); this document routes to them.

## Common edits

**Check [edit-recipes-guide.md](edit-recipes-guide.md) first.** Use its complete recipe when one covers the edit.

| Edit | Operation + recipe |
|---|---|
| Add / insert a stage | [case-editing-operations.md § Add a node](case-editing-operations.md#add-a-node-trigger--stage) + [plugins/stages/impl-json.md](plugins/stages/impl-json.md). Every regular stage needs ≥1 entry condition (Step 10). |
| Insert a stage between two existing stages | [case-editing-operations.md § Insert a stage between two existing stages](case-editing-operations.md#insert-a-stage-between-two-existing-stages) |
| Add a task to a stage | [case-editing-operations.md § Add a task to a stage](case-editing-operations.md#add-a-task-to-a-stage) + the task type's [plugins/tasks/<type>/impl-json.md](plugins/tasks/) |
| Bind / change a task input | [case-editing-operations.md § Bind an input](case-editing-operations.md#bind-an-input) + [bindings-and-expressions.md](bindings-and-expressions.md) |
| Move a task to a different stage or lane | [case-editing-operations.md § Move a task to a different stage or lane](case-editing-operations.md#move-a-task-to-a-different-stage-or-lane) |
| Remove / delete a task | [case-editing-operations.md § Delete a task](case-editing-operations.md#delete-a-task) |
| Add / change a condition (4 scopes) | the matching [plugins/conditions/<scope>/impl-json.md](plugins/conditions/) |
| Modify a condition rule in place (operator / expression / type) | [case-editing-operations.md § Modify a condition rule in place](case-editing-operations.md#modify-a-condition-rule-in-place) |
| Delete a condition rule (plain or connector, any scope) | [case-editing-operations.md § Delete a condition rule](case-editing-operations.md#delete-a-condition-rule) |
| Remove a case-exit completion / exit rule | [case-editing-operations.md § Delete a case-exit completion rule](case-editing-operations.md#delete-a-case-exit-completion-rule) |
| Replace a placeholder task with a real one | [case-editing-operations.md § Replace a placeholder task with an enriched task](case-editing-operations.md#replace-a-placeholder-task-with-an-enriched-task) + [placeholder-tasks.md](placeholder-tasks.md) |
| Re-sync a task whose source schema changed | [case-editing-operations.md § Re-sync a task after its source schema changed](case-editing-operations.md#re-sync-a-task-after-its-source-schema-changed) + the task type's [plugins/tasks/<type>/impl-json.md](plugins/tasks/) |
| Repoint a non-connector task at a different resource (swap which process/agent it runs) | [case-editing-operations.md § Repoint a non-connector task at a different resource](case-editing-operations.md#repoint-a-non-connector-task-at-a-different-resource) + the task type's [plugins/tasks/<type>/impl-json.md](plugins/tasks/) |
| Replace a trigger with a different type | [case-editing-operations.md § Replace a trigger with a different type](case-editing-operations.md#replace-a-trigger-with-a-different-type) |
| Re-target an event trigger (same type, different event) | [case-editing-operations.md § Re-target an event trigger](case-editing-operations.md#re-target-an-event-trigger-same-type-different-event) |
| Convert a Stage to/from an Exception Stage | [case-editing-operations.md § Convert a Stage to/from an Exception Stage](case-editing-operations.md#convert-a-stage-tofrom-an-exception-stage) |
| Delete a node (including a stage with successors; repoint their entry conditions) | [case-editing-operations.md § Delete a node](case-editing-operations.md#delete-a-node) |
| Delete a trigger (prune `entry-points.json` + In-arg variable cascade) | [case-editing-operations.md § Delete a node](case-editing-operations.md#delete-a-node) (Trigger branch, steps 4–5) |
| Delete a connector condition rule | [case-editing-operations.md § Delete a condition rule](case-editing-operations.md#delete-a-condition-rule) (connector cascade, step 4) |
| Add SLA / escalation | [plugins/sla/impl-json.md](plugins/sla/impl-json.md) |
| Modify / remove an SLA or escalation | [case-editing-operations.md § Modify or remove an SLA or escalation](case-editing-operations.md#modify-or-remove-an-sla-or-escalation) |
| Add a global variable / argument | [plugins/variables/global-vars/impl-json.md](plugins/variables/global-vars/impl-json.md) |
| Rename / delete a global variable or argument | [case-editing-operations.md § Rename or delete a global variable or argument](case-editing-operations.md#rename-or-delete-a-global-variable-or-argument) + [plugins/variables/global-vars/impl-json.md](plugins/variables/global-vars/impl-json.md) |
| Change a variable's type or default | [case-editing-operations.md § Change a variable's type or default](case-editing-operations.md#change-a-variables-type-or-default) + [plugins/variables/global-vars/impl-json.md](plugins/variables/global-vars/impl-json.md) |
| Add or repair a response to an SLA at-risk / breach event | [§ SLA responses in a brownfield edit](#sla-responses-in-a-brownfield-edit), then [plugins/conditions/stage-entry-conditions/impl-json.md](plugins/conditions/stage-entry-conditions/impl-json.md) |

## SLA responses in a brownfield edit

An SLA clock and response are separate edits. Choose response, status shape, and interrupting value per [sla-response-shapes.md](sla-response-shapes.md), the contract; this section defines edit scope.

- **Do not widen the edit.** A notify-only requirement means add an escalation to the target's `slaRules[].escalationRule` ([plugins/sla/impl-json.md](plugins/sla/impl-json.md)) and stop—no stage, task, or condition.
- **`start-task` adds a task, not a lane** ([sla-response-shapes.md § 1](sla-response-shapes.md#1-pick-the-response)): put the follow-up task in the breached stage, with the `sla-status-change` rule as its own task-entry condition, never as a stage-entry row (which reruns other tasks).
- **Four defects `validate` accepts:** task without an entry condition; non-interrupting lane demoted to a regular stage; `escalationId: "any"` “repaired” by repointing instead of deleting; and `start-task` authored as stage re-entry. Re-read [§ 5](sla-response-shapes.md#5-four-defects-validate-cannot-see) before finishing.
- Passing `validate` does not prove the response is correct; all four defects validate clean.

## After edits

1. **Validate:** run `uip maestro case validate <ProjectName>/caseplan.case --strict --output json` (use the default profile only if the CLI rejects `--strict`, and say so). This is authoritative; retry ≤3 and fix failures. On the 3rd failure HARD STOP and AskUserQuestion: `Retry with fix` / `Pause for manual edit` / `Abort` (same contract as Phase 4).
2. **Bindings/resources:** For any edit adding, removing, or repointing a resource binding—connector or non-connector—regenerate `bindings_v2.json` per [bindings-v2-sync.md](bindings-v2-sync.md), then run `uip solution resources refresh --solution-folder <SolutionDir> --output json` (Rule 15) before debug/publish. `bindings_v2.json` includes non-connector bindings (process/agent/rpa/action/api-workflow/function/business-rule/case-management — [bindings-v2-sync.md § What `resource refresh` produces](bindings-v2-sync.md#what-resource-refresh-produces)); stale data makes `uip solution upload` / `debug` throw "Resource is not configured". Pure schema-only re-sync (same resource, no binding change) needs no refresh. Repoint/removal also requires pruning the orphan ([bindings-v2-sync.md § Prune orphaned solution resources](bindings-v2-sync.md#prune-orphaned-solution-resources)). If step 1 reports `STRICT_BINDINGS_UNREFERENCED`, repair per [validator-codes.md § Binding cleanup](validator-codes.md#binding-cleanup--unreferenced-root-bindings) before finishing; `Valid` with that warning is not done.

## Completion Output

Report the edited file path; changed nodes/tasks/conditions; validation status; unresolved placeholder tasks; connector connections the user must create; and a **freshness note** stating whether the copy was pulled from Studio Web first (so re-publish reflects current server state) or is local-only and unsynced (so re-publish overwrites the server). Then add `Suggested next steps` in one short line before AskUserQuestion `What's next`: publish when ready to update Studio Web, run debug if runtime behavior changed, or stop and inspect the local diff.

| Option | What it does |
|---|---|
| **Publish to Studio Web** | Phase 5 — run `uip solution resources refresh`, then run `uip solution upload <SolutionDir> --output json --output-filter "{Status: Status, Action: Action, SolutionId: SolutionId, DesignerUrl: DesignerUrl}"` (filter mandatory—see [case-commands.md § uip solution upload](case-commands.md#uip-solution-upload)); print DesignerUrl and `Action` (`Imported`/`Overwritten`). |
| **Run debug session** | Phase 6 — execute the case for real (consent-gated, Rule 13). |
<!--skill-flavor:brownfield-publish-row:start-->
| **Publish to Orchestrator** | Phase 7 — run `uip maestro case pack` (mandatory BPMN recompile), then run `uip solution pack`, then run `uip solution publish` to the tenant solution feed (consent-gated, Rule 13). |
<!--skill-flavor:brownfield-publish-row:end-->
| **Done** (default) | Stop here. |
| **Something else** | Free-form. |

Do not run debug, publish, or publish to Orchestrator without explicit selection. After selection, follow [phased-execution.md](phased-execution.md) Phase 5 / Phase 6 / Phase 7 contracts.

<!-- END: brownfield.md -->