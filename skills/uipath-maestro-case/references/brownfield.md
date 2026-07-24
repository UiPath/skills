# Brownfield — Edit an Existing Case

Targeted changes to an existing `caseplan.json`. Skips the Phase 0–6 build pipeline. Terminates at `validate`, then hands off to Phase 5 (debug) / Phase 6 (publish).

> **Greenfield (new case from `sdd.md`) uses a different journey.** If `caseplan.json` does not yet exist, or the user wants to (re)build from a spec, see [planning.md](planning.md) → [implementation.md](implementation.md) → [phased-execution.md](phased-execution.md) instead.

## When this journey applies

`caseplan.json` already exists AND the user wants a targeted edit ("add a stage", "remove task X", "change this condition", "swap the trigger"). No `sdd.md`, no `tasks.md`, no planning phase, no prototyping hard stop. Routing lives in [SKILL.md](../SKILL.md#routing--greenfield-vs-brownfield).

## Kickoff — set dev expectations first

Before the first edit, present the flow once so the dev knows the steps and where they'll be asked to decide. Emit verbatim in tone (adjust wording to fit; keep the checkpoint markers). Present ONCE at entry; do not repeat. Allow-listed standalone text block (see [case-editing-operations.md § Hard token cap](case-editing-operations.md)).

> This is a targeted edit to an existing case (no full rebuild). Here's the flow:
> - I confirm where the case lives and **pull the latest** if it's in Studio Web (so a re-publish can't clobber server changes).
> - I make the edit, then **validate** and fix errors.
> - **Debug** (optional) — **you choose** whether to run the case for real (live emails / API calls).
> - **Publish** (optional) — **you choose** whether to upload to Studio Web.

## Pull latest first (before editing)

Most "edit an existing case" requests mean a case **deployed in Studio Web**, not just a local file. Editing the local `caseplan.json` and re-publishing (Phase 6 `uip solution upload`) **overwrites server state** — if the case changed in Studio Web after the local copy was made, the upload silently clobbers those changes, with no diff and no conflict check. Reconcile **before** the first edit.

1. **Determine where the case lives.** If not already known, AskUserQuestion: `Edit my Studio Web case (pull latest first)` (default) / `Edit a local-only project (no pull)`.
2. **Lives in Studio Web (has a SolutionId)** → pull current server state into the working dir before editing:
   - Standalone export: `uip solution download <SolutionId> -d <WorkingDir> --extract --output json` — exports the `.uis` archive and unpacks it; edit the extracted project.
   - Already-linked local solution project: `uip solution projects resync --project-name <ProjectName> --sync-option Sync --output json`.
   - SolutionId unknown → ask the user for it; never guess.
   - `--extract` / `resync` **overwrite the destination**. Run before any edit. If you have already edited the local copy this session, pulling discards those edits — confirm with the user first.
3. **Local-only project (no SolutionId)** → proceed as today, no pull.
4. The pull is a CLI boundary operation (like `uip solution upload`), not a Rule 13 artifact mutation — it runs once, before editing. After it, all edits resume via Read/Write/Edit only.

Record the outcome (pulled from SW at `<SolutionId>`, or local-only) for the freshness note in [Completion Output](#completion-output).

> **Do NOT regenerate from scratch.** SKILL.md Rule 6 ("always regenerate from scratch") is a greenfield/planning rule. Brownfield edits the file in place and preserves every node `id` / `elementId` — re-minting IDs breaks `=vars.*` references, conditions, and `entry-points.json`.

## Large or sweeping edits

Edit size never changes the journey — many edits still stay brownfield (in-place, IDs preserved). No complexity threshold escalates to greenfield. Batch multi-edit passes per [case-editing-operations.md § Per-section batch write contract](case-editing-operations.md#per-section-batch-write-contract--canonical): one `validate` at the end, not per edit.

When an edit touches many nodes or reads like "rebuild this case", confirm scope first via AskUserQuestion — `Edit in place` (default) vs `Rebuild from an updated spec` (greenfield via [planning.md](planning.md), re-mints IDs). Only an explicit rebuild choice or a new/updated `sdd.md` escalates to greenfield.

## Read this first

- **All mutations via Read/Write/Edit only** (Rule 13). CLI never mutates the case file in place: metadata fetches (`uip maestro case tasks describe`, `uip maestro case spec`, `is resources/triggers describe`), `uip maestro case validate`, the pre-edit pull (`uip solution download` / `solution projects resync` — see [§ Pull latest first](#pull-latest-first-before-editing)), and (on handoff) `uip solution resources refresh` / `uip solution upload` / `uip maestro case debug`. No `python`/`node`/`jq`/`sed`/`awk`/helper scripts touching the file.
- **`id-map.json` may be absent.** When editing a `caseplan.json` not built in this session, the `id-map.json` sidecar may not exist. Read node IDs directly from `caseplan.json`; do not assume the sidecar is present. If absent, do not synthesize one.
- **Connector edits need a metadata fetch first.** Adding/altering a connector-activity task or connector-bound rule requires `uip maestro case spec --type ...` (or `tasks describe`) before authoring the shape — never hand-author connector schemas. See [connector-integration.md](connector-integration.md).
- **Cross-cutting mechanics** (ID generation, Pre-flight Checklist, expression prefixes, per-section batch contract) live in [case-editing-operations.md](case-editing-operations.md). This doc routes; that doc supplies the recipe.

## Common edits

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
| Delete a node (incl. a stage with successors — repoint their entry conditions) | [case-editing-operations.md § Delete a node](case-editing-operations.md#delete-a-node) |
| Delete a trigger (prune `entry-points.json` + In-arg variable cascade) | [case-editing-operations.md § Delete a node](case-editing-operations.md#delete-a-node) (Trigger branch, steps 5–6) |
| Delete a connector condition rule | [case-editing-operations.md § Delete a condition rule](case-editing-operations.md#delete-a-condition-rule) (connector cascade, steps 4–6) |
| Add SLA / escalation | [plugins/sla/impl-json.md](plugins/sla/impl-json.md) |
| Modify / remove an SLA or escalation | [case-editing-operations.md § Modify or remove an SLA or escalation](case-editing-operations.md#modify-or-remove-an-sla-or-escalation) |
| Add a global variable / argument | [plugins/variables/global-vars/impl-json.md](plugins/variables/global-vars/impl-json.md) |
| Rename / delete a global variable or argument | [case-editing-operations.md § Rename or delete a global variable or argument](case-editing-operations.md#rename-or-delete-a-global-variable-or-argument) + [plugins/variables/global-vars/impl-json.md](plugins/variables/global-vars/impl-json.md) |
| Change a variable's type or default | [case-editing-operations.md § Change a variable's type or default](case-editing-operations.md#change-a-variables-type-or-default) + [plugins/variables/global-vars/impl-json.md](plugins/variables/global-vars/impl-json.md) |

## After edits

1. **Validate** — `uip maestro case validate <ProjectName>/caseplan.json --output json`. Authoritative; retry ≤3, fix on failure. On 3rd failure HARD STOP: AskUserQuestion `Retry with fix` / `Pause for manual edit` / `Abort` (same contract as Phase 4).
2. **Any edit that adds, removes, or repoints a resource binding — connector OR non-connector** — regenerate `bindings_v2.json` per [bindings-v2-sync.md](bindings-v2-sync.md), then `uip solution resources refresh --solution-folder <SolutionDir> --output json` (Rule 14) before any debug/publish. `bindings_v2.json` holds non-connector bindings too (process/agent/rpa/action/api-workflow/case-management — [bindings-v2-sync.md § What `resource refresh` produces](bindings-v2-sync.md#what-resource-refresh-produces)); a stale file makes `uip solution upload` / `debug` throw "Resource is not configured". A pure schema-only re-sync (same resource, no binding change) needs no refresh.

## Completion Output

Report: file path edited, what changed (nodes/tasks/conditions added/removed/modified), validation status, any placeholder tasks still unresolved, any connector connections the user must create, and a **freshness note** — whether the local copy was pulled from Studio Web first (so re-publish reflects current server state) or is a local-only project not synced from SW (re-publish overwrites whatever is on the server). Then AskUserQuestion "What's next":

| Option | What it does |
|---|---|
| **Run debug session** | Phase 5 — executes the case for real (consent-gated, Rule 12). |
| **Publish to Studio Web** | Phase 6 — `uip solution resources refresh` then `uip solution upload`, print DesignerUrl. |
| **Done** (default) | Stop here. |
| **Something else** | Free-form. |

Do not run debug or publish without explicit selection. On selection, follow the existing [phased-execution.md](phased-execution.md) Phase 5 / Phase 6 contracts.
