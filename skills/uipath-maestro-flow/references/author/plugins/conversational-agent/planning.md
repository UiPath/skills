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
| **Inline** | `uipath.agent.conversational` | A UUID subdirectory inside this flow project | The agent exists only to serve this chat. You scaffold it with `agent init --inline-in-flow`. |
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

## Topology

One loop, and the trigger is what makes it a chat:

```
core.trigger.conversation
        │
        ▼
wait-for-message ──▶ conversational agent ──────────────┐
        ▲              (success inline, output otherwise)│
        └───────────────────────────────────────────────┘
```

The agent streams its own reply, so **no send-message is needed for the agent to answer**. Add send-message only when the flow itself has something to say — a greeting before the first wait, or a message when handing off.

`get-conversation-context` is legal but usually redundant, and an unconnected one does not fail validation.

### The trigger is the whole distinction

`runtimeOptions.isConversational` in the packed `operate.json` is set by the **trigger alone**. An agent — inline, in-solution or published — does not make its caller conversational. A chat agent hung off a manual trigger packs without the marker and is not listed as a Conversational Agent, and nothing reports an error.

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

**The inline agent has no `output` port** — it continues on `success`. Wiring it as `output` fails: `edge add` reports `Source port "output" not found on node`, and a hand-written edge referencing it fails validation.

In-solution and published agents are the opposite: they continue on `output` and have no `success`. Read the ports off the node's own definition rather than carrying the inline rule across.

## Output Variables

| Node | Output |
| --- | --- |
| `core.trigger.conversation` | `output.conversationId` |
| `uipath.conversational.wait-for-message` | `output.conversationContext` — an object holding `conversationId`, `latestExchangeId`, `messages`, `userSettings` |
| `uipath.agent.conversational` | Declares no output properties — the reply is streamed, not returned |

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
