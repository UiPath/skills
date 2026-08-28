# Coded Agents — Flow Integration

Coded agents in flows use `uipath.core.agent.{key}` with `Orchestrator.StartAgentJob`. Choose the integration pattern based on where the agent lives.

## Pattern 1: In-Solution Coded Agent

For a coded-agent sibling folder in the same solution, reference it with `section: "In this solution"`; Studio Web resolves the node through the projects API.

- Scaffolding: [embedding-in-flows.md](embedding-in-flows.md)
- Inputs: [embedding-in-flows.md § Wiring the Agent's Inputs](embedding-in-flows.md#wiring-the-agents-inputs)
- Node JSON, top-level `bindings[]`, and `definitions[]`: uipath-maestro-flow skill, agent-plugin reference (In-solution variant)

Use the local `resource.key` created by `uip solution projects add`. It is stored in `resources/solution_folder/process/agent/<name>.json` and shown by `uip maestro flow registry list --local`.

## Pattern 2: Published Coded Agent

For a standalone Orchestrator tenant resource with independent versioning and reuse, run:

```bash
uip codedagent deploy --my-workspace
uip maestro flow registry pull --force
```

Capture the package key from the deploy command's own JSON output. Use its Orchestrator-assigned GUID as `resourceKey` in `uipath.core.agent.<resourceKey>` and `model.bindings.resourceKey`. Always run `uip maestro flow registry pull --force` after deployment.

Do not use `uip maestro flow registry search "uipath.core.agent"`: it lists only built-in node types (`uipath.agent.autonomous`, etc.), so deployed coded agents are expected to be absent.

If deploy output is unavailable or unparseable, discover the package in this order and stop at the first successful result:

1. Run `uip or packages list --search "<agent-name>" --output json`. If it returns 404 because the caller lacks `Orchestrator.Packages.View`, use step 2.
2. Run `uip or processes list --folder-path "<FolderName>" --output json` when the agent was deployed via `--folder` rather than `--my-workspace`.

If both paths are empty or return 404, re-run the deploy and capture its stdout JSON; it is authoritative.

For node JSON, use the uipath-maestro-flow skill agent-plugin reference (Published variant) and set `model.section` to `"Published"`.

## Pattern 3: Tool Resource for Another Agent

Deploy the coded agent to Orchestrator, then expose it as a tool for an inline or published parent agent. Create `<AgentProject>/resources/<ResourceName>/resource.json`:

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

## Pattern Comparison

| Aspect | In-Solution (1) | Published (2) | Tool (3) |
| --- | --- | --- | --- |
| Node type | `uipath.core.agent.<resourceKey>` (local, from `project add`) | `uipath.core.agent.<resourceKey>` (Orchestrator-assigned) | `uipath.agent.resource.tool.agent` |
| Lifecycle | `uip solution upload` (single pass) | `uip codedagent deploy` | `uip codedagent deploy` |
| Runtime lookup | Studio Web projects API | Orchestrator Releases API | Orchestrator (via parent agent) |
| `model.section` | `"In this solution"` | `"Published"` or absent | n/a |
| Cross-flow reuse | No | Yes | Yes |

## Debug

| Error | Cause | Fix |
| --- | --- | --- |
| Node doesn't resolve in SW (Pattern 1) | `resourceKey` was hand-invented rather than read from the resource file | Run `uip maestro flow registry list --local` and use the returned `resourceKey`; it matches `resource.key` in `resources/solution_folder/process/agent/<name>.json` |
| Agent not found in registry (Pattern 2/3) | Not deployed or registry stale | Run `uip codedagent deploy`, then run `uip maestro flow registry pull --force` |
| Tool resource never called | Tool description too vague | Sharpen the `description` in `resource.json` |