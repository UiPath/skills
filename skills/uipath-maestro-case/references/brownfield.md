# Brownfield — Edit an Existing Case

Targeted changes to an existing `caseplan.json`. Skips the Phase 0–6 build pipeline. Terminates at `validate`, then hands off to Phase 5 (publish) / Phase 6 (debug).

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

Most "edit an existing case" requests mean a case **deployed in Studio Web**, not just a local file. Editing the local `caseplan.json` and re-publishing (Phase 5 `uip solution upload`) **overwrites server state** — if the case changed in Studio Web after the local copy was made, the upload silently clobbers those changes, with no diff and no conflict check. Reconcile **before** the first edit.

1. **Determine where the case lives.** If not already known, AskUserQuestion: `Edit my Studio Web case (pull latest first)` (default) / `Edit a local-only project (no pull)`.
2. **Lives in Studio Web (has a SolutionId)** → pull current server state into the working dir before editing:
   - Standalone export: `uip solution download <SolutionId> -d <WorkingDir> --extract --output json` — exports the `.uis` archive and unpacks it; edit the extracted project.
   - Already-linked local solution project: `uip solution projects resync --project-name <ProjectName> --sync-option Sync --output json`.
   - SolutionId unknown → ask the user for it; never guess.
   - `--extract` / `resync` **overwrite the destination**. Run before any edit. If you have already edited the local copy this session, pulling discards those edits — confirm with the user first.
3. **Local-only project (no SolutionId)** → proceed as today, no pull.
4. The pull is a CLI boundary operation (like `uip solution upload`), not a Rule 13 artifact mutation — it runs once, before editing. After it, all edits resume via Read/Write/Edit only.

Record the outcome (pulled from SW at `<SolutionId>`, or local-only) for the freshness note in [Completion Output](#completion-output).

> Brownfield edits in place; only the explicit rebuild choice below escalates. Before mutation, load the canonical [root/ID mechanics](case-editing-operations.md#responsibilities-of-direct-json-authoring) and [preservation ledger](case-editing-operations.md#per-section-batch-write-contract--canonical).

## Large or sweeping edits

Edit size never changes the journey — many edits still stay brownfield (in-place, IDs preserved). No complexity threshold escalates to greenfield. Batch multi-edit passes per [case-editing-operations.md § Per-section batch write contract](case-editing-operations.md#per-section-batch-write-contract--canonical): one `validate` at the end, not per edit.

When an edit touches many nodes or reads like "rebuild this case", confirm scope first via AskUserQuestion — `Edit in place` (default) vs `Rebuild from an updated spec` (greenfield via [planning.md](planning.md), re-mints IDs). Only an explicit rebuild choice or a new/updated `sdd.md` escalates to greenfield.

## Read this first

- **All mutations via Read/Write/Edit only** (Rule 13). CLI never mutates the case file in place: metadata fetches (`uip maestro case tasks describe`, `uip maestro case spec`, `is resources/triggers describe`), `uip maestro case validate`, the pre-edit pull (`uip solution download` / `solution projects resync` — see [§ Pull latest first](#pull-latest-first-before-editing)), and (on handoff) `uip solution resources refresh` / `uip solution upload` / `uip maestro case debug`. No `python`/`node`/`jq`/`sed`/`awk`/helper scripts touching the file.
- **`id-map.json` may be absent.** When editing a `caseplan.json` not built in this session, the `id-map.json` sidecar may not exist. Read node IDs directly from `caseplan.json`; do not assume the sidecar is present. If absent, do not synthesize one.
- **Sweep consumers before destructive or identity-bearing edits.** Use [case-editing-operations.md § Canonical consumer sweep](case-editing-operations.md#canonical-consumer-sweep) once; operation recipes must not substitute narrower lists.
- **Load only the selected route.** Every edit uses the universal primitives plus the exact owner(s) in its row. Load [the composite guide](brownfield-operations-guide.md) only for a row that links it; select one task, trigger, or condition owner rather than reading siblings.
- **Connector edits need a metadata fetch first.** Adding/altering a connector-activity task or connector-bound rule requires `uip maestro case spec --type ...` (or `tasks describe`) before authoring the shape — never hand-author connector schemas. See [connector-integration.md](connector-integration.md).
- **Universal mechanics and simple operations** live in [case-editing-operations.md](case-editing-operations.md). This document only selects owners.

## Common edits

| Edit | Operation + recipe |
|---|---|
| Update one owner-declared non-coordinated scalar (specialized rows below take precedence) | [update primitive](case-editing-operations.md#update-one-property-in-place) + the selected owner from its [dispatch table](case-editing-operations.md#quick-reference--operation-to-plugin) |
| Add a stage | [add-node primitive](case-editing-operations.md#add-a-node-trigger--stage) + [stage owner](plugins/stages/impl-json.md) + [stage-entry owner](plugins/conditions/stage-entry-conditions/impl-json.md) |
| Insert a stage between existing stages | [composite recipe](brownfield-operations-guide.md#insert-a-stage-between-two-existing-stages) + [stage owner](plugins/stages/impl-json.md) + selected stage [entry](plugins/conditions/stage-entry-conditions/impl-json.md) / [exit](plugins/conditions/stage-exit-conditions/impl-json.md) owner |
| Add a task to a stage | [add-task primitive](case-editing-operations.md#add-a-task-to-a-stage) + one selected task owner from the [dispatch table](case-editing-operations.md#quick-reference--operation-to-plugin) |
| Bind / change a task input | [bind primitive](case-editing-operations.md#bind-an-input) + [binding owner](bindings-and-expressions.md) |
| Move a task to another stage or lane | [composite recipe](brownfield-operations-guide.md#move-a-task-to-a-different-stage-or-lane) + one selected task owner from the [dispatch table](case-editing-operations.md#quick-reference--operation-to-plugin) + [task-entry owner](plugins/conditions/task-entry-conditions/impl-json.md) |
| Remove / delete a task | [case-editing-operations.md § Delete a task](case-editing-operations.md#delete-a-task) + the deleted task's selected owner from the [dispatch table](case-editing-operations.md#quick-reference--operation-to-plugin); for cache cleanup, an activity also loads [connector integration](connector-integration.md), while a wait task loads [connector trigger common](connector-trigger-common.md) |
| Add / change a condition | exactly one owner: [stage entry](plugins/conditions/stage-entry-conditions/impl-json.md), [stage exit](plugins/conditions/stage-exit-conditions/impl-json.md), [task entry](plugins/conditions/task-entry-conditions/impl-json.md), or [case exit](plugins/conditions/case-exit-conditions/impl-json.md) |
| Modify a condition rule in place | [modify primitive](case-editing-operations.md#modify-a-condition-rule-in-place) + exactly one matching condition owner from the preceding row |
| Delete a condition rule (plain or connector, any scope) | [case-editing-operations.md § Delete a condition rule](case-editing-operations.md#delete-a-condition-rule) + its exact condition owner; a connector rule also loads [connector trigger common](connector-trigger-common.md) and [sidecar sync](bindings-v2-sync.md) |
| Remove a case-exit completion / exit rule | [case-editing-operations.md § Delete a case-exit completion rule](case-editing-operations.md#delete-a-case-exit-completion-rule) |
| Replace a placeholder task | [composite recipe](brownfield-operations-guide.md#replace-a-placeholder-task-with-an-enriched-task) + [registry gate](registry-discovery.md) + [placeholder owner](placeholder-tasks.md) + one task owner from the [dispatch table](case-editing-operations.md#quick-reference--operation-to-plugin) + [sidecar owner](bindings-v2-sync.md) |
| Re-sync a task schema | [composite recipe](brownfield-operations-guide.md#re-sync-a-task-after-its-source-schema-changed) + [registry](registry-discovery.md) or [connector](connector-integration.md) metadata owner + one task owner from the [dispatch table](case-editing-operations.md#quick-reference--operation-to-plugin) + [I/O binding](plugins/variables/io-binding/impl-json.md) / [expression binding](bindings-and-expressions.md) owners for affected I/O + conditional [sidecar owner](bindings-v2-sync.md) |
| Repoint a non-connector resource task | [composite recipe](brownfield-operations-guide.md#repoint-a-non-connector-task-at-a-different-resource) + [registry owner](registry-discovery.md) + one task owner from the [dispatch table](case-editing-operations.md#quick-reference--operation-to-plugin) + [resource binding](plugins/variables/bindings/impl-json.md) / [sidecar](bindings-v2-sync.md) owners + [I/O binding](plugins/variables/io-binding/impl-json.md) / [expression binding](bindings-and-expressions.md) owners when its schema changes |
| Replace a trigger type | [composite recipe](brownfield-operations-guide.md#replace-a-trigger-with-a-different-type) + one target owner ([manual](plugins/triggers/manual/impl-json.md), [timer](plugins/triggers/timer/impl-json.md), or [event](plugins/triggers/event/impl-json.md)) + [variable owner](plugins/variables/global-vars/impl-json.md); when either source or target is event, also load the [event owner](plugins/triggers/event/impl-json.md) and [connector trigger common](connector-trigger-common.md); then [entry-point](entry-points-sync.md) and conditional [sidecar](bindings-v2-sync.md) owners |
| Re-target an event trigger | [composite recipe](brownfield-operations-guide.md#re-target-an-event-trigger-same-type-different-event) + [connector trigger](connector-trigger-common.md) / [event](plugins/triggers/event/impl-json.md) / [variable](plugins/variables/global-vars/impl-json.md) / [entry-point](entry-points-sync.md) / [sidecar](bindings-v2-sync.md) owners |
| Convert primary / exception Stage | [composite recipe](brownfield-operations-guide.md#convert-a-stage-tofrom-an-exception-stage) + [stage owner](plugins/stages/impl-json.md) + selected stage [entry](plugins/conditions/stage-entry-conditions/impl-json.md) / [exit](plugins/conditions/stage-exit-conditions/impl-json.md) owner |
| Re-wire a stage transition | [composite recipe](brownfield-operations-guide.md#re-wire-a-stage-transition--no-edges) + [stage-entry owner](plugins/conditions/stage-entry-conditions/impl-json.md) and [stage-exit owner](plugins/conditions/stage-exit-conditions/impl-json.md) only for a divergent source exit |
| Delete a node (incl. a stage with successors — repoint their entry conditions) | [case-editing-operations.md § Delete a node](case-editing-operations.md#delete-a-node) + each removed connector target's task/condition owner; for cache cleanup load [connector integration](connector-integration.md) for activities and [connector trigger common](connector-trigger-common.md) for events, waits, or rules |
| Delete a trigger (prune entry point + In-arg cascade) | [case-editing-operations.md § Delete a node](case-editing-operations.md#delete-a-node) + its trigger owner; an event source also loads [event](plugins/triggers/event/impl-json.md), [connector common](connector-trigger-common.md), [global variables](plugins/variables/global-vars/impl-json.md), and [sidecar sync](bindings-v2-sync.md) |
| Add SLA / escalation | [plugins/sla/impl-json.md](plugins/sla/impl-json.md) |
| Modify / remove an SLA or escalation | [composite recipe](brownfield-operations-guide.md#modify-or-remove-an-sla-or-escalation) + [SLA owner](plugins/sla/impl-json.md) + [response owner](sla-response-shapes.md) |
| Add a global variable / argument | [variable owner](plugins/variables/global-vars/impl-json.md) + [entry-point sync](entry-points-sync.md) when adding an In/Out argument |
| Rename / delete a global variable or argument | [composite recipe](brownfield-operations-guide.md#rename-or-delete-a-global-variable-or-argument) + [variable owner](plugins/variables/global-vars/impl-json.md) + [entry-point sync](entry-points-sync.md) for an In/Out argument |
| Change a variable's type or default | [composite recipe](brownfield-operations-guide.md#change-a-variables-type-or-default) + [variable owner](plugins/variables/global-vars/impl-json.md) + [entry-point sync](entry-points-sync.md) for an In/Out argument |
| Add or repair an SLA at-risk / breach response | [composite recipe](brownfield-operations-guide.md#add-or-repair-an-sla-response) + [response owner](sla-response-shapes.md) + [SLA owner](plugins/sla/impl-json.md) for notify-only or any escalation mutation + only the selected task owner from the [dispatch table](case-editing-operations.md#quick-reference--operation-to-plugin), [stage owner](plugins/stages/impl-json.md), or exact condition owner above |

## SLA responses in a brownfield edit

[Composite recipe](brownfield-operations-guide.md#add-or-repair-an-sla-response).

## After edits

1. **Validate** — `uip maestro case validate <ProjectName>/caseplan.json --output json`. Authoritative; retry ≤3, fix on failure. On 3rd failure HARD STOP: AskUserQuestion `Retry with fix` / `Pause for manual edit` / `Abort` (same contract as Phase 4).
2. **Any edit that adds, removes, or repoints a resource binding — connector OR non-connector** — regenerate `bindings_v2.json` per [bindings-v2-sync.md](bindings-v2-sync.md), then `uip solution resources refresh --solution-folder <SolutionDir> --output json` (Rule 14) before any debug/publish. `bindings_v2.json` holds non-connector bindings too (process/agent/rpa/action/api-workflow/case-management — [bindings-v2-sync.md § What `resource refresh` produces](bindings-v2-sync.md#what-resource-refresh-produces)); a stale file makes `uip solution upload` / `debug` throw "Resource is not configured". A pure schema-only re-sync (same resource, no binding change) needs no refresh.

## Completion Output

Report: file path edited, what changed (nodes/tasks/conditions added/removed/modified), validation status, any placeholder tasks still unresolved, any connector connections the user must create, and a **freshness note** — whether the local copy was pulled from Studio Web first (so re-publish reflects current server state) or is a local-only project not synced from SW (re-publish overwrites whatever is on the server). Then include `Suggested next steps` in one short line before AskUserQuestion "What's next": publish when ready to update Studio Web, run debug if the edit changes runtime behavior, or stop and inspect the local diff.

| Option | What it does |
|---|---|
| **Publish to Studio Web** | Phase 5 — `uip solution resources refresh` then `uip solution upload <SolutionDir> --output json --output-filter "{Status: Status, SolutionId: SolutionId, DesignerUrl: DesignerUrl}"` (filter mandatory — see [case-commands.md § uip solution upload](case-commands.md#uip-solution-upload)), print DesignerUrl. |
| **Run debug session** | Phase 6 — executes the case for real (consent-gated, Rule 12). |
| **Done** (default) | Stop here. |
| **Something else** | Free-form. |

Do not run debug or publish without explicit selection. On selection, follow the existing [phased-execution.md](phased-execution.md) Phase 5 / Phase 6 contracts.
