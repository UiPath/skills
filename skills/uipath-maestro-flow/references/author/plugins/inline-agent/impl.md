# Inline Agent Node — Implementation

This skill covers flow-specific operations for low-code inline agent nodes: scaffolding, JSON structure, wiring, resources, and validation. For `agent.json`, `resource.json`, solution resources, prompts, and agent-side configuration, use the `uipath-agents` skill, especially `lowcode/capabilities/inline-in-flow/inline-in-flow.md`.

Node type: `uipath.agent.autonomous`. Bind the agent directory with `inputs.source = <projectId>`. BPMN type, `serviceType` (`Orchestrator.StartInlineAgentJob`), version, and context come from its `definitions[]` entry. Coded Python agents use the [`agent`](../agent/impl.md) plugin (`uipath.core.agent.{key}`); inline agents are low-code only.

<a id="configure-agentjson"></a>
## 1. Scaffold and configure the inline agent

Run:

```bash
uip agent init "<FlowProjectDir>" --inline-in-flow --output json
```

The command creates `<FlowProjectDir>/<projectId-uuid>/` with `agent.json`, `flow-layout.json` (`{}`), empty `evals/eval-sets/`, `features/`, and `resources/`. Record the returned `ProjectId`; it must equal the subdirectory name, `agent.json.projectId`, and the flow node's `inputs.source`. Do not create `entry-points.json` or `project.uiproj` in this directory.

Configure `<FlowProjectDir>/<projectId>/agent.json`:

1. Replace scaffolded `settings.model: "gpt-4o-2024-11-20"`; never ship that placeholder. Run `uip agent model list`, select the newest GA model appropriate to the task, and set `settings.maxTokens` at or below its cap. Follow [`model-selection-guide.md`](../../../../../uipath-agents/references/lowcode/model-selection-guide.md).
2. Set `settings.temperature` (`0` for extraction, classification, and judgment) and `settings.maxIterations`: keep `25` when any tool or context handle is present; use `≤5` only for a tool-less single-shot agent.
3. Put real system and user prompts in `messages[0].content` and `messages[1].content`, with bounded role, grounding, output contract, and per-tool call/stop criteria. Follow [`autonomous-agent-prompting-guide.md`](../../../../../uipath-agents/references/lowcode/prompting/autonomous-agent-prompting-guide.md#1-system-prompt-skeleton).
4. For every tool or context handle, include both sentences below, replacing placeholders. Use `N ≤ 3` for a single decision:

   ```text
   Call <toolName> at most <N> times (N ≤ 3 for a single decision). After the last call, stop retrieving and decide with the evidence you already have.
   If the retrieved content does not cover a detail, say so in <rationaleField>, lower <confidenceField>, and still return every outputSchema field. Never end a run without a determination.
   ```

5. Declare a typed `outputSchema`; do not rely on a bare `content` string. Set guardrails and other production fields required by the `uipath-agents` guides.

After editing `messages[].content`, run `uip agent refresh` to regenerate `contentTokens`; do not hand-author them. `content` is authoritative. Tokens use `type: "simpleText"` or `type: "variable"`; variable `rawString` is brace-free. `uip agent validate` is read-only and does not repair mismatches.

<a id="wiring-flow-variables-into-agent-prompts"></a>
## 2. Wire flow inputs into prompts

Author and align all three pieces; the CLI does not derive them. `uip agent refresh` does not scan prompts, derive `inputSchema`, or populate `agentInputVariables`; it only regenerates `messages[].contentTokens`. The converter builds runtime `JobArguments` only from the flow node's `inputs.agentInputVariables[]`, not from `$vars` tokens in `agent.json`.

Use `$vars.<trigger>.output.<var>` → `<trigger>__output__<var>`:

| Location | Required content |
|---|---|
| Flow node `inputs.agentInputVariables[]` | One entry per input: `{ "id": "<trigger>__output__<var>", "type": "string", "binding": "=$vars.<trigger>.output.<var>", "description": "Bound from $vars.<trigger>.output.<var>" }` |
| `agent.json` `inputSchema.properties` | One property named `<trigger>__output__<var>` with matching type and description |
| `messages[].content` | `{{input.<trigger>__output__<var>}}`; never `$vars` or `{{plainName}}` |
| `messages[].contentTokens[]` | One `{ "type": "variable", "rawString": "input.<trigger>__output__<var>" }` per interpolation; literals are `simpleText` |

The bound source must be a real `.flow` node ID with an edge path reaching the agent. See [../../../shared/node-output-wiring.md](../../../shared/node-output-wiring.md).

For a trigger, declare the variable in `variables.globals[]`, for example:

```json
{ "id": "invoiceNumber", "direction": "in", "type": "string", "triggerNodeId": "start" }
```

Read it as `$vars.<triggerId>.output.<id>`. `flow validate` does not verify that the referenced variable exists; an undeclared binding passes validation and faults at debug with empty `JobArguments`. Declare agent-fed flow outputs as `direction: "out"` globals and map them on every reachable End node. See [../../../shared/variables-and-expressions.md](../../../shared/variables-and-expressions.md) (§ Input associated with a trigger) and [../../editing-operations-json.md § Add a workflow variable](../../editing-operations-json.md#add-a-workflow-variable).

Do not write `inputs.systemPrompt` or `inputs.userPrompt` on the flow node. A present prompt string makes `@uipath/flow-converter` prune every `agentInputVariables[]` entry not referenced by that text (`@uipath/flow-converter`; prune present 0.25.1 through 0.42.0). Empty strings fail validation. Canonical prompts belong in `agent.json`.

A Studio Web-pulled flow may mirror prompts into node `inputs`; delete those keys or run `uip agent refresh --inline-in-flow`, which shell-ifies the node and preserves structural inputs. If connector output fields are unknown until execution, author best-guess flattened paths with matching `binding` and `inputSchema`, ask the user to confirm before upload, and correct prompt tokens and mirrors after the first run.

### Input rules

- Use `binding`, never `value`; the converter ignores Studio Web's `value: "=js:$vars…"` form. Use `binding: "=$vars.<trigger>.output.<var>"`.
- Match `agentInputVariables[].type` and `inputSchema` to the actual output shape. Data Service query-entity-records returns an array; `.map()` returns an array; bind a leaf such as `=$vars.crmLookup1.output[0].accountTier` when necessary. Registry metadata may say only `output.type: "object"`; use `flow debug` to determine runtime shape. A mismatch faults `AGENT_STARTUP.INPUT_VALIDATION_ERROR` (incident `170002`, `"Input should be a valid dictionary … input_type=list"`) even when both validators report `Valid`.
- Mark a schema key `required` only when its binding can never be empty.
- `flow validate` catches malformed or unknown `{{input.K}}` Resolution↔Contract mismatches, but not missing or wrong Delivery bindings.

### Token invariant

Run refresh after changing `content`. For `"Invoice Number: {{input.start__output__invoiceNumber}}\n"`, it must produce:

```json
[
  { "type": "simpleText", "rawString": "Invoice Number: " },
  { "type": "variable", "rawString": "input.start__output__invoiceNumber" },
  { "type": "simpleText", "rawString": "\n" }
]
```

If `uip agent validate` reports `Expected type "simpleText"…`, `Expected "input.X" but got "{{input.X}}"`, or `contentTokens has N entries but content requires M`, fix `content` if needed and run refresh; do not edit `rawString`.

<a id="registry-validation"></a>
## 3. Validate the registry and add the node

Run:

```bash
uip maestro flow registry get uipath.agent.autonomous --output json
```

Confirm input port `input`; output ports `success`, `error`; artifact ports `tool`, `context`, `escalation`; `model.source: true`; `model.serviceType: Orchestrator.StartInlineAgentJob`; and `model.version: v2`.

Use `Edit` / `Write` for graph edits. Do not use Flow CLI `node add`, `edge add`, or `variable` commands. Add a minimal node to `nodes[]`; do not add an instance `model` block:

```json
{
  "id": "autonomousAgent1",
  "type": "uipath.agent.autonomous",
  "typeVersion": "<definition.version>",
  "display": { "label": "Autonomous Agent" },
  "inputs": {
    "source": "<projectId-uuid>",
    "agentInputVariables": [],
    "agentOutputVariables": [{ "id": "content", "type": "string" }]
  },
  "outputs": {
    "error": {
      "type": "object",
      "description": "Error information if the node fails",
      "source": "=Error",
      "var": "error"
    }
  }
}
```

Copy the definition verbatim from `Data.Node` or the top-level node object, depending on CLI/plugin version. Set `typeVersion` to its exact `version`; add `variables.nodes[]` entries for `autonomousAgent1.output` and `autonomousAgent1.error` with `binding.nodeId` and matching `binding.outputId`; add `layout.nodes.<agentNodeId>`; then run `flow format` for final positioning.

<a id="adding-resource-nodes"></a>
## 4. Wire edges and resources

Add normal edges with `Edit` / `Write`:

```json
{ "id": "<EDGE_ID>", "sourceNodeId": "<upstreamNodeId>", "sourcePort": "output", "targetNodeId": "autonomousAgent1", "targetPort": "input" }
{ "id": "<EDGE_ID>", "sourceNodeId": "autonomousAgent1", "sourcePort": "success", "targetNodeId": "<nextNodeId>", "targetPort": "input" }
```

Resource edges use the agent artifact port and resource node `input`; `tool` and `context` are bottom ports and `escalation` is the top port:

```json
{ "id": "<EDGE_ID>", "sourceNodeId": "autonomousAgent1", "sourcePort": "tool", "targetNodeId": "<toolNodeId>", "targetPort": "input" }
```

### Resource matrix

| Kind | Edge source port | Node type | `resource.json` discriminator | Run `uip solution resources refresh`? | Reference |
|---|---|---|---|---|---|
| RPA process tool | `tool` | `uipath.agent.resource.tool.process.<release-key>` | `type: "process"` | Yes | `lowcode/capabilities/process/process.md` |
| Agent tool | `tool` | `uipath.agent.resource.tool.agent.<release-key>` | `type: "agent"` | Yes | `lowcode/capabilities/process/process.md` |
| API workflow tool | `tool` | `uipath.agent.resource.tool.api.<release-key>` | `type: "api"` | Yes | `lowcode/capabilities/process/process.md` |
| Process Orchestration tool | `tool` | `uipath.agent.resource.tool.processorchestration.<release-key>` | `type: "processOrchestration"` | Yes | `lowcode/capabilities/process/process.md` |
| Built-in tool | `tool` | `uipath.agent.resource.tool.builtin.<toolType>` | `type: "internal"` | No | `lowcode/capabilities/built-in-tools/built-in-tools.md` |
| Context (index / RAG) | `context` | `uipath.agent.resource.context.index.<index-name>.<index-id>` | `$resourceType: "context"`, `contextType: "index"` | Yes | `lowcode/capabilities/context/index.md` |
| Escalation (HITL) | `escalation` | `uipath.agent.resource.escalation` | `$resourceType: "escalation"` | Yes | `lowcode/capabilities/escalation/escalation.md` |

For every kind: discover the type, generate a UUID, add a minimal node, copy its definition into `definitions[]`, add layout, wire exactly one artifact edge, author `resource.json`, then refresh and validate.

Run discovery commands:

```bash
uip maestro flow registry search "<prefix>" --output json
uip maestro flow registry get "<NodeType>" --output json
uip maestro flow registry get uipath.agent.resource.escalation --output json
uip maestro flow registry get "uipath.agent.resource.tool.builtin.<toolType>" --output json
RES=$(uuidgen)
```

Use `registry search` for `uipath.agent.resource.tool.process`, `uipath.agent.resource.tool.agent`, `uipath.agent.resource.tool.api`, `uipath.agent.resource.tool.processorchestration`, and context; then get the matching `NodeType`. `<release-key>` is the release-key GUID from `uip solution resources list` (`Key`); `<toolType>` is the fixed kebab discriminator matching `resource.json` `properties.toolType`.

Add each resource node as:

```json
{
  "id": "agentTool1",
  "type": "<NodeType>",
  "typeVersion": "<DEFINITION_VERSION>",
  "display": { "label": "<Label>" },
  "inputs": { "source": "<RES_UUID>" }
}
```

Copy the registry definition verbatim and set `typeVersion` to its `version`. Add top-level `bindings[]` when `model.bindings` exists; process tools use `model.bindings.resourceKey` and `model.bindings.values[]` (`name`, `folderPath`, etc.). Built-in tools declare none. Keep `inputs.source` equal to the resource UUID, resource directory name, and `resource.json.id`.

Author `<FlowProjectDir>/<inlineAgentProjectId>/resources/<RES_UUID>/resource.json` according to the matrix reference. A missing `$resourceType` or built-in `type` causes `uip agent validate` to report `"resources": 0` and refresh to write an empty `bindings_v2.json`.

For process, agent, API, and processOrchestration tools, read `lowcode/capabilities/process/process.md` § Tool resource.json Shape first. Use the exact subtype `type`; RPA uses raw .NET arrays (Template A in `solution-files.md`), while Agent/API/Process Orchestration use JSON Schema V2 (Template B). Run `uip solution resources list` and `uip solution resources get` to populate `referenceKey`, `folderPath`, `inputSchema`, and `outputSchema`. Set `location` to `"solution"` for discovery `Source: "Local"` and `"external"` for `Source: "Remote"`; set `properties.folderPath` to the literal discovered path; include `"guardrails": { "type": "array" }` in `inputSchema.properties`.

Run refresh and validation:

```bash
uip agent refresh "<FlowProjectDir>/<projectId>" --inline-in-flow \
  --bindings-target "<FlowProjectDir>/bindings_v2.json" --output json
uip agent validate "<FlowProjectDir>/<projectId>" --inline-in-flow --output json
uip solution resources refresh --output json
```

Run `uip solution resources refresh` for every kind except built-in tools. Built-ins use `referenceKey: null` and `type: "internal"`, require no `bindings[]`, solution files, or solution refresh. For process tools, context, and escalation, pass `--bindings-target <FlowProjectDir>/bindings_v2.json`; refresh regenerates `bindings_v2.json`, so never hand-edit it. Verify refresh and validate both report `"resources": N` with `N > 0`.

<a id="refresh-and-validate"></a>
## 5. Refresh and validate the complete flow

Run:

```bash
uip agent refresh "<FlowProjectDir>/<projectId>" --inline-in-flow --output json
uip agent refresh "<FlowProjectDir>/<projectId>" --inline-in-flow \
  --bindings-target "<FlowProjectDir>/bindings_v2.json" --output json
uip agent validate "<FlowProjectDir>/<projectId>" --inline-in-flow --output json
uip maestro flow validate <FlowName>.flow --output json
```

Use the `--bindings-target` form after all tool/resource edits. Refresh writes `entry-points.json` and `bindings_v2.json`, propagates tool bindings, and shell-ifies self-contained Studio Web flows: it strips embedded agent prompts/model/guardrails and resource config, leaving structural agent inputs (`source`, `agentInputVariables`, etc.) and resource `{source, detail, itemsDescription}`. It is scoped to the refreshed agent, a no-op for CLI-authored shells, and best-effort. When it acts, output includes `FlowShellified: true` and `FlowResourceNodesStripped: <n>`. Keep canonical configuration in the sidecar; do not re-embed it in `.flow`.

Re-run this self-check after CLI upgrades: a prompt-less node must pass and empty-string prompts must fail. Older CLIs may reject absent keys with `[REQUIRED_FIELD] "systemPrompt" is required`; upgrade first. If upgrading is impossible, add minimal non-empty placeholders only after that error, run debug, and confirm `JobArguments` contains bound inputs. If it is `{"input":""}`, the converter prune remains; do not ship the workaround and escalate for upgrade.

## 6. JSON structure and output wiring

The instance has only `inputs`, `outputs`, and `display`; do not add `model`. `inputs.source` is the UUID and `inputs.agentInputVariables[]` has one `{id, type, binding}` per input. The definition supplies service type/version/context.

Typed `outputSchema.properties` surface flat at `$vars.<nodeId>.output.<field>`; there is no `.content.` wrapper. Without a typed schema, a single string is at `$vars.<nodeId>.output.content`; errors are at `$vars.<nodeId>.error`.

Align output delivery:

| Location | Required content |
|---|---|
| `agent.json` `outputSchema.properties` | One typed key per returned field |
| Flow node `inputs.agentOutputVariables[]` | One `{ "id": "<field>", "type": "<type>" }` per field, not one `content` object |
| End node `outputs.<global>` | `"source": "=js:$vars.<agentNodeId>.output.<field>"` |

Declare each flow output as a `direction: "out"` global and map it on every reachable End node. Do not use `agentOutputVariables: [{"id":"content","type":"object"}]` with `.output.content.<field>`; validation may pass, debug may complete, and output will be null.

## 7. Debug and repair

| Symptom | Cause and fix |
|---|---|
| `flow validate` reports `[SCHEMA_ERROR] System prompt is required` or `[REQUIRED_FIELD] systemPrompt` / `userPrompt` required | Empty prompt keys, missing `inputs.source`, missing subdirectory, or missing `agent.json`. Delete prompt keys, never set `""`; set `inputs.source` to the UUID and verify `<FlowDir>/<projectId>/agent.json`. Use the Older CLI procedure if absent keys are rejected. |
| Debug shows `JobArguments {"input":""}` or `AGENT_STARTUP.INPUT_VALIDATION_ERROR` (`"Field required"`, incident `170002`) | Node prompt keys caused converter pruning. Delete them or run refresh; verify no `systemPrompt` key. A placeholder that references no input cannot preserve delivery. |
| `inputs.source` matches no directory or the wrong agent runs | Use the exact UUID directory/project ID; remove stale or human-readable folder names. |
| `Orchestrator.StartAgentJob` or runtime mismatch | Remove instance `model`; use the registry definition with `model.serviceType: "Orchestrator.StartInlineAgentJob"`. |
| Studio Web says "System prompt is required" | Ensure real `agent.json.messages[]` content, refresh, validate, and re-import. Remove node prompt keys. |
| "Could not find process for tool" or empty/missing `bindings_v2.json` | Run `uip agent refresh --inline-in-flow --bindings-target <FlowProjectDir>/bindings_v2.json`, validate, then `uip solution resources refresh`. Do not hand-edit `bindings_v2.json`. |
| Tool cannot resolve | Add definition-declared top-level `bindings[]`; match node `inputs.source` and `resource.json.id`; run refresh with `--bindings-target`, validate, and solution refresh. |
| `inputs.agentProjectId` unrecognized | Use `inputs.source`; `agentProjectId` is invalid. |
| `uip agent validate` rejects the project | Delete `entry-points.json` and `project.uiproj` from the inline directory. |
| Agent returns empty `output.content` | Fix `messages[].contentTokens` by running refresh; use `simpleText` and `variable`. |
| Token errors (`Expected type "simpleText" but got "text"`; braces in `rawString`; wrong count) | Fix `content` and run refresh; never hand-edit tokens. |
| Literal `{{input.X}}` at runtime | Add `X` to `inputSchema.properties`; run flow validation. |
| Debug `AGENT_RUNTIME.TERMINATION_LLM_RAISED_ERROR` with literal `input.<key>` | Replace `value: "=js:$vars…"` with `binding: "=$vars.<trigger>.output.<var>"`; declare the trigger global. If binding is correct, remove node prompt keys. |
| Debug `AGENT_RUNTIME.TERMINATION_LLM_RAISED_ERROR` "Template placeholders detected instead of actual values" | The converter ignored `value`; use `binding` and strip `=js:`. Then check prompt-key pruning. |
| Typed flow output is null although validation passes | List every field in `agentOutputVariables[]` and map End nodes to flat `=js:$vars.<node>.output.<field>` paths, without `.content.`. |

### Repair a stale definition

Run:

```bash
uip maestro flow registry get uipath.agent.autonomous --output json > /tmp/registry_response.json
```

Replace the matching `definitions[]` entry (`nodeType`) with `Data.Node` or the top-level response object, and set the instance `typeVersion` to its exact `version`. For every `uipath.agent.autonomous` or `uipath.agent.resource.` node, move any `model.source` to `inputs.source` and remove the instance `model` block. Then run:

```bash
uip maestro flow validate <FILE>.flow --output json
```

The same replacement pattern applies to any node type by substituting its `nodeType` in the command and loop guard. Use direct JSON edits through `Edit` / `Write`; if a bulk rewrite is explicitly approved, use the `python3` heredoc pattern in [editing-operations-json.md — Edit Tooling](../../editing-operations-json.md#edit-tooling).

### Resolve `[REQUIRED_FIELD] systemPrompt is required`

Check in order: (1) `inputs.source` contains the project UUID on the agent and every resource node, with no instance `model`; (2) `<FlowDir>/<projectId>/agent.json` exists; (3) `messages[0].content` and `messages[1].content` are real and their tokens are refreshed; (4) delete node prompt keys. If a stale flow has UUIDs in `model.source`, move them to `inputs.source`. Then run agent refresh, agent validate, and flow validate. Do not use empty prompts.

## 8. What not to do

- Do not use Flow CLI `node add`, `edge add`, or `variable` for inline-agent graph edits; use `Edit` / `Write`.
- Do not write `inputs.systemPrompt` / `inputs.userPrompt`; prompts live in `agent.json`.
- Do not put a `model` block on the inline-agent or resource-node instance.
- Do not use `model.agentProjectId`, `inputs.agentProjectId`, or `model.source`; all related nodes use `inputs.source`.
- Do not create `entry-points.json` or `project.uiproj` in an inline agent directory.
- Do not rename the UUID directory to a human-readable name.
- Do not use `uip agent tool add`; hand-author `resource.json`.
- Do not skip `uip agent refresh --inline-in-flow` followed by `uip agent validate --inline-in-flow` after editing `agent.json` or `resources/*/resource.json`; for tool-bearing agents, pass `--bindings-target <FlowProjectDir>/bindings_v2.json`.
