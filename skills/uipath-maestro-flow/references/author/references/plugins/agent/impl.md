# Agent Node — Implementation

Agent nodes invoke UiPath AI agents via node type `uipath.core.agent.{key}`. Coded (Python) agents always use this plugin; low-code (`agent.json`) agents use it only when they are a standalone project (in-solution sibling or published). Inline low-code agents (embedded as a UUID subdirectory inside the flow project) use `uipath.agent.autonomous` — see the [inline-agent plugin](../inline-agent/impl.md).

The agent lives in one of two places:

- **In this solution** — sibling project inside the current solution. `{key}` is the local `resource.key` minted by `uip solution project add` (written to `resources/solution_folder/process/agent/<CodedAgentProject>.json`). The runtime resolves the node via the Studio Web projects API after `uip solution upload`. The manifest in `definitions[]` carries `model.section: "In this solution"`.
- **Published** — deployed to Orchestrator as a tenant resource. `{key}` is the Orchestrator-assigned resource key. Discoverable via `uip maestro flow registry search`. The manifest in `definitions[]` carries `model.section: "Published"`.

The node-instance shape (in `nodes[]`) is identical across the two variants — only the manifest in `definitions[]` differs (`{key}` and `model.section`).

## Discovery

**Published (tenant registry):**

```bash
uip maestro flow registry pull --force
uip maestro flow registry search "uipath.core.agent" --output json
```

Requires `uip login`. Only published agents from your tenant appear.

**In-solution (local, no login required):**

```bash
uip maestro flow registry list --local --output json
uip maestro flow registry get "<nodeType>" --local --output json
```

Run from inside the flow project directory. Discovers sibling agent projects in the same `.uipx` solution.

## Registry Validation

```bash
uip maestro flow registry get "uipath.core.agent.{key}" --output json
uip maestro flow registry get "uipath.core.agent.{key}" --local --output json
```

Requires `uip login`. Only published agents from the tenant appear in the registry.

Confirm from `registry get`:

- Input port: `input`
- Output port: `output`
- `outputDefinition.output.schema` — contains `content` (string)
- `outputDefinition.error.schema` — contains `code`, `message`, `detail`, `category`, `status`
- `model.serviceType` — `Orchestrator.StartAgentJob`
- `model.bindings.resourceSubType` — `Agent`
- `model.bindings.resourceKey` — the `<FolderPath>.<AgentName>` string used to scope binding resolution
- `inputDefinition` — typically empty (agents accept free-form input via the flow's wiring)

## Adding / Editing

For step-by-step add, delete, and wiring procedures, see [editing-operations.md](../../editing-operations.md). Use the JSON structure below for the node-specific `inputs`.

## JSON Structure

### Node instance (inside `nodes[]`) — published variant

The instance carries only per-instance data (`inputs`, `outputs`, `display`). BPMN type, serviceType, version, and binding/context templates come from the definition in `definitions[]`.

```json
{
  "id": "classifyIntent",
  "type": "uipath.core.agent.ffa33d88-8a85-4570-933c-9a69aa2dfbb5",
  "typeVersion": "<DEFINITION_VERSION>",
  "display": { "label": "Classify Intent" },
  "inputs": {},
  "outputs": {
    "output": {
      "type": "object",
      "description": "The return value of the agent",
      "source": "=result.response",
      "var": "output"
    },
    "error": {
      "type": "object",
      "description": "Error information if the agent fails",
      "source": "=result.Error",
      "var": "error"
    }
  }
}
```

The `model` block (BPMN type, `serviceType`, `bindings`, `context` template) lives on the manifest entry in `definitions[]`, not on the instance. The manifest is auto-populated by `uip maestro flow registry pull` — never hand-author it.

Three values to discover — never invent:
- **`type` suffix** — Orchestrator-assigned UUID for this agent. Per-ring and per-agent — never copy across environments. Read from `uip maestro flow registry search "uipath.core.agent"` / `registry get` as `nodeType`.
- **`typeVersion`** — the manifest's `version` field. Read from `uip maestro flow registry get <nodeType> --output json` (`.version`).
- **`resourceKey`** — composite `<FolderPath>.<AgentName>` (e.g. `Shared.Apple Genius Agent`). Appears on each top-level `bindings[]` entry tied to this agent. Read from `registry get` (`model.bindings.resourceKey` on the manifest).

Confirm all three from `registry get` before wiring.

### Node instance (inside `nodes[]`) — in-solution variant

```json
{
  "id": "codedAgent",
  "type": "uipath.core.agent.<resourceKey>",
  "typeVersion": "<DEFINITION_VERSION>",
  "display": { "label": "<Label>", "icon": "<AGENT_ICON>" },
  "inputs": {},
  "outputs": {
    "output": { "type": "object", "description": "The return value of the agent", "source": "=result.response", "var": "output" },
    "error":  { "type": "object", "description": "Error information if the agent fails", "source": "=result.Error", "var": "error" }
  }
}
```

`<AGENT_ICON>` depends on the agent's implementation type: `"coded-agent"` for Python-coded agents, `"autonomous-agent"` for low-code (`agent.json`) agents. Detect the type by inspecting the sibling agent project directory: if `agent.json` exists at its root, use `"autonomous-agent"`; otherwise use `"coded-agent"`. Do NOT copy `.display.icon` from `uip maestro flow registry get --local` — that manifest returns `"coded-agent"` for every in-solution agent regardless of implementation type, and the value must be corrected here.

Same shape as the published variant — no `model` on the instance.

**Never hand-author the `definitions[]` entry.** Run `uip maestro flow registry get "uipath.core.agent.<resourceKey>" --local --output json`, extract the `Data.Node` object, and paste it verbatim into `definitions[]`. Constructing it by hand risks missing required validator fields (`model.section`, `runtimeConstraints`, `supportsErrorHandling`, etc.).

`<resourceKey>` is the local `resource.key` written by `uip solution project add` to `resources/solution_folder/process/agent/<CodedAgentProject>.json` — read it from that file or from `uip maestro flow registry list --local --output json`. Read `<DEFINITION_VERSION>` from `uip maestro flow registry get "uipath.core.agent.<resourceKey>" --local --output json` (`.version`).

### Top-level `bindings[]` entries (sibling of `nodes`/`edges`/`definitions`)

**Rule.** Exactly one entry per `(resourceKey, propertyAttribute)` pair. Multiple node instances referencing the same agent MUST reuse the same `bindings[].id` — never duplicate the entry.

**Validate.** After writing the flow, group `bindings[]` by `(resourceKey, propertyAttribute)`. Each group must have length 1. If any group has length > 1, deduplicate before saving.

```json
"bindings": [
  {
    "id": "bClassifyIntentName",
    "name": "name",
    "type": "string",
    "resource": "process",
    "resourceKey": "<resourceKey>",
    "default": "<agent-name>",
    "propertyAttribute": "name",
    "resourceSubType": "Agent"
  },
  {
    "id": "bClassifyIntentFolderPath",
    "name": "folderPath",
    "type": "string",
    "resource": "process",
    "resourceKey": "<resourceKey>",
    "default": "<folder-path-or-empty>",
    "propertyAttribute": "folderPath",
    "resourceSubType": "Agent"
  }
]
```

> For the resolution mechanics and why these entries are required, see [file-format.md — Bindings](../../../../shared/file-format.md#bindings--orchestrator-resource-bindings-top-level-bindings).

## Accessing Output

The agent's response is available downstream:

```javascript
// In a Script node after the agent
const response = $vars.classifyIntent.output.content;
return { classification: response };
```

- `$vars.{nodeId}.output.content` — the agent's text response
- `$vars.{nodeId}.error` — error details if the agent fails

## If the Agent Does Not Exist Yet

Create the agent first, then wire it. Three paths:

- **In-solution (sibling project, coded or low-code)** — scaffold via `uipath-agents`, register with `uip solution project add` to mint the local `resource.key`, then discover via `uip maestro flow registry list --local`. For the coded pipeline, see [coded/embedding-in-flows.md](../../../../../../uipath-agents/references/coded/embedding-in-flows.md).
- **Published coded agent** — `uip codedagent deploy`, then `uip maestro flow registry pull --force`.
- **Published low-code agent** — `uip solution deploy`, then `uip maestro flow registry pull --force`.

## Using an Agent as a Tool Resource

To use a published agent (coded or low-code) as a **tool for another agent** rather than a standalone flow node, add it as a `uipath.agent.resource.tool.agent` resource node wired to the parent agent's `tool` handle. This lives within the agent's canvas, not at the top level of the flow.

For the resource file format and wiring details, see the `uipath-agents` skill:
- Coded agents: [coded/flow-integration.md § Pattern 3](../../../../../../uipath-agents/references/coded/flow-integration.md#pattern-3-tool-resource-for-another-agent)
- Low-code agents: see the `uipath-agents` skill's low-code references.

## Debug

| Error | Cause | Fix |
| --- | --- | --- |
| Node type not found in registry | Agent not published, or registry stale | If in same solution: run `registry list --local`. Otherwise: run `uip login` then `uip maestro flow registry pull --force`. For coded agents, ensure `uip codedagent deploy` completed successfully |
| In-solution node doesn't resolve | `resourceKey` was hand-invented rather than read from the resource file, or `uip solution project add` was never run for the agent project | Run `uip maestro flow registry list --local` and use the returned `resourceKey` (same value as `resource.key` in `resources/solution_folder/process/agent/<CodedAgentProject>.json`) |
| Agent execution failed | Underlying agent errored | Check `$vars.{nodeId}.error` for details. For coded agents, test locally first with `uip codedagent run` |
| Empty `output.content` | Agent returned no response | Verify the agent is configured correctly (published: in Orchestrator; in-solution: in Studio Web) |
| `inputDefinition` is empty | Expected — agents accept input via flow wiring, not typed fields | Wire upstream data to the agent via `$vars` expressions |
