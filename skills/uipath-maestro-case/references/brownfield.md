# Brownfield — Edit an Existing Case

Targeted changes to an existing `caseplan.json`. Skips the Phase 0–6 build pipeline. Terminates at `validate`, then hands off to Phase 5 (debug) / Phase 6 (publish).

> **Greenfield (new case from `sdd.md`) uses a different journey.** If `caseplan.json` does not yet exist, or the user wants to (re)build from a spec, see [planning.md](planning.md) → [implementation.md](implementation.md) → [phased-execution.md](phased-execution.md) instead.

## When this journey applies

`caseplan.json` already exists AND the user wants a targeted edit ("add a stage", "remove task X", "change this condition", "swap the trigger"). No `sdd.md`, no `tasks.md`, no planning approval, no prototyping hard stop. Routing lives in [SKILL.md](../SKILL.md#routing--greenfield-vs-brownfield).

> **Do NOT regenerate from scratch.** SKILL.md Rule 6 ("always regenerate from scratch") is a greenfield/planning rule. Brownfield edits the file in place and preserves every node `id` / `elementId` — re-minting IDs breaks `=vars.*` references, conditions, and `entry-points.json`.

## Large or sweeping edits

Edit size never changes the journey — many edits still stay brownfield (in-place, IDs preserved). No complexity threshold escalates to greenfield. Batch multi-edit passes per [case-editing-operations.md § Per-section batch write contract](case-editing-operations.md#per-section-batch-write-contract--canonical): one `validate` at the end, not per edit.

When an edit touches many nodes or reads like "rebuild this case", confirm scope first via AskUserQuestion — `Edit in place` (default) vs `Rebuild from an updated spec` (greenfield via [planning.md](planning.md), re-mints IDs). Only an explicit rebuild choice or a new/updated `sdd.md` escalates to greenfield.

## Read this first

- **All mutations via Read/Write/Edit only** (Rule 13). CLI is read-only here: metadata fetches (`uip maestro case tasks describe`, `uip maestro case spec`, `is resources/triggers describe`), `uip maestro case validate`, and (on handoff) `uip solution resources refresh` / `uip solution upload` / `uip maestro case debug`. No `python`/`node`/`jq`/`sed`/`awk`/helper scripts touching the file.
- **`id-map.json` may be absent.** When editing a `caseplan.json` not built in this session, the `id-map.json` sidecar may not exist. Read node IDs directly from `caseplan.json`; do not assume the sidecar is present. If absent, do not synthesize one.
- **Connector edits need a metadata fetch first.** Adding/altering a connector-activity task or connector-bound rule requires `uip maestro case spec --type ...` (or `tasks describe`) before authoring the shape — never hand-author connector schemas. See [connector-integration.md](connector-integration.md).
- **Cross-cutting mechanics** (ID generation, Pre-flight Checklist, expression prefixes, per-section batch contract) live in [case-editing-operations.md](case-editing-operations.md). This doc routes; that doc supplies the recipe.

## Common edits

| Edit | Operation + recipe |
|---|---|
| Add / insert a stage | [case-editing-operations.md § Add a node](case-editing-operations.md#add-a-node-trigger--stage--exceptionstage) + [plugins/stages/impl-json.md](plugins/stages/impl-json.md). Every regular stage needs ≥1 entry condition (Step 10). |
| Insert a stage between two existing stages | [case-editing-operations.md § Insert a stage between two existing stages](case-editing-operations.md#insert-a-stage-between-two-existing-stages) |
| Add a task to a stage | [case-editing-operations.md § Add a task to a stage](case-editing-operations.md#add-a-task-to-a-stage) + the task type's [plugins/tasks/<type>/impl-json.md](plugins/tasks/) |
| Bind / change a task input | [case-editing-operations.md § Bind an input](case-editing-operations.md#bind-an-input) + [bindings-and-expressions.md](bindings-and-expressions.md) |
| Add / change a condition (4 scopes) | the matching [plugins/conditions/<scope>/impl-json.md](plugins/conditions/) |
| Replace a placeholder task with a real one | [case-editing-operations.md § Replace a placeholder task with an enriched task](case-editing-operations.md#replace-a-placeholder-task-with-an-enriched-task) + [placeholder-tasks.md](placeholder-tasks.md) |
| Re-sync a task whose source schema changed | [case-editing-operations.md § Re-sync a task after its source schema changed](case-editing-operations.md#re-sync-a-task-after-its-source-schema-changed) + the task type's [plugins/tasks/<type>/impl-json.md](plugins/tasks/) |
| Replace a trigger with a different type | [case-editing-operations.md § Replace a trigger with a different type](case-editing-operations.md#replace-a-trigger-with-a-different-type) |
| Delete a node | [case-editing-operations.md § Delete a node](case-editing-operations.md#delete-a-node) |
| Delete a connector condition rule | [case-editing-operations.md § Delete a connector condition rule](case-editing-operations.md#delete-a-connector-condition-rule) |
| Add SLA / escalation | [plugins/sla/impl-json.md](plugins/sla/impl-json.md) |
| Add a global variable / argument | [plugins/variables/global-vars/impl-json.md](plugins/variables/global-vars/impl-json.md) |

## After edits

1. **Validate** — `uip maestro case validate <ProjectName>/caseplan.json --output json`. Authoritative; retry ≤3, fix on failure. On 3rd failure HARD STOP: AskUserQuestion `Retry with fix` / `Pause for manual edit` / `Abort` (same contract as Phase 4).
2. **Connector add/remove only** — regenerate `bindings_v2.json` per [bindings-v2-sync.md](bindings-v2-sync.md), then `uip solution resources refresh --solution-folder <SolutionDir> --output json` (Rule 14) before any debug/publish.

## Completion Output

Report: file path edited, what changed (nodes/tasks/conditions added/removed/modified), validation status, any placeholder tasks still unresolved, any connector connections the user must create. Then AskUserQuestion "What's next":

| Option | What it does |
|---|---|
| **Run debug session** | Phase 5 — executes the case for real (consent-gated, Rule 12). |
| **Publish to Studio Web** | Phase 6 — `uip solution resources refresh` then `uip solution upload`, print DesignerUrl. |
| **Done** (default) | Stop here. |
| **Something else** | Free-form. |

Do not run debug or publish without explicit selection. On selection, follow the existing [phased-execution.md](phased-execution.md) Phase 5 / Phase 6 contracts.
