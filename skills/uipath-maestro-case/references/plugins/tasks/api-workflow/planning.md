# api-workflow task — Planning

An API Workflow (formerly "Coded Workflow") task. Invokes a UiPath API workflow by entityKey.

## When to Use

Pick this plugin when the sdd.md labels a task as `API_WORKFLOW` — typically a TypeScript / C# coded workflow that exposes an API-style interface.

## Required Fields from sdd.md

| Field | Source | Notes |
|-------|--------|-------|
| `display-name` | Task `Task Name` | |
| `name` | Resolved registry entry's **`name` field** (NOT the sdd.md "Resolved Resource") | Binds to `data.name` AND forms the `resourceKey` suffix `<folderPath>.<name>`. The sdd.md "Resolved Resource" is only the **search query** (matches `folders[0].displayName`). For `api-index.json` the entry `name` is the literal constant **`"API Workflow"`** — NOT the workflow's own name. See [§ Registry Resolution](#registry-resolution). |
| `folder-path` | Resolved registry `folders[0].fullyQualifiedName` (NOT the sdd.md "Folder") | Binds to `data.folderPath`; Orchestrator starts the workflow here at runtime. The sdd.md "Folder" only seeds the lookup and may be a parent/truncated path. See [§ Registry Resolution](#registry-resolution). For an API workflow **built inline** as an in-solution sibling, the runtime `folder-path` is **empty `""`** (co-located — the case starts the workflow in its own deployed folder) while `resourceKey` stays `solution_folder.<name>`; do NOT put the `solution_folder` sentinel in `folder-path` (runtime `folder not exist`). See [§ Creating an API workflow inline](#creating-an-api-workflow-inline). |
| `task-type-id` | Registry resolution (below) | `entityKey` in `api-index.json` |
| `inputs` | sdd.md task data mapping | See [bindings-and-expressions.md](../../../bindings-and-expressions.md) |
| `outputs` | sdd.md task Outputs + resolved schema | Follow the shared [I/O-binding output-list contract](../../variables/io-binding/planning.md#canonical-tasksmd-output-list). |
| `runOnlyOnce` | sdd.md (default `false`) | Re-entry behavior comes from the SDD, not the task type. |
| `isRequired` | sdd.md (default `true`) | |

## Registry Resolution

1. **Primary cache file:** `api-index.json`.
2. **Identifier field:** `entityKey`.
3. **Match priority:** exact name + exact folder > exact name, multiple folders (pick matching) > exact name only > **no match**. An exact-name hit in a **different** folder — including a child of the sdd.md folder (which only seeds the lookup and **may be a parent/truncated path**, see field table) — is an **exact name only** match: **resolve it** (bind `folder-path` to the registry entry's full path per step 4). Do NOT treat a folder difference as no-match or fall through to the Create gate — the gate is only for names **no** registry entry carries at all. A true no-match runs the [§ in-solution check](#no-tenant-index-match--check-in-solution-siblings-before-the-gate) first, then the Rule 17 gate; only a task left unresolved after the gate falls back to the sdd.md folder (step 4).
4. **Take BOTH `name` and `folder-path` from the SELECTED entry, never the sdd.md** (which only seeds the lookup): `folder-path` = `folders[0].fullyQualifiedName`; `name` = the entry's `name` field (`"API Workflow"` for `api-index.json` — see field table). So `resourceKey` = `<folders[0].fullyQualifiedName>.API Workflow`, NOT `<…>.<workflow name>` — the wrong suffix passes `validate` but faults at `case debug` (process unresolvable). Fall back to the sdd.md folder/name only on no registry match (Unresolved path).
5. Discover inputs/outputs via `tasks describe` — see [bindings-and-expressions.md § Discovering output names](../../../bindings-and-expressions.md).

### No tenant-index match → check in-solution siblings BEFORE the gate

When steps 1–3 find nothing in the tenant index **and** the CLI supports `registry --local`, apply the registry owner's [Local Solution Scope](../../../registry-discovery.md#local-solution-scope), then check for an existing in-solution sibling before treating the API workflow as unresolved:

```bash
uip maestro case registry search "<name>" --type api --local --output json
```

An exact-name match with `Resource.Source == "local"` is an existing in-solution sibling: **resolve it directly** with `resourceKey="solution_folder.<name>"`; do not enter the [Rule 17 Create gate](../../../registry-discovery.md#must-confirm-before-placeholder-fallback) or load an inline-creation guide. Only a name absent from both the tenant index and local siblings reaches the gate. Read the sibling I/O from raw `entry-points.json` `entryPoints[0].input/.output.properties` (flat deploy shape); if absent, fall back to the `input.schema.document.properties` wrapper variant, then to `Workflow.json` root input/output schema properties when the entry-point I/O is `null`. Warn in the completion report whenever a fallback was used.

## Unresolved Fallback

> **Build it inline first (creatable kind).** At the [Rule 17 empty-lookup gate](../../../registry-discovery.md#must-confirm-before-placeholder-fallback) the user may pick **Create** to build the missing API workflow as an in-solution sibling — see [§ Creating an API workflow inline](#creating-an-api-workflow-inline). This fallback applies only when the user declines/skips Create, the build fails, or the CLI lacks `registry --local`.

Mark `<UNRESOLVED: api-workflow "<name>" in folder "<folder>" not found in api-index.json>`. Omit `inputs:` and `outputs:`; capture intended wiring in a fenced ```` ```text ```` code block (not `#` prefixed — it renders as markdown H1). Execution creates a placeholder task — see [placeholder-tasks.md](../../../placeholder-tasks.md).

## Creating an API workflow inline

After the shared Create flow's Select step checks this API workflow, read [Inline API Workflow Creation](inline-creation-guide.md) before pinned-I/O work or spawning its builder. Tenant-resolved, existing-local, unchecked, and fallback paths do not load that guide.

## tasks.md Entry Format

```markdown
## T<n>: Add api-workflow task "<display-name>" to "<stage>"
- name: "<resource-name>"
- taskTypeId: <entityKey>
- folder-path: "<folder>"
- inputs:
  - <input_name> = "<value>"
- outputs:
  - <SDD output row, copied verbatim>
- runOnlyOnce: false
- isRequired: true
- activation-mode: <sequential|parallel|parallel-after-predecessor|event-triggered|adhoc|fan-in|conditional-gate>   # required
- entry-rule: <copy the matching supplied/approved SDD task-entry rule>   # required; legality: ../../conditions/task-entry-conditions/planning.md#phase-1-plan-presentation-contract
- rationale: "<copy the supplied/approved SDD rationale>"   # required
- order: after T<m>
- lane: <n>  # structural/layout position only; sequencing is the task entry rule plus data.tasks order.
- verify: Confirm Result: Success, capture TaskId
```
