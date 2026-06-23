# Coded Agents — Flow Integration

Coded agents in flows use the `uipath.core.agent.{key}` node with `Orchestrator.StartAgentJob`. Three patterns exist, distinguished by where the agent lives.

---

## Pattern 1: In-Solution Coded Agent

The coded agent lives as a sibling folder inside the same solution as the flow. The flow references it with `section: "In this solution"`; the runtime resolves the node via the Studio Web projects API.

- **Agent-side scaffolding:** [embedding-in-flows.md](embedding-in-flows.md)
- **Wiring the agent's inputs:** [embedding-in-flows.md § Wiring the Agent's Inputs](embedding-in-flows.md#wiring-the-agents-inputs)
- **Flow node JSON shape + top-level `bindings[]` + `definitions[]` entry:** [agent/impl.md § In-solution variant](../../../uipath-maestro-flow/references/plugins/agent/impl.md#node-instance-inside-nodes--in-solution-variant)

The node-type's `{key}` is the local `resource.key` minted by `uip solution project add` (written to `resources/solution_folder/process/agent/<name>.json`) and surfaced by `uip maestro flow registry list --local`.

---

## Pattern 2: Published Coded Agent

The coded agent is deployed to Orchestrator as a standalone tenant resource. Any solution can reference it.

**When to use:** reused across flows, independent versioning, already deployed.

```bash
uip codedagent deploy --my-workspace
uip maestro flow registry pull --force
```

**Capture the package key from the deploy command's own output** — `uip codedagent deploy` prints JSON containing the package `Key` (an Orchestrator-assigned GUID). That GUID is the `resourceKey` used in the flow node's `type` (`uipath.core.agent.<resourceKey>`) and `model.bindings.resourceKey`. Always run `uip maestro flow registry pull --force` after deploy to refresh the local flow registry cache, but do NOT depend on `uip maestro flow registry search "uipath.core.agent"` to return the deployed agent — that search only enumerates built-in node types (`uipath.agent.autonomous`, etc.); user-deployed coded agents do not appear there, so an empty result is the *expected* state and is NOT a sign the deploy failed.

Fallback discovery paths if the deploy output is unavailable or unparseable, **tried in order** — stop at the first one that returns the package:

1. `uip or packages list --search "<agent-name>" --output json` (tenant feed listing). Returns 404 on tenants where the caller lacks `Orchestrator.Packages.View` scope — if so, move to (2).
2. `uip or processes list --folder-path "<FolderName>" --output json` if the agent was deployed via `--folder` rather than `--my-workspace`.

If all paths return empty / 404, the deploy command's stdout JSON is authoritative — re-run the deploy and capture its output rather than chasing post-hoc discovery endpoints.

For the flow node JSON shape, see [agent/impl.md § Published variant](../../../uipath-maestro-flow/references/plugins/agent/impl.md#node-instance-inside-nodes--published-variant). `model.section` is `"Published"`.

---

## Pattern 3: Tool Resource for Another Agent

The coded agent is a tool that another agent (inline or published) can call. Requires deploying the coded agent to Orchestrator first.

**Resource file** at `<AgentProject>/resources/<ResourceName>/resource.json`:

```json
{
  "$resourceType": "tool",
  "type": "agent",
  "name": "MyCodedAgent",
  "description": "What this agent does (shown to the parent LLM for tool selection)",
  "location": "external",
  "properties": {
    "processName": "<CODED_AGENT_PROCESS_NAME>",
    "folderPath": "<FOLDER_PATH>"
  },
  "inputSchema":  { "type": "object", "properties": { "userInput": { "type": "string" } } },
  "outputSchema": { "type": "object", "properties": { "content":   { "type": "string" } } },
  "id": "<UUID>",
  "referenceKey": ""
}
```

Coded agents use `location: "external"`.

---

## Pattern Comparison

| Aspect | In-Solution (1) | Published (2) | Tool (3) |
|---|---|---|---|
| Node type | `uipath.core.agent.<resourceKey>` (local, from `project add`) | `uipath.core.agent.<resourceKey>` (Orchestrator-assigned) | `uipath.agent.resource.tool.agent` |
| Lifecycle | `uip solution upload` (single pass) | `uip codedagent deploy` | `uip codedagent deploy` |
| Runtime lookup | Studio Web projects API | Orchestrator Releases API | Orchestrator (via parent agent) |
| `model.section` | `"In this solution"` | `"Published"` or absent | n/a |
| Cross-flow reuse | No | Yes | Yes |

---

## Debug

| Error | Cause | Fix |
| --- | --- | --- |
| Node doesn't resolve in SW (Pattern 1) | `resourceKey` was hand-invented rather than read from the resource file | Run `uip maestro flow registry list --local` and use the returned `resourceKey` (it matches `resource.key` in `resources/solution_folder/process/agent/<name>.json`) |
| Agent not found in registry (Pattern 2/3) | Not deployed or registry stale | `uip codedagent deploy`, then `uip maestro flow registry pull --force` |
| Tool resource never called | Tool description too vague | Sharpen the `description` in `resource.json` |
