# Chat (Text-based Conversation) Nodes — Planning

Build a conversational flow whose job is to model a **text-based chat**: a user types, the Flow responds through AI or deterministic answers, and waits for the next message or eventually terminates. For a chat that happens over a **phone call**, use [inline-voice-agent](../inline-voice-agent/planning.md) instead — same idea, different medium, different node types.

The flow is **surface-agnostic**. One conversational flow is consumed from many channels. once deployed, a common SDK lists every conversational flow on the tenant, and every OOTB integration built on that SDK — e.g. web-chat, iframe embedding, UiPath Assistant, Microsoft Teams, Slack — plus any customer's custom UI is able to converse with the chat experience. Author for the conversation, not for a channel.

## Node Types

| Node type | Role |
| --- | --- |
| `core.trigger.conversation` | Starts the flow when a conversation is created. Emits the `conversationId` every other node is addressed by. |
| `uipath.conversational.wait-for-message` | Pauses until the user sends a message (initiates an exchange). Returns the conversation context (which includes the recent exchanges in the chat history), intended for input into a conversational agent node. |
| conversational agent node | Requires the user to initiate an exchange first. Given the conversation context, runs a single response turn, streaming its messages and tool-calls back to the chat. Which node type depends on where the agent lives — see below. |
| `uipath.conversational.send-message` | Requires the user to initiate an exchange first. Sends a flow-composed message (e.g. a handoff notice, results/updates from other nodes) back to the chat. |
| `uipath.conversational.get-conversation-context` | Immediately reads the conversation context without waiting for a user message. Note that wait-for-message already returns the conversation context, so this node should only be used when the direct fetching of the conversation context is truly needed. |

### Pick the agent flavor before you build

The trigger and message nodes are identical whichever you pick. Only the agent node changes — and **ask the user rather than defaulting**, because the answer decides the node type, the ports, and whether you scaffold anything at all:

| Flavor | Node type | Where the agent lives | Choose it when |
| --- | --- | --- | --- |
| **Inline** | `uipath.agent.conversational` | A UUID subdirectory inside this flow project | The agent exists only as part of this conversational flow, or you need [structured outputs](impl.md#structured-outputs) to route on — only inline has them. You scaffold it with `agent init --inline-in-flow --conversational`. |
| **In-solution** | `uipath.core.agent.<projectId>` | A sibling project in the same solution | The agent is its own project, versioned separately, maybe reused by other flows in the solution. Discover it with `registry list --local`. |
| **Published** | `uipath.core.agent.<guid>` | The tenant, already published | The user names an existing agent, or one is already deployed. Discover it with `registry search`. Nothing to scaffold. |

**If the user names an existing agent, it is not inline.** Run `uip maestro flow registry search "<name>" --output json` (and `registry list --local` for solution siblings) before scaffolding anything — the same rule the [agent](../agent/planning.md) plugin states for autonomous agents.

In-solution and published share one node type and one set of ports; inline differs on both (see [Ports](#ports)).

Read each node's current inputs and version from the registry rather than assuming — these move between releases:

```bash
uip maestro flow registry get uipath.conversational.wait-for-message
```

## When to Use

Use these nodes when the flow **is** the conversation: a support chat, an intake questionnaire, a triage bot. The flow's shape generally loops with wait-for-message, but can also have termination - once the flow ends, the conversation gracefully completes, with a UI change to the user that the conversation has completed.

### Chat vs Voice vs Autonomous

| Situation | Text-based conversation (`uipath.agent.conversational`) | Voice ([`uipath.agent.voice`](../inline-voice-agent/planning.md)) | Inline autonomous ([`uipath.agent.autonomous`](../inline-agent/planning.md)) |
| --- | --- | --- | --- |
| The user types and reads replies | Yes | No | No |
| The user is on a phone call | No | Yes | No |
| A reasoning step over flow data, nobody talking | No | No | Yes |
| Reply reaches the user | Streamed by the agent | Spoken on the call | Only through send-message node with the agent's result (high latency) |

### When NOT to Use
- **The conversation is a phone call** — [inline-voice-agent](../inline-voice-agent/planning.md).
- **A single pause for a human to review, approve, or fill in data** — See [hitl](../hitl/planning.md) for a form.

## Critical Rules Any Conversational Flow Must Follow
Combine the nodes, along with flow's other nodes and routing capabilities, to model conversational paths as needed. The **following rules hold for whatever shape you build:**

- **Start with `core.trigger.conversation`.** The trigger alone sets `runtimeOptions.isConversational` in the packed `operate.json`, marking it as a chattable process.
- **Immediately follow the conversation trigger with a wait-for-message node.** This is so the Flow can immediately handle user's first chat message.
  - Related: the flow **cannot send a message "first"** and can only reply. The user must initiate an exchange before conversational agent and send-message nodes can respond, as those nodes require an exchange ID to reply to; this exchange ID is included in the conversation context outputted from a wait-for-message node.
  - Every key in `conversationalAgentSettings` derives from a wait-for-message node's `conversationContext` — see [impl.md](impl.md#the-conversationalagentsettings-wiring-rule).
- **Reach a wait node again to keep the conversation alive.** The flow's response to the latest exchange ends when either arriving back at a wait-for-message node or when the flow ends. The flow may also terminate, and the chat UI will indicate to the user that the conversation has gracefully completed.
- **The conversational agent node streams its own reply.** No send-message is needed for the agent to answer, since its message and tool-calls are streamed automatically to the chat and appended to the conversation history.
- **Leave the conversational agent on the port its flavor exposes** — `success` for inline, `output` for in-solution and published. See [Ports](#ports).

A simple flow that satisfies all the rules:

```
core.trigger.conversation → wait-for-message → conversational agent ──┐
                                   ▲                                   │
                                   └───────────────────────────────────┘
```

That is a starting point, not the only supported shape. Add whatever the conversational flow needs: additional agent and send-message nodes, a decision on the agent's outputs, handoffs, parallel branches to execute behind-the-scenes tasks, an escalation to [hitl](../hitl/planning.md), a connector or RPA call between turns, or no loop back at all when the conversation should end.

### Get Conversation Context

`get-conversation-context` is legal but usually redundant — wait-for-message already returns the context. It may be useful for cases when conversational agent and send-message nodes are chained together (to re-obtain the chat-history between them) or when needing the most up-to-date conversation-history without requiring the user to send a message. Note that you **cannot** immediately use `get-conversation-context` after the `core.trigger.conversation` and use the outputted conversation context as input for conversational agents and send-message nodes, since there is not yet an initiated exchange (see above critical rules).

## Ports

| Node type | Target | Source |
| --- | --- | --- |
| `core.trigger.conversation` | — | `output` |
| `uipath.conversational.wait-for-message` | `input` | `output` |
| `uipath.agent.conversational` (inline) | `input` | `success`, `escalation`, `context`, `tool` |
| `uipath.core.agent.<id>` (in-solution) | `input` | `output` |
| `uipath.core.agent.<id>` (published) | `input` | `output`, `error` |
| `uipath.conversational.send-message` | `input` | `output` |
| `uipath.conversational.get-conversation-context` | `input` | `output` |

Only the inline agent breaks the pattern: `success`, and no `output` port. In-solution and published have `output` and no `success`. Both mistakes are caught — `edge add` lists the real ports, validate reports `Edge references undeclared source handle`. Note `output` is also a variable namespace (`$vars.<id>.output.…`) on every node, which is why the inline agent has one without having the port.

## Output Variables

| Node | Output |
| --- | --- |
| `core.trigger.conversation` | `output.conversationId` |
| `uipath.conversational.wait-for-message` | `output.conversationContext` — an object holding `conversationId`, `latestExchangeId`, `messages`, `userSettings` |
| `uipath.agent.conversational` | `output.uipath__agent_response_messages` — this turn's messages (role, contentParts, toolCalls). The reply is streamed, so there is no `output.response`. |

There is **no `output.exchangeId`** on wait-for-message and **no `output.response`** on the agent. Binding either produces `undefined` at runtime, and `flow validate` does not catch it — invented `$vars` paths pass validation today, so read the real field names off `registry get` rather than trusting a clean validate.

## Scaffolding Prerequisite

The inline agent node points at an agent project directory that must exist first:

```bash
uip agent init "<FlowProjectName>" --inline-in-flow --conversational
```

The returned `ProjectId` is the UUID the node's `inputs.source` must carry. See [impl.md](impl.md) for the scaffold contents and the `agent.json` settings that matter.

## Resources — tools, context, escalation

The `tool`, `context` and `escalation` source ports behave exactly as they do on the inline autonomous node: discover the resource node type through the registry, add the node with `Edit`, wire the artifact edge from the agent's port, and author the matching `resource.json`. Do not re-derive that flow — [inline-agent/impl.md § Adding Resource Nodes](../inline-agent/impl.md#adding-resource-nodes) owns discovery, the one UUID that serves as both `inputs.source` and the sidecar directory, and the `refresh --bindings-target` step that propagates tool bindings into the parent flow.

Three things differ from the autonomous node:

- **There is no `memory` port.** The autonomous node has one; `uipath.agent.conversational` does not. An edge to it fails the same way any bad port does — `edge add` will not list it, and validate reports `Edge references undeclared source handle`.
- **Guardrails ride as a top-level `guardrails` array in the inline agent's `agent.json`**, which `uip agent init --inline-in-flow --conversational` scaffolds for you. Which guardrails apply is flavor-specific — Studio Web's properties panel filters the catalog by conversational vs autonomous — so do not assume a guardrail available on an autonomous agent is offered here.
- **Do not add `guardrails` to `inputSchema.properties`.** That requirement is autonomous-only, where it sits alongside the process arguments. A conversational agent's `inputSchema` stays `{"type": "object", "properties": {}}`; populating it breaks the shape the `uipath-agents` scaffold test asserts.

## Planning Annotation

In the architectural plan:

- `chat-agent: <description>` — one line per agent; omit for a scripted chat. Inline: Reuse the [inline-agent](../inline-agent/planning.md) annotations. In-solution or published: `<agent-name> in <folder-path>`.
- `chat-agent-flavor: <agent-name> = inline | in-solution | published` — one per agent above; decides the node type (`uipath.agent.conversational` for inline, `uipath.core.agent.{key}` for the others) and on which port (`success` for inline, `output` for the others)
- `chat-send-message: <purpose>` — one line per flow-authored message (loading messages, handoff notice, node output results); a scripted chat consists mostly of these
- `chat-structured-output: <agent-name> = <fieldName>` — only when the flow branches on that conversational agent's reply; forces that conversational agent to inline flavor because in-solution and published conversational agents have no structured outputs
- Tools, contexts, and escalations on any inline chat agent reuse the [inline-agent](../inline-agent/planning.md) annotations
