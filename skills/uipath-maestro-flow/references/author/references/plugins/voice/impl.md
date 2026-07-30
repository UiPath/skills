# Voice Nodes — Implementation

This plugin covers building the two voice topologies: scaffolding the voice agent's directory, the four node JSON shapes, `callContext` wiring, and what validate/pack/debug enforce. Inline-agent mechanics (the agent subdirectory, `inputs.source`, resource nodes, refresh) are identical to [inline-agent/impl.md](../inline-agent/impl.md) — read it first; only voice-specific deltas are documented here.

Node type: `uipath.agent.voice`, bound to a local subdirectory via `inputs.source = <projectId>`. Its BPMN `serviceType` (`Orchestrator.StartInlineAgentJob`, `v2`) comes from the definition in `definitions[]`, same as the autonomous inline agent. The plumbing nodes serialize to `ConversationalService.CreateOutgoingCall` / `ConversationalService.EndCall` serviceTasks.

## Prerequisite — Scaffold the Voice Agent

```bash
uip agent init "<FlowProjectDir>" --inline-in-flow --conversational --output json
```

Same layout as any inline agent (`<FlowProjectDir>/<projectId-uuid>/` with `agent.json`, `flow-layout.json`, `evals/`, `features/`, `resources/`). **Record the returned `ProjectId`** — the voice node's `inputs.source` must match it exactly.

The scaffold is a conversational agent but has **no `settings.voice` block** — add it by hand (next section). Without it, `flow validate` fails with `has no settings.voice`.

## Configure `agent.json`

Edit `<FlowProjectDir>/<projectId>/agent.json`. The canonical shape (what Studio Web writes for a voice agent — field values below are the current Studio Web defaults; confirm the live voice model/persona list against your tenant):

```json
{
  "settings": {
    "model": "anthropic.claude-sonnet-4-5-20250929-v1:0",
    "maxTokens": 8192,
    "temperature": 0,
    "engine": "conversational-v1",
    "maxIterations": 8,
    "mode": "standard",
    "voice": {
      "model": "gemini-3.1-flash-live-preview",
      "maxTokens": 65536,
      "temperature": 0,
      "persona": "Aoede"
    }
  },
  "inputSchema": { "type": "object", "properties": {} },
  "outputSchema": { "type": "object", "properties": {} },
  "metadata": { "isConversational": true },
  "type": "lowCode",
  "guardrails": [],
  "messages": [
    { "role": "system", "content": "", "contentTokens": [] },
    { "role": "user", "content": "", "contentTokens": [] }
  ],
  "projectId": "<projectId-uuid>"
}
```

Field rules — three are hard contract, the rest are tunable:

1. **`settings.voice` is required** — the realtime speech model, its token budget, and the spoken `persona`. This is a *second* model, separate from `settings.model`: `settings.model` is the conversational engine's LLM (reasoning, tool calls); `settings.voice.model` is the realtime audio model. Do not collapse them.
2. **`settings.engine: "conversational-v1"` + `metadata.isConversational: true` are required** — `flow validate` errors with `is not a conversational agent` when either is off.
3. **`outputSchema` MUST stay empty** (`{ "type": "object", "properties": {} }`) — the runtime streams the conversation; a voice agent has no typed output object. Do not declare output properties.
4. Author the system prompt in `messages[0].content` (empty is valid — voice agents have no required prompt field — but a real persona/goal prompt is what makes the call useful). Prompt inputs follow the inline-agent triple: declare under `inputSchema.properties`, reference as `{{input.<key>}}`, rebuild `contentTokens` via `uip agent refresh --inline-in-flow` — see [inline-agent/impl.md § Wiring Flow Variables into Agent Prompts](../inline-agent/impl.md#wiring-flow-variables-into-agent-prompts).
5. `settings.model`, `maxTokens`, `temperature`, `maxIterations` tune the engine LLM as for any conversational agent (`uip agent model list` for the tenant's models).

## Registry Validation

Validate the node types against the registry during Phase 2. The voice types ship on tenants with conversational voice enabled — they need an authenticated `uip maestro flow registry pull` first:

```bash
uip maestro flow registry get uipath.agent.voice --output json
uip maestro flow registry get core.trigger.voice --output json
uip maestro flow registry get uipath.conversational.voice.create-outgoing-call --output json
uip maestro flow registry get uipath.conversational.voice.end-call --output json
```

Confirm on `uipath.agent.voice`:

- Input port: `input`; output port: `success`; artifact ports: `escalation` (top), `context` + `tool` (bottom)
- The definition declares `model.source: true`; flow-core hoists that identity field onto the node instance as `inputs.source`
- `model.serviceType` — `Orchestrator.StartInlineAgentJob`, `model.version` — `v2`

Confirm `ConversationalService.CreateOutgoingCall` / `ConversationalService.EndCall` as the plumbing nodes' `model.serviceType`. If `registry get` reports the type as not found or not enabled, the tenant does not have conversational voice — surface it as an Open Question; do not hand-write definitions.

## Adding / Editing

Voice nodes are user-owned: author them directly in the `.flow` JSON with `Edit` / `Write` (same rule as the inline autonomous agent — they are not a Flow CLI carve-out). Copy each type's definition verbatim from `registry get` into `definitions[]`, add a `variables.nodes[]`-regenerating `uip maestro flow format` at the end, and follow [editing-operations.md](../../editing-operations.md) for the general procedure.

### The `callContext` wiring rule

The node that originates the call emits `output.callContext`. Bind it into **both** the voice agent and the end-call node, as a structured `jsExpression` binding object (this is the persisted Studio Web shape — not a `=js:` string):

- Inbound: origin is the `core.trigger.voice` node
- Outbound: origin is the `uipath.conversational.voice.create-outgoing-call` node
- `fieldType` differs by target: `"object"` on the voice agent, `"string"` on the end-call node (a code-editor text field)

### Node JSON — inbound trigger

```json
{
  "id": "incomingCall1",
  "type": "core.trigger.voice",
  "typeVersion": "1.0",
  "display": { "label": "Incoming call", "shape": "circle", "icon": "phoneIncoming" },
  "inputs": { "entryPointId": "<generated-uuid>" }
}
```

`inputs.entryPointId` is a fresh UUID, same convention as other triggers ([shared/file-format.md](../../../../shared/file-format.md)). The phone number is bound to the process at deploy time, not in the `.flow`.

### Node JSON — create outgoing call (outbound only)

```json
{
  "id": "createOutgoingCall1",
  "type": "uipath.conversational.voice.create-outgoing-call",
  "typeVersion": "1.0",
  "display": { "label": "Create outgoing call", "icon": "phoneOutgoing" },
  "inputs": {
    "from": "<SIP-trunk-E164-number>",
    "to": { "type": "literal", "expression": "<destination-E164-number>", "fieldType": "string" }
  }
}
```

`from` is a **plain string** (an E.164 number provisioned as a SIP trunk on the tenant); `to` is a literal binding object. Both are required.

### Node JSON — voice agent

```json
{
  "id": "voiceAgent1",
  "type": "uipath.agent.voice",
  "typeVersion": "1.0",
  "display": { "label": "Voice agent", "shape": "rectangle", "icon": "phone" },
  "inputs": {
    "source": "<projectId-uuid>",
    "callContext": {
      "type": "jsExpression",
      "expression": "$vars.incomingCall1.output.callContext",
      "fieldType": "object"
    }
  }
}
```

Exactly two inputs. **No per-instance `model` block** (flow-core hoists the definition's `model.source: true` onto `inputs.source`), **no `inputs.systemPrompt`/`userPrompt` placeholders** (unlike the autonomous agent — the voice validator does not require them; prompts live in `agent.json`), and **no hand-authored `inputs.voice`** (validate derives it from `agent.json` `settings.voice`).

### Node JSON — end call

```json
{
  "id": "endCall1",
  "type": "uipath.conversational.voice.end-call",
  "typeVersion": "1.0",
  "display": { "label": "End call", "icon": "phoneOff" },
  "inputs": {
    "callContext": {
      "type": "jsExpression",
      "expression": "$vars.incomingCall1.output.callContext",
      "fieldType": "string"
    }
  }
}
```

Same expression as the voice agent's binding, `fieldType: "string"`. Outbound flows bind from the create-outgoing-call node instead: `$vars.createOutgoingCall1.output.callContext`.

### Wire edges with Edit / Write

The trigger's source port is `output`; every other voice edge leaves `success`; targets are always `input`:

```json
{ "id": "<EDGE_ID>", "sourceNodeId": "incomingCall1", "sourcePort": "output", "targetNodeId": "voiceAgent1", "targetPort": "input" }
```

```json
{ "id": "<EDGE_ID>", "sourceNodeId": "voiceAgent1", "sourcePort": "success", "targetNodeId": "endCall1", "targetPort": "input" }
```

Outbound inserts the call node between trigger and agent: `manualTrigger1 (output) → createOutgoingCall1 (input)`, then `createOutgoingCall1 (success) → voiceAgent1 (input)`. Tool/context/escalation resource nodes wire to the voice agent's artifact ports exactly as in [inline-agent/impl.md § Adding Resource Nodes](../inline-agent/impl.md#adding-resource-nodes).

## Accessing Output

```javascript
// In a Script node after the voice agent
const session = $vars.voiceAgent1.output.uipath__voice_session;
return { callEnded: session.callEnded, endedBy: session.endedBy };
```

- `$vars.{originNodeId}.output.callContext` — the live-call handle (`type`, `id`, `conversationId`); consumed by the voice agent and end-call bindings
- `$vars.{voiceAgentNodeId}.output.uipath__voice_session` — `callEnded` (bool), `endedBy` (`agent`/`user`/`system`/`error`), `reason`
- `$vars.{endCallNodeId}.output.ended` — whether the call was ended
- `$vars.{nodeId}.error` — error details if a node fails

## Validate and Pack

```bash
uip maestro flow format <FlowName>.flow --output json
uip maestro flow validate <FlowName>.flow --output json
```

Voice flows get extra validation on top of the standard checks: the agent directory must exist with a conversational `agent.json` carrying `settings.voice`, and both `callContext` bindings must be present (flow-schema rules `conversational-voice-call-context` / `conversational-voice-end-call-context`).

Packing (`uip maestro flow pack`, or `uip solution pack` — see the operate capability) serializes the voice agent to an `Orchestrator.StartInlineAgentJob` serviceTask that **embeds the complete built agent definition** (`agentDefinition` in the BPMN context: agent.json + resources + features), plus `voice.mode: "maestro_flow"` and an `{"isVoice":true,"callContext":…}` job body. This embedding is why pack and debug fail early when the agent directory is missing — a voice serviceTask without its `agentDefinition` deploys but every call dies silently. The packed `operate.json` gains `runtimeOptions.isConversational: true` automatically when the flow has voice nodes.

Debugging (`uip maestro flow debug`) needs a tenant with conversational voice and a live call — always get user consent first, and for outbound flows confirm the `to` number: the flow **places a real phone call**.

## Debug

| Error | Cause | Fix |
| --- | --- | --- |
| `flow validate`: `agent.json not found at <path>` | `inputs.source` UUID doesn't match any subdirectory, or the agent directory was never created | Run `uip agent init "<FlowProjectDir>" --inline-in-flow --conversational`, set `inputs.source` to the returned `ProjectId` |
| `flow validate`: `` has no `settings.voice` `` | Scaffolded agent.json was not hand-edited | Add the `settings.voice` block (§ Configure `agent.json`) |
| `flow validate`: `is not a conversational agent` | `metadata.isConversational` false/missing, or wrong engine | Set `metadata.isConversational: true` and `settings.engine: "conversational-v1"` |
| `flow validate`: `[CONVERSATIONAL_VOICE_CALL_CONTEXT_REQUIRED]` | Voice agent node lacks the `inputs.callContext` binding | Bind `$vars.<originNodeId>.output.callContext` as a `jsExpression` object with `fieldType: "object"` |
| `flow validate` flags the end-call node's call context | End-call node lacks `inputs.callContext` | Same expression as the voice agent, `fieldType: "string"` |
| `flow validate`: `requires a source UUID at inputs.source` | Voice agent node has no `inputs.source` | Set it to the agent directory's UUID |
| `flow pack` / `flow debug`: `Missing agent definition for voice agent node …` | Agent directory deleted or moved after validate | Restore `<FlowProjectDir>/<projectId>/agent.json` or fix `inputs.source`; the BPMN is never written without the embedded definition |
| `registry get` reports the voice type not found / not enabled | Tenant lacks conversational voice, or no authenticated `registry pull` was run | `uip login`, `uip maestro flow registry pull`, retry; if still absent, the tenant isn't voice-enabled — Open Question |
| Call connects but the agent is silent / call drops immediately | Package built without the embedded `agentDefinition` (hand-rolled pack pipeline), or `settings.voice` removed after pack | Re-pack with the CLI; verify the staged `.bpmn` has `name="agentDefinition"` on the voice serviceTask |
| Outbound call never dials | `from` is not a SIP trunk number on the tenant, or `to` is malformed | Use a provisioned E.164 trunk number for `from`; `to` must be E.164 in a literal binding |

## What NOT to Do

- **Do not scaffold a standalone voice agent** — there is no such thing; `uip agent init` without `--inline-in-flow` builds text agents. A voice agent exists only as an inline conversational agent inside a flow project.
- **Do not set an `isVoice` input flag on the node** — deprecated contract. The converter derives voice mode from the `uipath.agent.voice` node type; the `{"isVoice":true}` job body is emitted for you at pack time.
- **Do not declare `outputSchema` properties on a voice agent** — the schema must stay empty; the runtime streams the conversation and delivers session data via `$vars.<nodeId>.output.uipath__voice_session`.
- **Do not hand-author `inputs.voice` on the flow node** — validate hydrates it from `agent.json` `settings.voice`; the agent.json is the source of truth.
- **Do not collapse `settings.voice.model` into `settings.model`** — they are two different models (realtime speech vs engine LLM) and both are read.
- **Do not run `uip maestro flow eval` on a voice flow** — the platform blocks voice agents from eval runs; the CLI rejects it with a clear error.
- **Do not put a `model` block, `systemPrompt`/`userPrompt` placeholders, or `agentInputVariables` on the voice node instance** — the voice node carries exactly `inputs.source` + `inputs.callContext`; prompts and prompt inputs live in `agent.json`.
- **Do not hand-write `definitions[]` entries** — copy verbatim from `uip maestro flow registry get <node-type>` on a voice-enabled tenant.
