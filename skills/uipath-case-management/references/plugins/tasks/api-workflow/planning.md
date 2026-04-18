# api-workflow task — Planning

An API Workflow (formerly "Coded Workflow") task. Invokes a UiPath API workflow by entityKey.

## When to Use

Pick this plugin when the sdd.md labels a task as `API_WORKFLOW` — typically a TypeScript / C# coded workflow that exposes an API-style interface.

## Required Fields from sdd.md

| Field | Source | Notes |
|-------|--------|-------|
| `display-name` | API Workflow Reference "Name" | |
| `name` | API Workflow Reference "Name" | CLI flag `--name` |
| `folder-path` | API Workflow Reference "Folder" | CLI flag `--folder-path` |
| `task-type-id` | Registry resolution (below) | `entityKey` in `api-index.json` |
| `inputs` | sdd.md task data mapping | See [bindings-and-expressions.md](../../../bindings-and-expressions.md) |
| `outputs` | Discovered via `tasks describe` | |
| `runOnlyOnce` | sdd.md (default `true`) | |
| `isRequired` | sdd.md (default `true`) | |

## Registry Resolution

1. **Primary cache file:** `api-index.json`.
2. **Identifier field:** `entityKey`.
3. Match by exact name + folder.
4. Discover inputs/outputs via `tasks describe` — see [bindings-and-expressions.md § Discovering output names](../../../bindings-and-expressions.md).

## Unresolved Fallback

Mark `<UNRESOLVED: api-workflow "<name>" in folder "<folder>" not found in api-index.json>`. Omit `inputs:` and `outputs:`; capture intended wiring in a fenced ```` ```text ```` code block (not `#` prefixed — it renders as markdown H1). Execution creates a skeleton task — see [skeleton-tasks.md](../../../skeleton-tasks.md).

## tasks.md Entry Format

```markdown
## T<n>: Add api-workflow task "<display-name>" to "<stage>"
- taskTypeId: <entityKey>
- folder-path: "<folder>"
- inputs:
  - <input_name> = "<value>"
- outputs: <out1>, <out2>
- runOnlyOnce: true
- isRequired: true
- order: after T<m>
- lane: <n>  # FE layout coordinate; increment per task within the stage
- verify: Confirm Result: Success, capture TaskId
```
