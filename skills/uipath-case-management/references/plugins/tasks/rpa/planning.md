# rpa task — Planning

An RPA robot task. The sdd.md component type is `RPA`. At the CLI level, RPA tasks use `--type rpa` but the cached entity typically lives in `process-index.json` — the registry does not separate "process" from "rpa" at storage time.

## When to Use

Pick this plugin when the sdd.md explicitly labels a task as `RPA` (e.g., "RPA robot does X"). The distinction from `process` is **semantic** (sdd.md intent) rather than structural (registry representation).

If sdd.md is ambiguous between `PROCESS` and `RPA`, default to `process` unless the sdd.md mentions UI automation, desktop apps, or robot-specific concerns.

## Required Fields from sdd.md

Same shape as [process/planning.md](../process/planning.md):

| Field | Notes |
|-------|-------|
| `display-name` | from Process Reference |
| `name` | from Process Reference |
| `folder-path` | from Process Reference |
| `task-type-id` | from registry (`entityKey` in `process-index.json`) |
| `inputs`, `outputs`, `runOnlyOnce`, `isRequired` | see [bindings-and-expressions.md](../../../bindings-and-expressions.md) |

## Registry Resolution

1. **Primary cache file:** `process-index.json` (yes — RPA tasks share this cache with `process`).
2. **Identifier field:** `entityKey`.
3. Use the sdd.md `RPA` label to set `--type rpa` on the CLI; use the cache `entityKey` for `--task-type-id`.
4. If no match in `process-index.json`, search all other cache files as a fallback.
5. Discover inputs/outputs via `tasks describe` — see [bindings-and-expressions.md § Discovering output names](../../../bindings-and-expressions.md).

## Unresolved Fallback

Mark `<UNRESOLVED: rpa "<name>" in folder "<folder>" not found in registry>`. Omit `inputs:` and `outputs:`; capture intended wiring in a fenced ```` ```text ```` code block (not `#` prefixed — it renders as markdown H1). Execution creates a skeleton task — see [skeleton-tasks.md](../../../skeleton-tasks.md).

## tasks.md Entry Format

```markdown
## T<n>: Add rpa task "<display-name>" to "<stage>"
- taskTypeId: <entityKey>
- folder-path: "<folder>"
- inputs:
  - <input_name> = "<value>"
- outputs: <out1>
- runOnlyOnce: true
- isRequired: true
- order: after T<m>
- lane: <n>  # FE layout coordinate; increment per task within the stage
- verify: Confirm Result: Success, capture TaskId
```
