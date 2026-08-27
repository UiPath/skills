# Agent Node — Implementation

Agent nodes invoke UiPath AI agents through `uipath.core.agent.{key}`. Coded (Python) agents always use this plugin. Standalone low-code (`agent.json`) agents use it when in-solution siblings or published; inline low-code agents embedded as a UUID subdirectory use `uipath.agent.autonomous`—see the [inline-agent plugin](../inline-agent/impl.md).

Agents are either:

- **In this solution**: a sibling project. `{key}` is the local `resource.key` minted by `uip solution projects add` and written to `resources/solution_folder/process/agent/<CodedAgentProject>.json`. Runtime resolution uses the Studio Web projects API after `uip solution upload`; `definitions[]` uses `model.section: "In this solution"`.
- **Published**: an Orchestrator tenant resource. `{key}` is the Orchestrator-assigned resource key, discoverable with `uip maestro flow registry search`; `definitions[]` uses `model.section: "Published"`.

The `nodes[]` shape is the same; only the `definitions[]` manifest differs.

## Discovery and Registry Validation

Run these commands for published agents (requires `uip login`):

```bash
uip maestro flow registry pull --force
uip maestro flow registry search "uipath.core.agent" --output json
```

Only published agents from the logged-in tenant appear. Run these commands inside the flow project directory for in-solution agents; no login is required:

```bash
uip maestro flow registry list --local --output json
uip maestro flow registry get "<node-type>" --local --output json
```

These discover sibling agent projects in the same `.uipx` solution.

Run:

```bash
uip maestro flow registry get "uipath.core.agent.{key}" --output json
uip maestro flow registry get "uipath.core.agent.{key}" --local --output json
```

The non-local command requires `uip login` and shows only published tenant agents. Confirm from `registry get`:

- Ports are input `input` and output `output`.
- `outputDefinition.output.schema` contains `content` (string).
- `outputDefinition.error.schema` contains `code`, `message`, `detail`, `category`, `status`.
- `model.serviceType` is `Orchestrator.StartAgentJob`.
- `model.bindings.resourceSubType` is `Agent`.
- `model.bindings.resourceKey` is the `<FolderPath>.<AgentName>` string used to scope binding resolution.
- `inputDefinition` is the typed input schema, with one property per `entry-points.json` input field. Each property requires an `inputs.<field>` entry on the node instance; it is empty only for agents with no typed inputs (free-form). See [Wiring Inputs](#wiring-inputs).

For add, delete, and wiring procedures, see [editing-operations.md](../../editing-operations.md). Use the JSON below for node-specific `inputs`.

## Node Instances

Per-instance data is `inputs`, `outputs`, and `display`; BPMN type, service type, version, and binding/context templates come from `definitions[]`.

### Published

```json
{
  "id": "<NODE_ID>",
  "type": "uipath.core.agent.<AGENT_UUID>",
  "typeVersion": "<DEFINITION_VERSION>",
  "display": { "label": "<LABEL>" },
  "inputs": {
    "<INPUT_FIELD>": {
      "type": "jsExpression",
      "expression": "$vars.<UPSTREAM_NODE_ID>.output.<FIELD>",
      "fieldType": "<FIELD_TYPE>"
    }
  },
  "outputs": {
    "error": {
      "type": "object",
      "description": "Error information if the agent fails",
      "source": "=Error",
      "var": "error"
    }
  }
}
```

Never invent these values; confirm all three with `registry get` before wiring:

- `type` suffix: the Orchestrator-assigned UUID, per ring and agent; read `nodeType` from `uip maestro flow registry search "uipath.core.agent"` or `registry get`.
- `typeVersion`: the manifest `version`, read from `uip maestro flow registry get <node-type> --output json` (`.version`).
- `resourceKey`: composite `<FolderPath>.<AgentName>`, read from `model.bindings.resourceKey`.

The `model` block belongs on the `definitions[]` manifest, not the instance. The manifest is auto-populated by `uip maestro flow registry pull`; never hand-author it.

### In-solution

```json
{
  "id": "<NODE_ID>",
  "type": "uipath.core.agent.<resourceKey>",
  "typeVersion": "<DEFINITION_VERSION>",
  "display": { "label": "<LABEL>", "icon": "<AGENT_ICON>" },
  "inputs": {},
  "outputs": {
    "error": { "type": "object", "description": "Error information if the agent fails", "source": "=Error", "var": "error" }
  }
}
```

Declare `error` only; `output` is derived. Hand-authoring it makes the converter copy `source` verbatim, so `"=result.response"` resolves to null at runtime even when `flow validate` passes. `output` is allowed only with exactly `source: "=this"` and the agent’s output schema. See [file-format.md § Node outputs](../../../../shared/file-format.md#node-outputs).

Set `display.icon` by inspecting the sibling project root: use `"autonomous-agent"` when `agent.json` exists, otherwise `"coded-agent"`. Do not copy `.display.icon` from `uip maestro flow registry get --local`; that manifest reports `"coded-agent"` for every in-solution agent.

Never hand-author `definitions[]`. Run:

```bash
uip maestro flow registry get "uipath.core.agent.<resourceKey>" --local --output json
```

Extract the `Data.Node` object verbatim into `definitions[]`; hand construction can omit `model.section`, `runtimeConstraints`, and `supportsErrorHandling`. Read `<resourceKey>` from `resources/solution_folder/process/agent/<CodedAgentProject>.json` or from `uip maestro flow registry list --local --output json`. Read `<DEFINITION_VERSION>` from `.version` in local `registry get` output.

## Top-level `bindings[]`

`bindings[]` is a sibling of `nodes`, `edges`, and `definitions`. Create exactly one entry per `(resourceKey, propertyAttribute)` pair. Multiple instances referencing one agent must reuse the same `bindings[].id`; never duplicate entries.

After writing the flow, group `bindings[]` by `(resourceKey, propertyAttribute)` and require each group to have length 1. Deduplicate any group longer than 1 before saving.

```json
"bindings": [
  {
    "id": "<BINDING_ID_NAME>",
    "name": "name",
    "type": "string",
    "resource": "process",
    "resourceKey": "<resourceKey>",
    "default": "<agent-name>",
    "propertyAttribute": "name",
    "resourceSubType": "Agent"
  },
  {
    "id": "<BINDING_ID_FOLDER>",
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

See [file-format.md — Bindings](../../../../shared/file-format.md#bindings--orchestrator-resource-bindings-top-level-bindings) for resolution mechanics and why these entries are required.

## Wiring Inputs

Create one `inputs.<field>` entry for every property in `inputDefinition.properties`. Use either shape below with the same binding:

```json
"<INPUT_FIELD>": {
  "type": "jsExpression",
  "expression": "$vars.<UPSTREAM_NODE_ID>.output.<FIELD>",
  "fieldType": "<FIELD_TYPE>"
}
```

or:

```json
"<INPUT_FIELD>": {
  "type": "literal",
  "expression": "{{ $vars.<UPSTREAM_NODE_ID>.output.<FIELD> }}",
  "fieldType": "<FIELD_TYPE>"
}
```

`literal` may mix static text and `{{ }}` interpolation. Never use a plain `"=js:..."` string; it is sent verbatim to the activity and fails with `Cannot find name '<identifier>'`. Set `<FIELD_TYPE>` to the property’s JSON-schema type (`string`, `boolean`, `number`, etc.) from `inputDefinition.properties`; do not invent it.

For a trigger-to-agent flow, surface a flow input as a trigger-bound global:

```json
"variables": {
  "globals": [
    { "id": "<INPUT_FIELD>", "direction": "in", "type": "string", "defaultValue": "", "triggerNodeId": "<TRIGGER_ID>" }
  ]
}
```

Connect trigger → agent → end:

```json
"edges": [
  { "id": "<EDGE_1>", "sourceNodeId": "<TRIGGER_ID>", "sourcePort": "output", "targetNodeId": "<AGENT_ID>", "targetPort": "input" },
  { "id": "<EDGE_2>", "sourceNodeId": "<AGENT_ID>", "sourcePort": "output", "targetNodeId": "<END_ID>", "targetPort": "input" }
]
```

Reference upstream values as `$vars.<nodeId>.output.<field>` and flow globals as `$vars.<global>`. Agent inputs therefore reference `$vars.<TRIGGER_ID>.output.<INPUT_FIELD>`.

## Accessing Output

```javascript
const response = $vars.<AGENT_NODE_ID>.output.content;
return { result: response };
```

- `$vars.{nodeId}.output.content`: agent text response.
- `$vars.{nodeId}.error`: failure details.

## If the Agent Does Not Exist Yet

Create it before wiring:

- **In-solution sibling, coded or low-code**: scaffold with `uipath-agents`, register with `uip solution projects add` to mint `resource.key`, then discover with `uip maestro flow registry list --local`. For coded agents, see [coded/embedding-in-flows.md](../../../../../../uipath-agents/references/coded/embedding-in-flows.md).
- **Published coded**: run `uip codedagent deploy`, then `uip maestro flow registry pull --force`.
- **Published low-code**: run `uip solution deploy`, then `uip maestro flow registry pull --force`.

## Using an Agent as a Tool Resource

To use a published coded or low-code agent as another agent’s tool, add a `uipath.agent.resource.tool.agent` resource node inside the parent agent’s canvas and wire it to the parent agent’s `tool` handle. Do not add it at the top level of the flow.

For format and wiring details, see the `uipath-agents` skill:

- Coded agents: [coded/flow-integration.md § Pattern 3](../../../../../../uipath-agents/references/coded/flow-integration.md#pattern-3-tool-resource-for-another-agent)
- Low-code agents: the `uipath-agents` skill’s low-code references.

## Debug

| Error | Cause | Fix |
| --- | --- | --- |
| Node type not found in registry | Agent is unpublished or registry is stale | For an in-solution agent, run `registry list --local`. Otherwise run `uip login` then `uip maestro flow registry pull --force`. For coded agents, ensure `uip codedagent deploy` completed successfully. |
| In-solution node does not resolve | `resourceKey` was invented, or `uip solution projects add` was not run | Run `uip maestro flow registry list --local` and use its `resourceKey`, which must equal `resource.key` in `resources/solution_folder/process/agent/<CodedAgentProject>.json`. |
| Agent execution failed | Underlying agent error | Inspect `$vars.{nodeId}.error`; for coded agents, test locally with `uip codedagent run`. |
| Empty `output.content` | Agent returned no response | Verify configuration in Orchestrator for published agents or Studio Web for in-solution agents. |
| `inputDefinition` is empty | Agent declares no typed input schema (free-form) | Wire upstream data through `jsExpression` inputs; see [Wiring Inputs](#wiring-inputs). |