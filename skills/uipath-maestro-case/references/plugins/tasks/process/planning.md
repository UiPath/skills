# process task — Planning

An RPA-driven automated process task. Invokes a UiPath process (or agentic process) by name and folder.

## When to Use

Pick this plugin when the sdd.md describes a task as any of:

- `PROCESS` — a regular UiPath process
- `AGENTIC_PROCESS` — an agentic process orchestrated by UiPath
- Generic "run automation X" where X is a published process

For RPA robot tasks specifically, prefer [rpa](../rpa/planning.md). For Coded workflows / API-workflows, use [api-workflow](../api-workflow/planning.md).

## Required Fields from sdd.md

| Field | Source | Notes |
|-------|--------|-------|
| `display-name` | Process Reference "Name" | Shown in the UI |
| `name` | Process Reference "Name" | CLI flag `--name` |
| `folder-path` | Process Reference "Folder" | CLI flag `--folder-path`. Required for disambiguation. |
| `task-type-id` | Registry resolution (see below) | CLI flag `--task-type-id`. Enables auto-enrichment. |
| `inputs` | sdd.md task data mapping | See [bindings-and-expressions.md](../../../bindings-and-expressions.md) |
| `outputs` | Discovered via `tasks describe` | Listed for downstream cross-task references |
| `runOnlyOnce` | sdd.md (default `true`) | CLI flag `--should-run-only-once` |
| `isRequired` | sdd.md (default `true`) | CLI flag `--is-required` |

## Registry Resolution

1. **Primary cache file:** `process-index.json` for `PROCESS`, `processOrchestration-index.json` for `AGENTIC_PROCESS`.
2. **Identifier field:** `entityKey`.
3. **Cross-type fallback.** If the primary cache file has no match, search both files — the sdd.md label is not authoritative. A process registered as `process` may be mislabeled `AGENTIC_PROCESS` in sdd.md and vice versa.
4. **Match priority:** exact name + exact folder > exact name, multiple folders (pick matching) > exact name only > no match.
5. **Discover inputs/outputs:** after resolving the `entityKey`, fetch the input/output schema via `tasks describe` — see [bindings-and-expressions.md § Discovering output names](../../../bindings-and-expressions.md). Record input names, types, and output names. Unrecognized inputs in sdd.md → ask the user (**AskUserQuestion** with matching field names + "Something else").

## Unresolved Fallback

If no match is found across both cache files after `uip maestro case registry pull --force`:

- Mark the task line: `<UNRESOLVED: process "<name>" in folder "<folder>" not found in registry>`
- Omit `inputs:` and `outputs:`; capture intended wiring in a fenced ```` ```text ```` code block (not `#` prefixed — it renders as markdown H1).
- Continue planning for remaining tasks.
- Execution creates a skeleton task (no `--task-type-id`, no bindings). See [skeleton-tasks.md](../../../skeleton-tasks.md).

## tasks.md Entry Format

```markdown
## T<n>: Add process task "<display-name>" to "<stage>"
- taskTypeId: <entityKey>
- folder-path: "<folder>"
- inputs:
  - <input_name> = "<literal-or-expression>"
  - <input_name> <- "<Stage>"."<Task>".<output>
- outputs: <out1>, <out2>, <out3>
- runOnlyOnce: true
- isRequired: true
- order: after T<m>
- lane: <n>  # FE layout coordinate; increment per task within the stage
- verify: Confirm Result: Success, capture TaskId
```
