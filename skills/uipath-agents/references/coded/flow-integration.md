# Coded Agents — Flow Integration

Coded agents in flows use the `uipath.core.agent.{key}` node with `Orchestrator.StartAgentJob`. Three patterns exist, distinguished by where the agent lives.

---

## Pattern 1: In-Solution Coded Agent

The coded agent lives as a sibling folder inside the same solution as the flow. The flow references it with `section: "In this solution"`; the runtime resolves the node via the Studio Web projects API.

- **Agent-side scaffolding:** [embedding-in-flows.md](embedding-in-flows.md)
- **Flow node JSON shape + top-level `bindings[]` + `definitions[]` entry:** [agent/impl.md § In-solution variant](../../../uipath-maestro-flow/references/plugins/agent/impl.md#node-instance-inside-nodes--in-solution-variant)

The node-type's `{key}` is the local `resource.key` minted by `uip solution project add` (written to `resources/solution_folder/process/agent/<name>.json`) and surfaced by `uip maestro flow registry list --local`.

---

## Pattern 2: Published Coded Agent

The coded agent is deployed to Orchestrator as a standalone tenant resource. Any solution can reference it.

**When to use:** reused across flows, independent versioning, already deployed.

```bash
uip codedagent deploy --my-workspace
uip maestro flow registry pull --force
uip maestro flow registry search "uipath.core.agent" --output json
```

For the flow node JSON shape, see [agent/impl.md § Published variant](../../../uipath-maestro-flow/references/plugins/agent/impl.md#node-instance-inside-nodes--published-variant). In this variant `resourceKey` is Orchestrator-assigned and `model.section` is `"Published"`.

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
