# Voice Nodes — Planning

Voice nodes let a flow hold a real-time AI voice conversation on a live phone call. The centerpiece is `uipath.agent.voice` — an **inline conversational agent** whose `agent.json` carries a `settings.voice` block. Around it sit three nodes that start, place, and end the call. There is no standalone voice agent — a voice agent only runs inside a Maestro Flow.

For inline-agent fundamentals (the agent subdirectory, `inputs.source` binding, resource nodes on artifact ports), see [inline-agent/planning.md](../inline-agent/planning.md) — everything there applies to the voice agent node too. This plugin covers what voice adds on top: the node set, the two call topologies, and the `callContext` wiring rule.

## Node Types

| Node Type | Role | When to Select |
| --- | --- | --- |
| `uipath.agent.voice` | Agent | AI agent that converses in real time on a live call. Backed by an inline conversational agent directory (`<uuid>/agent.json` with `settings.voice`) |
| `core.trigger.voice` | Trigger | Start the flow when a phone call arrives on a number bound to the process (inbound topology) |
| `uipath.conversational.voice.create-outgoing-call` | Action | Dial an outbound call and wait until the media stream is open; emits the `callContext` (outbound topology) |
| `uipath.conversational.voice.end-call` | Action | End the active call |

All four are fixed OOTB node types. They ship in the CLI's bundled registry, so `registry get` resolves them offline on any tenant — a clean `registry get` confirms the *node shapes*, not that the tenant can place calls. SIP trunk provisioning is only observable at deploy/debug time — check it with `trunks list` below. Commands: [impl.md § Registry Validation](impl.md#registry-validation).

## Phone Numbers and SIP Trunks

Both topologies need a SIP trunk on the tenant, and **direction is a separate flag from existence** — a number that exists may still be unusable for your topology:

```bash
uip conversational trunks list --direction outbound --output json   # outbound `from`
uip conversational trunks list --direction inbound  --output json   # inbound binding
```

- **Outbound `inputs.from`** — one of the tenant's outbound-enabled trunks. `trunks list --direction outbound` enumerates the candidates; each trunk's `phoneNumber` is a usable value. A number that is only inbound-enabled fails at dial time, not at validate.
- **Outbound `inputs.to`** — the user's to give. Who gets called is not a tenant fact and not the agent's call to make.
- **Inbound** — the number you bind must have `inboundEnabled: true`. A tenant can easily have several trunks where only one qualifies.
- A trunk already showing a non-null `processKey` is bound to another process; re-pointing it needs `--yes` and **silently takes the number away from that process**. Confirm with the user before reusing one.
- **`trunks list` returning nothing is not something you can fix from the CLI.** The CLI can read trunks and bind one to a process — it cannot add a number, enable a direction on one, or release one back. Those are portal-only, on the **Phone numbers** page:

  ```text
  {baseUrl}/{orgName}/agents_/phone-numbers
  # e.g. https://alpha.uipath.com/conversationalagents/agents_/phone-numbers
  ```

  It is org-scoped (no tenant segment) — build it from `uip login status --output json` (`Data.BaseUrl` + `Data.Organization`). There is no `trunks create`.

Numbers referenced in older examples go stale — always re-list rather than copying a number out of a doc or an existing flow. Binding an inbound number is a deploy-time step, not a `.flow` edit: [impl.md § Bind an Inbound Phone Number](impl.md#bind-an-inbound-phone-number).

## When to Use

Use voice nodes when the flow's job is a phone conversation — answering an inbound support line, placing an outbound notification/collection call — and an AI agent should hold that conversation.

### Voice vs Text Agent Decision Table

| Situation | Voice (`uipath.agent.voice`) | Inline autonomous ([`uipath.agent.autonomous`](../inline-agent/planning.md)) |
| --- | --- | --- |
| The interaction is a live phone call | Yes | No |
| Reasoning/judgment step over flow data, no call involved | No | Yes |
| Needs typed `outputSchema` consumed by downstream nodes | Optional — the node emits three fixed `uipath__*` outputs regardless; custom schema properties merge with them | Yes |
| Needs eval runs (`uip maestro flow eval`) | No — the platform blocks voice agents from eval runs | Yes |

### When NOT to Use

- **No live call in the process** — use [inline-agent](../inline-agent/planning.md) or a published [agent](../agent/planning.md)
- **The "conversation" is text chat, not audio** — voice nodes are call-media-specific

## Topologies

Exactly two supported shapes. The `callContext` originates at the trigger (inbound) or the create-outgoing-call node (outbound) and must reach both the voice agent and the end-call node. **Both shapes live at the top level of the `.flow`** — a voice agent node inside a `core.subflow` is rejected by `flow validate` and by pack; see [impl.md § What NOT to Do](impl.md#what-not-to-do).

**Inbound** — agent answers a call:

```text
core.trigger.voice (output) → uipath.agent.voice (success) → uipath.conversational.voice.end-call
```

**Outbound** — flow places a call first:

```text
core.trigger.manual (output) → uipath.conversational.voice.create-outgoing-call (success) → uipath.agent.voice (success) → uipath.conversational.voice.end-call
```

### Picking a topology changes how the flow is tested

Only a real inbound call can raise a `core.trigger.voice`, so **`uip maestro flow debug` refuses an inbound flow outright** (`Inbound voice flows cannot be debugged from the CLI.`). Testing it means the full deploy path — publish, bind a number, then dial it — while an outbound flow runs under `flow debug` directly and places its call from the CLI.

| | Inbound | Outbound |
| --- | --- | --- |
| Trigger | `core.trigger.voice` | `core.trigger.manual` (or any other trigger) |
| `uip maestro flow debug` | **Rejected** — publish + bind + dial the number | Runs, and places a real call |
| Phone number | Bound to the deployed release ([impl.md § Bind an Inbound Phone Number](impl.md#bind-an-inbound-phone-number)) | Named directly in `inputs.from` |
| Needs a deploy to test at all | Yes | No |

Outbound is the only shape with a local test loop; inbound cannot be exercised at all until it is deployed and a number is bound to it.

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

`core.trigger.voice`: single `output` source port (right). `uipath.conversational.voice.create-outgoing-call` and `uipath.conversational.voice.end-call`: `input` (left, target) + `success` (right, source) + the implicit `error` port.

## Output Variables

- `$vars.{originNodeId}.output.callContext` — the live-call handle (`{ type: "phone"|"web", id, conversationId }`). Origin is the trigger (inbound) or the create-outgoing-call node (outbound); it must be bound into **both** the voice agent and the end-call node.
- `$vars.{voiceAgentNodeId}.output` — end-of-session data (`uipath__voice_session`, `uipath__voice_call_context`, `uipath__agent_response_messages`), not a typed result object. Field shapes: [impl.md § Accessing Output](impl.md#accessing-output).
- `$vars.{endCallNodeId}.output.ended` — whether the call was ended.
- `$vars.{nodeId}.error` — error details (`code`, `message`, `detail`, `category`, `status`) on the three action nodes: `uipath.agent.voice`, create-outgoing-call, end-call. `core.trigger.voice` has no `error` — its outputDefinition is `output` only.

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
- Outbound only: `voice-from: <SIP trunk E.164 number>` — one of the tenant's outbound-enabled trunks (§ Phone Numbers and SIP Trunks) — and `voice-to: <destination E.164 number>`, which the user supplies
- Tools/contexts/escalations on the voice agent reuse the [inline-agent](../inline-agent/planning.md) annotations
