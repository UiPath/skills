# case-management task — Planning

A nested case task. Invokes another case definition as a sub-case within the current one. Enables hierarchical / recursive case structures.

## When to Use

Pick this plugin when the sdd.md describes a task that spawns or delegates to another case definition. Typical patterns:

- Parent case orchestrates multiple sub-cases
- Long-running sub-workflow packaged as its own case

If sdd.md describes a simple stage-to-stage flow within the same case, do not use this — use regular stages and edges.

## Required Fields from sdd.md

| Field | Source | Notes |
|-------|--------|-------|
| `display-name` | Case Reference "Name" | |
| `name` | Case Reference "Name" | |
| `folder-path` | Resolved registry `folders[0].fullyQualifiedName` (NOT the sdd.md "Folder") | Binds to `data.folderPath`; Orchestrator starts the sub-case here at runtime. The sdd.md "Folder" only seeds the lookup and may be a parent/truncated path. See [§ Registry Resolution](#registry-resolution). |
| `task-type-id` | Registry resolution (below) | `entityKey` in `caseManagement-index.json` |
| `inputs` | sdd.md task data mapping | Passed as case-instance inputs to the sub-case |
| `outputs` | Discovered via `tasks describe` | Returned when the sub-case completes |
| `runOnlyOnce` | sdd.md (default `true`) | |
| `isRequired` | sdd.md (default `true`) | |

## Registry Resolution

1. **Primary cache file:** `caseManagement-index.json`.
2. **Identifier field:** `entityKey`.
3. Match by exact name + folder.
4. **`folder-path` = the SELECTED entry's `folders[0].fullyQualifiedName`** (not the sdd.md "Folder" — see the field table above). Fall back to the sdd.md folder only when there is no registry match (Unresolved path).
5. Discover inputs/outputs via `tasks describe` — see [bindings-and-expressions.md § Discovering output names](../../../bindings-and-expressions.md).

## Unresolved Fallback

Mark `<UNRESOLVED: case "<name>" in folder "<folder>" not found in caseManagement-index.json>`. Omit `inputs:` and `outputs:`; capture intended wiring in a fenced ```` ```text ```` code block (not `#` prefixed — it renders as markdown H1). Execution creates a placeholder task — see [placeholder-tasks.md](../../../placeholder-tasks.md). Note: if the referenced sub-case has not been deployed yet, it will not appear in the registry — the user must deploy it before the parent case can reference it.

## tasks.md Entry Format

```markdown
## T<n>: Add case-management task "<display-name>" to "<stage>"
- taskTypeId: <entityKey>
- folder-path: "<folder>"
- inputs:
  - <input_name> = "<value>"
- outputs: <out1>, <out2>
- runOnlyOnce: true
- isRequired: true
- order: after T<m>
- lane: <n>  # FE layout; increment per task. Within `runs-sequentially` group, parallel members share a lane (semantic).
- verify: Confirm Result: Success, capture TaskId
```
