# Conversational (Text Chat) Nodes — Planning

Plan a flow whose job is a **text chat**: a user types, an AI agent answers, the flow waits for the next message. For a chat that happens over a **phone call**, use [inline-voice-agent](../inline-voice-agent/planning.md) instead — same idea, different medium, different node types.

## Node Types

| Node type | Role |
| --- | --- |
| `core.trigger.conversation` | Starts the flow when a conversation is created. Emits the `conversationId` every other node is addressed by. |
| `uipath.conversational.wait-for-message` | Pauses until the user sends a message. Returns the conversation context the agent reads. |
| the agent node | Reads the conversation and streams its reply straight to the chat. Which node type depends on where the agent lives — see below. |
| `uipath.conversational.send-message` | Writes a message the **flow** composes — a greeting, a handoff notice. Not the agent's reply. |
| `uipath.conversational.get-conversation-context` | Reads recent exchanges without waiting. Rarely needed — wait-for-message already returns the context. |

### Pick the agent flavor before you build

The trigger and message nodes are identical whichever you pick. Only the agent node changes — and **ask the user rather than defaulting**, because the answer decides the node type, the ports, and whether you scaffold anything at all:

| Flavor | Node type | Where the agent lives | Choose it when |
| --- | --- | --- | --- |
| **Inline** | `uipath.agent.conversational` | A UUID subdirectory inside this flow project | The agent exists only to serve this chat, or you need [structured outputs](impl.md#structured-outputs) to route on — only inline has them. You scaffold it with `agent init --inline-in-flow --conversational`. |
| **In-solution** | `uipath.core.agent.<projectId>` | A sibling project in the same solution | The agent is its own project, versioned separately, maybe reused by other flows in the solution. Discover it with `registry list --local`. |
| **Published** | `uipath.core.agent.<guid>` | The tenant, already published | The user names an existing agent, or one is already deployed. Discover it with `registry search`. Nothing to scaffold. |

**If the user names an existing agent, it is not inline.** Run `uip maestro flow registry search "<name>" --output json` (and `registry list --local` for solution siblings) before scaffolding anything — the same rule the [agent](../agent/planning.md) plugin states for autonomous agents.

In-solution and published share one node type and one set of ports; inline differs on both (see [Ports](#ports)).

Read each node's current inputs and version from the registry rather than assuming — these move between releases:

```bash
uip maestro flow registry get uipath.conversational.wait-for-message
```

## When to Use

Use these nodes when the process **is** the conversation: a support chat, an intake questionnaire, a triage bot. The flow's shape is a loop, and it stays alive between turns.

### Chat vs Voice vs Autonomous

| Situation | Conversational text (`uipath.agent.conversational`) | Voice ([`uipath.agent.voice`](../inline-voice-agent/planning.md)) | Inline autonomous ([`uipath.agent.autonomous`](../inline-agent/planning.md)) |
| --- | --- | --- | --- |
| The user types and reads replies | Yes | No | No |
| The user is on a phone call | No | Yes | No |
| A reasoning step over flow data, nobody talking | No | No | Yes |
| Runs to completion in one pass | No — it waits for turns | No | Yes |
| Reply reaches the user | Streamed by the agent | Spoken on the call | Returned as node output |

### When NOT to Use

- **Nobody is conversing** — a reasoning or extraction step is [inline-agent](../inline-agent/planning.md) or a published [agent](../agent/planning.md).
- **The conversation is a phone call** — [inline-voice-agent](../inline-voice-agent/planning.md).
- **A single question with a typed answer** — a chat loop is the wrong shape; use [hitl](../hitl/planning.md) for a form.

## Rules Any Chat Flow Must Follow

Combine the nodes however the conversation needs. These hold whatever shape you build:

- **Start with `core.trigger.conversation`.** The trigger alone sets `runtimeOptions.isConversational` in the packed `operate.json`. An agent — inline, in-solution or published — does not make its caller conversational, so a chat agent hung off a manual trigger packs without the marker, is not listed as a Conversational Agent, and nothing reports an error.
- **The agent reads a wait node's context.** Every key in `conversationalAgentSettings` derives from one wait-for-message node's `conversationContext` — see [impl.md](impl.md#the-conversationalagentsettings-wiring-rule).
- **Reach a wait node again to keep the conversation alive.** After the agent answers, control has to arrive back at a wait node — directly, or through any nodes in between — or the conversation ends after that turn. Arriving there is also what ends the exchange; there is no flag to set.
- **The agent streams its own reply.** No send-message is needed for the agent to answer. Add one only when the flow itself speaks — a greeting, a handoff notice.
- **Leave the agent on the port its flavor exposes** — `success` for inline, `output` for in-solution and published. See [Ports](#ports).

The smallest flow that satisfies all five:

```
core.trigger.conversation → wait-for-message → conversational agent ──┐
                                   ▲                                   │
                                   └───────────────────────────────────┘
```

That is a starting point, not the supported shape. Whatever else the conversation needs goes between those nodes — a greeting before the first wait, a decision on the agent's reply, an escalation to [hitl](../hitl/planning.md), a connector or RPA call between turns, or no loop back at all when one answer ends it.

`get-conversation-context` is legal but usually redundant — wait-for-message already returns the context — and an unconnected one does not fail validation.

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

## Planning Annotation

When planning a chat flow, state:

- **The loop** — which node the agent returns to, and on which port (`success` for an inline agent, `output` for in-solution or published)
- **Which flavor** — inline, in-solution or published; it decides the node type and the ports
- **The context binding** — the agent's `conversationalAgentSettings.context`, and which wait node it reads
- **Who speaks** — the agent streams its replies; list any send-message the flow itself needs
- **Testing** — `flow debug` cannot drive a chat headlessly; it uploads and hands off to Studio Web or the VS Code extension
