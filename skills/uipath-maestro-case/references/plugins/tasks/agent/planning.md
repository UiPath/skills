# agent task — Planning

An AI agent task. Invokes a UiPath Agent by entityKey for reasoning, classification, extraction, or generative work.

## When to Use

Pick this plugin when the sdd.md describes a task as `AGENT` — an AI agent that processes inputs and returns structured outputs. Use when the task requires reasoning or judgment rather than deterministic automation.

## Required Fields from sdd.md

| Field | Source | Notes |
|-------|--------|-------|
| `display-name` | Task `Task Name` | Shown in the UI |
| `name` | Task `Resolved Resource` | Concrete intended resource name and registry query |
| `folder-path` | Resolved registry `folders[0].fullyQualifiedName` (NOT the sdd.md "Folder") | Binds to `data.folderPath`; Orchestrator starts the agent here at runtime. The sdd.md "Folder" only seeds the lookup and may be a parent/truncated path. See [§ Registry Resolution](#registry-resolution). For an agent **built inline** as an in-solution sibling, the runtime `folder-path` is **empty `""`** (co-located — the case starts the agent in its own deployed folder) while `resourceKey` stays `solution_folder.<name>`; do NOT put the `solution_folder` sentinel in `folder-path` (runtime `folder not exist`). See [§ Creating an Agent inline](#creating-an-agent-inline). |
| `task-type-id` | Registry resolution (below) | Enables auto-enrichment via `tasks describe` |
| `element-id` | (optional) | Required only when the agent has multiple element bindings |
| `inputs` | sdd.md task data mapping | See [bindings-and-expressions.md](../../../bindings-and-expressions.md) |
| `outputs` | sdd.md task Outputs + resolved schema | Follow the shared [I/O-binding output-list contract](../../variables/io-binding/planning.md#canonical-tasksmd-output-list). |
| `runOnlyOnce` | sdd.md (default `false`) | Re-entry behavior comes from the SDD, not the task type.  |
| `isRequired` | sdd.md (default `true`) |  |

## Registry Resolution

1. **Primary cache file:** `agent-index.json`.
2. **Identifier field:** `entityKey`.
3. **Cross-type fallback.** Agents are occasionally registered in `processOrchestration-index.json` when wrapped in an agentic process — search both if the primary yields no match.
4. **Match priority:** exact name + exact folder > exact name, multiple folders (pick matching) > exact name only > **no match**. An exact-name hit in a **different** folder — including a child of the sdd.md folder (which only seeds the lookup and **may be a parent/truncated path**, see field table) — is an **exact name only** match: **resolve it** (bind `folder-path` to the registry entry's full path per step 5). Do NOT treat a folder difference as no-match or fall through to the Create gate — the gate is only for names **no** registry entry carries at all. A true no-match runs the [§ in-solution check](#no-tenant-index-match--check-in-solution-siblings-before-the-gate) first, then the Rule 17 gate; only a task left unresolved after the gate falls back to the sdd.md folder (step 5).
5. **`folder-path` = the SELECTED entry's `folders[0].fullyQualifiedName`** (not the sdd.md "Folder" — see the field table above). Fall back to the sdd.md folder only when there is no registry match (Unresolved path).
6. **Discover inputs/outputs** via `tasks describe` — see [bindings-and-expressions.md § Discovering output names](../../../bindings-and-expressions.md). For agents with multiple elements, also pass `--element-id` when invoking describe (see [case-commands.md § uip maestro case tasks](../../../case-commands.md)).

### No tenant-index match → check in-solution siblings BEFORE the gate

When steps 1–4 find nothing in the tenant index **and** the CLI supports `registry --local`, apply the registry owner's [Local Solution Scope](../../../registry-discovery.md#local-solution-scope), then check for an existing in-solution sibling before treating the agent as unresolved.

```bash
uip maestro case registry search "<name>" --type agent --local --output json
```

An exact-name match with `Resource.Source == "local"` means the agent **already exists as an in-solution sibling**. Resolve it directly and do not enter Rule 17: bind by name/folder with `resourceKey="solution_folder.<name>"`, and read case-preserving I/O from on-disk `entry-points.json` `entryPoints[0].input/.output.properties`. Only a name absent from both tenant and local sources reaches the gate. This keeps reruns idempotent without loading any Create guide.

## Unresolved Fallback

> **Build it inline first (creatable kind).** At the [Rule 17 empty-lookup gate](../../../registry-discovery.md#must-confirm-before-placeholder-fallback) the user may pick **Create** to build the missing agent as an in-solution sibling — see [§ Creating an Agent inline](#creating-an-agent-inline). This fallback applies only when the user declines/skips Create, the build fails, or the CLI lacks `registry --local`.

Mark `<UNRESOLVED: agent "<name>" in folder "<folder>" not found in registry>`. Omit `inputs:` and `outputs:`; capture intended wiring in a fenced ```` ```text ```` code block (not `#` prefixed — it renders as markdown H1). Execution creates a placeholder task — see [placeholder-tasks.md](../../../placeholder-tasks.md).

## Creating an Agent inline

After the shared Create flow's Select step checks this agent, read [Inline Agent Creation](inline-creation-guide.md) before kind choice, pinned-I/O work, or spawning its builder. Tenant-resolved, existing-local, unchecked, and fallback paths do not load that guide.

## tasks.md Entry Format

```markdown
## T<n>: Add agent task "<display-name>" to "<stage>"
- name: "<resource-name>"
- taskTypeId: <entityKey>
- folder-path: "<folder>"
- inputs:
  - <input_name> <- "<Stage>"."<Task>".<output>
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
