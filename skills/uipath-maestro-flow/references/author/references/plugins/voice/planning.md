# Voice Nodes — Planning

Voice nodes let a flow hold a real-time AI voice conversation on a live phone call. The centerpiece is `uipath.agent.voice` — an **inline conversational agent** (a subdirectory of the flow project, same mechanics as [inline-agent](../inline-agent/planning.md)) whose `agent.json` carries a `settings.voice` block. Around it sit three plumbing nodes that create, identify, and end the call. There is no standalone voice agent — a voice agent only runs inside a Maestro Flow.

For inline-agent fundamentals (the agent subdirectory, `inputs.source` binding, resource nodes on artifact ports), see [inline-agent/planning.md](../inline-agent/planning.md) — everything there applies to the voice agent node too. This plugin covers what voice adds on top: the node set, the two call topologies, and the `callContext` wiring rule.

## Node Types

| Node Type | Role | When to Select |
| --- | --- | --- |
| `uipath.agent.voice` | Agent | AI agent that converses in real time on a live call. Backed by an inline conversational agent directory (`<uuid>/agent.json` with `settings.voice`) |
| `core.trigger.voice` | Trigger | Start the flow when a phone call arrives on a number bound to the process (inbound topology) |
| `uipath.conversational.voice.create-outgoing-call` | Action | Dial an outbound call and wait until the media stream is open; emits the `callContext` (outbound topology) |
| `uipath.conversational.voice.end-call` | Action | End the active call |

All four are fixed OOTB node types. They appear in the registry on tenants with conversational voice enabled — run `uip login` + `uip maestro flow registry pull`, then `uip maestro flow registry get <node-type>` for definitions.

## When to Use

Use voice nodes when the flow's job is a phone conversation — answering an inbound support line, placing an outbound notification/collection call — and an AI agent should hold that conversation.

### Voice vs Text Agent Decision Table

| Situation | Voice (`uipath.agent.voice`) | Inline autonomous ([`uipath.agent.autonomous`](../inline-agent/planning.md)) |
| --- | --- | --- |
| The interaction is a live phone call | Yes | No |
| Reasoning/judgment step over flow data, no call involved | No | Yes |
| Needs typed `outputSchema` consumed by downstream nodes | No — a voice agent's `outputSchema` stays empty (the runtime streams the conversation) | Yes |
| Needs eval runs (`uip maestro flow eval`) | No — the platform blocks voice agents from eval runs | Yes |

### When NOT to Use

- **No live call in the process** — use [inline-agent](../inline-agent/planning.md) or a published [agent](../agent/planning.md)
- **The "conversation" is text chat, not audio** — voice nodes are call-media-specific
- **You need the agent's answer as structured flow data** — voice agents stream the conversation; they do not return a typed output object

## Topologies

Exactly two supported shapes. The `callContext` originates at the trigger (inbound) or the create-outgoing-call node (outbound) and must reach both the voice agent and the end-call node.

**Inbound** — agent answers a call:

```text
core.trigger.voice (output) → uipath.agent.voice (success) → uipath.conversational.voice.end-call
```

**Outbound** — flow places a call first:

```text
core.trigger.manual (output) → uipath.conversational.voice.create-outgoing-call (success) → uipath.agent.voice (success) → uipath.conversational.voice.end-call
```

## Ports

`uipath.agent.voice` (same artifact ports as the inline autonomous agent):

| Port | Position | Direction | Use |
| --- | --- | --- | --- |
| `input` | left | target | Flow sequence input |
| `success` | right | source | Normal flow output (agent session ended) |
| `error` | right | source | Implicit error port (shared with all action nodes) — see [Implicit error port on action nodes](../../../../shared/file-format.md#implicit-error-port-on-action-nodes) |
| `tool` | bottom | source (artifact) | Connect tool resource nodes |
| `context` | bottom | source (artifact) | Connect context resource nodes |
| `escalation` | top | source (artifact) | Connect escalation resource nodes |

`core.trigger.voice`: single `output` source port (right). `uipath.conversational.voice.create-outgoing-call` and `uipath.conversational.voice.end-call`: `input` (left, target) + `success` (right, source).

## Output Variables

- `$vars.{triggerNodeId}.output.callContext` — inbound: identifies the live call (`{ type: "phone"|"web", id, conversationId }`). Bind into the voice agent and end-call nodes.
- `$vars.{createOutgoingCallNodeId}.output.callContext` — outbound: same shape, emitted once the outbound media stream is open.
- `$vars.{voiceAgentNodeId}.output` — end-of-session data: `uipath__voice_session` (`callEnded`, `endedBy: "agent"|"user"|"system"|"error"`, `reason`), `uipath__voice_call_context`, `uipath__agent_response_messages`.
- `$vars.{endCallNodeId}.output.ended` — whether the call was ended.
- `$vars.{nodeId}.error` — error details on any of the four (`code`, `message`, `detail`, `category`, `status`).

## Scaffolding Prerequisite

The voice agent's backing directory is created with the same command as any inline agent, plus the conversational flag:

```bash
uip agent init "<FlowProjectDir>" --inline-in-flow --conversational --output json
```

Record the returned `ProjectId` — the voice node's `inputs.source` must match it exactly. The scaffold produces a conversational agent (`settings.engine: "conversational-v1"`, `metadata.isConversational: true`) **without** a `settings.voice` block — adding it by hand is mandatory, or `flow validate` fails. Shape and defaults: [impl.md § Configure `agent.json`](impl.md#configure-agentjson).

## Planning Annotation

In the architectural plan:

- `voice-topology: inbound | outbound` — which of the two shapes
- `voice-agent: <description>` with a `<projectId-placeholder>` — the UUID is assigned during Phase 2 when `uip agent init --inline-in-flow --conversational` runs
- Outbound only: `voice-from: <SIP trunk E.164 number>` and `voice-to: <destination E.164 number>` — `from` must be a number provisioned on the tenant; flag unknowns as Open Questions
- Tools/contexts/escalations on the voice agent reuse the [inline-agent](../inline-agent/planning.md) annotations
