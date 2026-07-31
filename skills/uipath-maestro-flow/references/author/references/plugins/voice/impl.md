# Voice Nodes — Implementation

This plugin covers building the two voice topologies: scaffolding the voice agent's directory, the four node JSON shapes, `callContext` wiring, and what validate/pack/debug enforce. Inline-agent mechanics (the agent subdirectory, `inputs.source`, resource nodes, refresh) are identical to [inline-agent/impl.md](../inline-agent/impl.md) — the voice deltas below are complete on their own; open that file only when the voice agent has tools/contexts/escalations or prompt inputs (the two sections linked from here).

Node type: `uipath.agent.voice`, bound to a local subdirectory via `inputs.source = <projectId>` — the same BPMN contract as the autonomous inline agent. The plumbing nodes serialize to `ConversationalService.CreateOutgoingCall` / `ConversationalService.EndCall` serviceTasks.

## Prerequisite — Scaffold the Voice Agent

```bash
uip agent init "<FlowProjectDir>" --inline-in-flow --conversational --output json
```

Same layout as any inline agent (`<FlowProjectDir>/<projectId-uuid>/` with `agent.json`, `flow-layout.json`, `evals/`, `features/`, `resources/`). **Record the returned `ProjectId`** — the voice node's `inputs.source` must match it exactly.

The scaffold is a conversational agent but has **no `settings.voice` block** — adding it is mandatory (next section).

## Configure `agent.json`

`--conversational` already writes everything a conversational agent needs except the voice block (full `agent.json` shape and per-field rules: the `uipath-agents` skill's [`agent-definition.md`](../../../../../../uipath-agents/references/lowcode/agent-definition.md)). Add `settings.voice` to `<FlowProjectDir>/<projectId>/agent.json`, leaving the scaffolded fields in place:

```json
{
  "settings": {
    "voice": {
      "model": "gemini-3.1-flash-live-preview",
      "maxTokens": 65536,
      "temperature": 0,
      "persona": "Aoede"
    }
  }
}
```

Those are the current Studio Web defaults; the realtime model and persona list are tenant-gated, so confirm them if the call fails to connect.

Field rules:

1. **`settings.voice` is required** — the realtime speech model, its token budget, and the spoken `persona`. This is a *second* model, separate from `settings.model`: `settings.model` is the conversational engine's LLM (reasoning, tool calls); `settings.voice.model` is the realtime audio model.
2. **Leave `settings.engine: "conversational-v1"` and `metadata.isConversational: true` exactly as scaffolded** — both are required at runtime. `flow validate` checks `metadata.isConversational` and errors with `is not a conversational agent` when it is off; a wrong `settings.engine` is *not* caught by validate and surfaces only as a failed call, so do not rely on validation to catch it. Never hand-flip `metadata.isConversational` to repair it; re-scaffold with `uip agent init --inline-in-flow --conversational` (`uipath-agents` critical rule 23).
3. **`outputSchema` MUST stay empty** (`{ "type": "object", "properties": {} }`) — the runtime streams the conversation; a voice agent has no typed output object.
4. Author the system prompt in `messages[0].content` (empty is valid — voice agents have no required prompt field — but a real persona/goal prompt is what makes the call useful). Prompt inputs follow the inline-agent triple: declare under `inputSchema.properties`, reference as `{{input.<key>}}`, rebuild `contentTokens` via `uip agent refresh --inline-in-flow` — see [inline-agent/impl.md § Wiring Flow Variables into Agent Prompts](../inline-agent/impl.md#wiring-flow-variables-into-agent-prompts).
5. `settings.model`, `maxTokens`, `temperature`, `maxIterations` tune the engine LLM as for any conversational agent (`uip agent model list` for the tenant's models).

## Registry Validation

Read the node definitions during Phase 2 to copy into `definitions[]`. All four voice types ship in the CLI's bundled node registry, so `registry get` answers locally — no `uip login` and no `registry pull` required. Fetch only the three types your topology uses:

```bash
uip maestro flow registry get uipath.agent.voice --output json
uip maestro flow registry get uipath.conversational.voice.end-call --output json
# inbound only:
uip maestro flow registry get core.trigger.voice --output json
# outbound only:
uip maestro flow registry get uipath.conversational.voice.create-outgoing-call --output json
```

`uipath.agent.voice` confirms identically to the autonomous inline agent — ports, `model.source: true` hoisting onto `inputs.source`, and `model.serviceType` / `model.version` — see [inline-agent/impl.md § Registry Validation](../inline-agent/impl.md#registry-validation). Voice adds no port or model field to that set. On the plumbing nodes, confirm `ConversationalService.CreateOutgoingCall` / `ConversationalService.EndCall` as `model.serviceType`. Never hand-write `definitions[]` entries — always copy them from `registry get`.

**`registry get` succeeding does not mean the tenant supports voice.** It answers from the bundled registry, so it succeeds offline and on any tenant. Whether conversational voice is actually enabled (and a SIP trunk provisioned) can only be established at deploy/debug time — if the user hasn't confirmed it, raise it as an Open Question rather than treating a clean `registry get` as proof.

## Adding / Editing

For step-by-step add, delete, and wiring procedures, see [editing-operations.md](../../editing-operations.md). Voice nodes are user-owned — author them directly in the `.flow` JSON with `Edit` / `Write` (same rule as the inline autonomous agent; they are not a Flow CLI carve-out).

### The `callContext` wiring rule

The node that originates the call emits `output.callContext`. Bind it into **both** the voice agent and the end-call node, as a structured `jsExpression` binding object (this is the persisted Studio Web shape — not a `=js:` string):

- Inbound: origin is the `core.trigger.voice` node
- Outbound: origin is the `uipath.conversational.voice.create-outgoing-call` node
- `fieldType` mirrors the declared type of the target property in the node definition's `inputDefinition` — read it off `registry get`. For the two voice targets that resolves to `"object"` on the voice agent and `"string"` on the end-call node (a code-editor text field)

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

Exactly two inputs — `source` and `callContext`. Nothing else goes on the instance; see § What NOT to Do for the fields that do *not* belong here and why.

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

Outbound flows bind from the create-outgoing-call node instead: `$vars.createOutgoingCall1.output.callContext`.

### Wire edges with Edit / Write

The trigger's source port is `output`; every other voice edge leaves `success`; targets are always `input`. Edge object shape: [editing-operations-json.md § Add an edge](../../editing-operations-json.md#add-an-edge).

Outbound inserts the call node between trigger and agent: `manualTrigger1 (output) → createOutgoingCall1 (input)`, then `createOutgoingCall1 (success) → voiceAgent1 (input)`. Tool/context/escalation resource nodes wire to the voice agent's artifact ports exactly as in [inline-agent/impl.md § Adding Resource Nodes](../inline-agent/impl.md#adding-resource-nodes).

## Accessing Output

```javascript
// In a Script node after the voice agent
const session = $vars.voiceAgent1.output.uipath__voice_session;
return { callEnded: session.callEnded, endedBy: session.endedBy };
```

- `$vars.{originNodeId}.output.callContext` — the live-call handle (`type`, `id`, `conversationId`); consumed by the voice agent and end-call bindings
- `$vars.{voiceAgentNodeId}.output.uipath__voice_session` — `callEnded` (bool), `endedBy` (`agent`/`user`/`system`/`error`), `reason`. The same node also emits `uipath__voice_call_context` and `uipath__agent_response_messages`
- `$vars.{endCallNodeId}.output.ended` — whether the call was ended
- `$vars.{nodeId}.error` — error details if a node fails

## Validate and Pack

```bash
uip maestro flow format <FlowName>.flow --output json
uip maestro flow validate <FlowName>.flow --output json
```

Voice flows get extra validation on top of the standard checks: the agent directory must exist with a conversational `agent.json` carrying `settings.voice`, and both `callContext` bindings must be present. Failure modes and fixes are in § Debug.

Packing (`uip maestro flow pack`, or `uip solution pack` — see the operate capability) serializes the voice agent to an `Orchestrator.StartInlineAgentJob` serviceTask that **embeds the complete built agent definition** (`agentDefinition` in the BPMN context: agent.json + resources + features), and sets `runtimeOptions.isConversational: true` in the packed `operate.json`. That embedding is why pack and debug fail early when the agent directory is missing.

Debugging (`uip maestro flow debug`) needs a tenant with conversational voice and a live call — always get user consent first, and for outbound flows confirm the `to` number: the flow **places a real phone call**.

## Debug

| Error | Cause | Fix |
| --- | --- | --- |
| `flow validate`: `agent.json not found at <path>` | `inputs.source` UUID doesn't match any subdirectory, or the agent directory was never created | Run `uip agent init "<FlowProjectDir>" --inline-in-flow --conversational`, set `inputs.source` to the returned `ProjectId` |
| `flow validate`: `` has no `settings.voice` `` | Scaffolded agent.json was not hand-edited | Add the `settings.voice` block (§ Configure `agent.json`) |
| `flow validate`: `is not a conversational agent` | `metadata.isConversational` is not `true` — usually the agent was scaffolded without `--conversational` | Re-scaffold with `uip agent init --inline-in-flow --conversational` and repoint `inputs.source` — do not hand-flip `metadata.isConversational` (`uipath-agents` critical rule 23) |
| `flow validate`: `[CONVERSATIONAL_VOICE_CALL_CONTEXT_REQUIRED]` (rule `conversational-voice-call-context`) | Voice agent node lacks the `inputs.callContext` binding | Bind `$vars.<originNodeId>.output.callContext` as a `jsExpression` object with `fieldType: "object"` |
| `flow validate` flags the end-call node's call context (rule `conversational-voice-end-call-context`) | End-call node lacks `inputs.callContext` | Same expression as the voice agent, `fieldType: "string"` |
| `flow validate`: `requires a source UUID at inputs.source` | Voice agent node has no `inputs.source` | Set it to the agent directory's UUID |
| `flow pack` / `flow debug`: `Missing agent definition for voice agent node …` | Agent directory deleted or moved after validate | Restore `<FlowProjectDir>/<projectId>/agent.json` or fix `inputs.source`; the BPMN is never written without the embedded definition |
| `registry get` reports the voice type not found | The installed CLI predates voice support (the types ship in its bundled registry, so this is a CLI-version problem, not a tenant one) | `uip tools update`; re-run `registry get` |
| Call never connects on a tenant that packs and deploys fine | Conversational voice not enabled on the tenant, or no SIP trunk provisioned — neither is detectable from the CLI | Confirm with the user / tenant admin; raise as an Open Question rather than re-authoring the flow |
| Call connects but the agent is silent / call drops immediately | Package built without the embedded `agentDefinition` (hand-rolled pack pipeline), or `settings.voice` removed after pack | Re-pack with the CLI; verify the staged `.bpmn` has `name="agentDefinition"` on the voice serviceTask |
| Outbound call never dials | `from` is not a SIP trunk number on the tenant, or `to` is malformed | Use a provisioned E.164 trunk number for `from`; `to` must be E.164 in a literal binding |

## What NOT to Do

- **Do not scaffold a standalone voice agent** — there is no such thing; `uip agent init` without `--inline-in-flow` builds text agents. A voice agent exists only as an inline conversational agent inside a flow project.
- **Do not set an `isVoice` input flag on the node** — deprecated contract. The converter derives voice mode from the `uipath.agent.voice` node type; the `{"isVoice":true}` job body is emitted for you at pack time.
- **Do not put a `model` block, `systemPrompt`/`userPrompt` placeholders, `agentInputVariables`, or `inputs.voice` on the voice node instance** — it carries exactly `inputs.source` + `inputs.callContext`. Prompts and prompt inputs live in `agent.json`; flow-core hoists `model.source` onto `inputs.source`; validate hydrates `voice` from `agent.json` `settings.voice`.
- **Do not declare `outputSchema` properties on a voice agent** — the schema must stay empty; the runtime streams the conversation and delivers session data via `$vars.<nodeId>.output.uipath__voice_session`.
- **Do not collapse `settings.voice.model` into `settings.model`** — they are two different models (realtime speech vs engine LLM) and both are read.
- **Do not run `uip maestro flow eval` on a voice flow** — the platform blocks voice agents from eval runs; the CLI rejects it with a clear error.
- **Do not hand-write `definitions[]` entries** — copy verbatim from `uip maestro flow registry get <node-type>` on a voice-enabled tenant.
