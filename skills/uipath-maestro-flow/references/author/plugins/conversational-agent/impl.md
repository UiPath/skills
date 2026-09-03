# Conversational (Text Chat) Nodes — Implementation

Wire whatever shape the conversation needs, inside the rules in [planning.md](planning.md#rules-any-chat-flow-must-follow).

For a phone conversation, use [inline-voice-agent/impl.md](../inline-voice-agent/impl.md) instead.

Everything here is the same for all three agent flavors except the agent node itself and its port. Settle the flavor first — [planning.md](planning.md#pick-the-agent-flavor-before-you-build).

## Resolve the Agent

**Inline** — scaffold it, from the solution root:

```bash
uip agent init "<FlowProjectName>" --inline-in-flow --conversational
```

Writes `<FlowProject>/<uuid>/agent.json` plus `flow-layout.json`, and returns `Data.ProjectId`. **Keep that UUID** — it is what the agent node's `inputs.source` must carry.

**In-solution** — the agent is a sibling project; nothing to scaffold in the flow. Find its node type:

```bash
uip maestro flow registry list --local --output json
```

**Published** — already on the tenant:

```bash
uip maestro flow registry search "<agent name>" --output json
```

Both of the latter give a `uipath.core.agent.<id>` node type. `registry get` on it returns `inputDefaults` holding `isConversational: true` and `conversationalAgentSettings`, which is how you confirm the agent really is a chat agent rather than an autonomous one. Discovery details live in [agent/impl.md](../agent/impl.md#discovery).

**If an in-solution agent comes back autonomous**, the registry could not read its `agent.json` — it builds that node from the sibling project's file, and falls back to autonomous when the file is missing or malformed. Re-run with `--log-level debug` and it names the reason:

```
[DEBUG] Unparseable agent.json in <projectDir>: … The node will describe an autonomous agent.
[DEBUG] No readable agent.json in <projectDir>; the node will describe an autonomous agent.
```

Nothing else reports it, and the authored node would run as autonomous with no error at any step. Published agents are unaffected — their flag comes from the release, not a local file.

## Configure `agent.json`

Edit the scaffolded file, then regenerate its derived fields:

```bash
uip agent refresh "<FlowProject>/<uuid>" --inline-in-flow
uip agent validate "<FlowProject>/<uuid>" --inline-in-flow
```

`refresh` rebuilds `contentTokens[]` from `messages[].content`. **Skip it and `agent validate` fails** with `contentTokens has 0 entries but content requires 1` — the error does not name `agent refresh`, so it is easy to get stuck on.

Run `refresh` after any `agent.json` edit — for an in-solution agent too, without the flag: `uip agent refresh "<AgentProject>"`. A published agent has no local file, so there is nothing to refresh.

Settings that matter for a conversational agent:

| Key | Value | Why |
| --- | --- | --- |
| `settings.engine` | `conversational-v1` | What makes it a chat agent rather than autonomous |
| `metadata.isConversational` | `true` | Read by the registry to pick the icon and keep the agent out of the agent-as-tool picker |
| `settings.maxIterations` | `8` | keep what the scaffold wrote |

`uip agent init --conversational` writes all three. Do not remove them.

## Registry Validation

`flow validate` has **no registry fallback** — a hand-authored node must carry its manifest in the file's `definitions[]`. Fetch one per node type in the flow:

```bash
uip maestro flow registry get core.trigger.conversation --output json
uip maestro flow registry get uipath.conversational.wait-for-message --output json
uip maestro flow registry get uipath.agent.conversational --output json
```

Append each `Data.Node` verbatim to the `.flow`'s `definitions[]`, and set the node's `typeVersion` to exactly the `version` the command returned. Miss one and validate reports `Node type "<type>:<version>" has no matching definition`.

The conversational agent node requires a login; the trigger and the tool nodes resolve from the bundled catalog.

## The `conversationalAgentSettings` Wiring Rule

This is the one that goes wrong silently. The agent reads the conversation through `inputs.conversationalAgentSettings`, which holds **five** keys — a `context` binding plus four fields derived from it:

```json
"conversationalAgentSettings": {
  "mode": "simple",
  "context":        { "type": "jsExpression", "expression": "$vars.waitForMessage1.output.conversationContext",                  "fieldType": "object" },
  "conversationId": { "type": "jsExpression", "expression": "$vars.waitForMessage1.output.conversationContext.conversationId",   "fieldType": "string" },
  "exchangeId":     { "type": "jsExpression", "expression": "$vars.waitForMessage1.output.conversationContext.latestExchangeId", "fieldType": "string" },
  "messages":       { "type": "jsExpression", "expression": "$vars.waitForMessage1.output.conversationContext.messages",         "fieldType": "array"  },
  "userSettings":   { "type": "jsExpression", "expression": "$vars.waitForMessage1.output.conversationContext.userSettings",     "fieldType": "object" }
}
```

**Write all five.** In Studio Web the author fills `context` and the panel derives the other four, but that derivation only runs in the editor — nothing derives them when the file is authored from the CLI.

Validation only requires `conversationId`, so it half-helps: leave that out and validate fails, but bind `context` and `conversationId` while dropping `exchangeId`, `messages` and `userSettings` and validate passes. The runtime reads all four, so that flow ships an agent with no chat history and no user settings.

Note the field is `latestExchangeId` inside `conversationContext`, not `exchangeId`.

## Bindings Are Objects, Not `=js:` Strings

Every expression binding in a `.flow` is the object form above. A bare `"=js:$vars.…"` string is a pre-1.3 file format that current files no longer use — Studio Web renders it as literal text rather than a binding, and nothing warns.

This matters when using `node add`, which writes `--input` JSON through untouched:

```bash
# WRONG — lands in the file verbatim, renders as text
uip maestro flow node add ChatFlow/ChatFlow.flow uipath.conversational.wait-for-message \
  -i '{"conversationId":"=js:$vars.conversationTrigger1.output.conversationId"}'

# RIGHT
uip maestro flow node add ChatFlow/ChatFlow.flow uipath.conversational.wait-for-message \
  -i '{"conversationId":{"type":"jsExpression","expression":"$vars.conversationTrigger1.output.conversationId","fieldType":"string"}}'
```

(`uip maestro flow node configure --detail` uses the `=js:` form for **connector** nodes — that is a different surface and does not apply here.)

## Node JSON

Editing the `.flow` directly carries the usual obligations — chiefly a `variables.nodes[]` entry for every data-producing node, which is what makes `$vars.<id>.output` resolve at all. See [editing-operations-json.md](../../editing-operations-json.md). `node add` writes those entries for you.

### Conversation trigger

Replace the default manual trigger — `flow init` scaffolds `core.trigger.manual`, and the conversation trigger is what makes the packaged flow conversational.

```bash
uip maestro flow node delete ChatFlow/ChatFlow.flow start
uip maestro flow node add ChatFlow/ChatFlow.flow core.trigger.conversation --position 256,144
```

### Wait for message

```json
{
  "id": "waitForMessage1",
  "type": "uipath.conversational.wait-for-message",
  "inputs": {
    "conversationId": { "type": "jsExpression", "expression": "$vars.conversationTrigger1.output.conversationId", "fieldType": "string" },
    "from": "User"
  }
}
```

### The agent — inline

`inputs.source` is the scaffolded UUID; `conversationalAgentSettings` is the five-key block above.

```bash
uip maestro flow node add ChatFlow/ChatFlow.flow uipath.agent.conversational \
  --position 768,144 --source <ProjectId> -i '<the settings JSON>'
```

### The agent — in-solution or published

Same settings block, different node type, and `isConversational` alongside it instead of `source`:

```json
{
  "id": "supportAgent1",
  "type": "uipath.core.agent.<projectId-or-guid>",
  "typeVersion": "<version from registry get>",
  "inputs": {
    "isConversational": true,
    "conversationalAgentSettings": { "...": "the five-key block above" }
  }
}
```

An in-solution agent needs its `definitions[]` entry fetched with `--local`; a published one comes from the pulled tenant registry.

### Get conversation context (rarely needed)

Reads recent exchanges without waiting. wait-for-message already returns the same context, so reach for this only when the flow needs the history at a point where it is not waiting — and note an unconnected one is legal and does not fail validation.

```json
{
  "id": "getConversationContext1",
  "type": "uipath.conversational.get-conversation-context",
  "inputs": {
    "conversationId": { "type": "jsExpression", "expression": "$vars.conversationTrigger1.output.conversationId", "fieldType": "string" },
    "exchangeLimit": 20
  }
}
```

### Send message (only when the flow itself speaks)

`conversationId`, `exchangeId`, `content`, `role` and `mimeType` are all required. `role` and `mimeType` each accept exactly one value, so write them as shown. `content` is normally a literal — the agent's own replies are streamed, not routed through this node.

```json
{
  "id": "sendMessage1",
  "type": "uipath.conversational.send-message",
  "inputs": {
    "conversationId": { "type": "jsExpression", "expression": "$vars.conversationTrigger1.output.conversationId", "fieldType": "string" },
    "exchangeId":     { "type": "jsExpression", "expression": "$vars.waitForMessage1.output.conversationContext.latestExchangeId", "fieldType": "string" },
    "content":        { "type": "literal", "expression": "Anything else I can help with?", "fieldType": "string" },
    "role": "assistant",
    "mimeType": "text/markdown"
  }
}
```

## Structured Outputs

An **inline** agent can return named fields for a downstream node to route on. Published and in-solution agents cannot.

Declare each field in two places or it yields nothing at run time:

| Where | What |
| --- | --- |
| the node, in the `.flow` | `inputs.agentOutputVariables: [{ "id": "shouldHandoff", "type": "boolean", "description": "..." }]` |
| the inline `agent.json` | the same field under `outputSchema.properties` |

Bind it downstream as `$vars.<agentNodeId>.output.shouldHandoff`. Writing one side without the other passes `agent validate` and `flow validate` — nothing checks the pair.

## Wire the Edges

An **inline** agent leaves on `success`; an in-solution or published one leaves on `output`. The smallest loop:

```bash
uip maestro flow edge add ChatFlow/ChatFlow.flow conversationTrigger1 waitForMessage1
uip maestro flow edge add ChatFlow/ChatFlow.flow waitForMessage1 conversationalAgent1
uip maestro flow edge add ChatFlow/ChatFlow.flow conversationalAgent1 waitForMessage1 --source-port success
```

Omit `--source-port success` and the command fails with `Source port "output" not found on node "conversationalAgent1". Available source ports: escalation, context, tool, success`.

## Validate

```bash
uip maestro flow validate ChatFlow/ChatFlow.flow
```

Unbound identifiers each report their own error, naming the node and field:

```
[nodes[waitForMessage1].inputs.conversationId]   [SCHEMA_ERROR] Conversation ID is required
[nodes[sendMessage1].inputs.exchangeId]          [SCHEMA_ERROR] Exchange ID is required
[nodes[sendMessage1].inputs.content]             [SCHEMA_ERROR] Content is required
[nodes[conversationalAgent1].inputs.conversationalAgentSettings.conversationId]
                                                 [CONVERSATIONAL_CONVERSATION_ID_REQUIRED] Conversation ID is required
```

A clean validate does **not** mean the bindings are right — see [planning.md § Output Variables](planning.md#output-variables).

## Pack and Ship

```bash
uip maestro flow pack ChatFlow ./dist --version 1.0.0
```

Confirm the marker in the packaged `content/operate.json`:

```json
"runtimeOptions": { "isConversational": true }
```

Absent means the flow does not start on `core.trigger.conversation`, and it will not be listed as a Conversational Agent.

## Debug — the CLI Hands Off

A chat cannot be driven headlessly, so `flow debug` uploads the solution and stops:

```bash
uip maestro flow debug ChatFlow --open-in-browser
```

Returns `Code: FlowDebugStudioWebHandoff` with `Data.studioWebUrl` and `Data.handedOff: true`, and no debug session is started. `--timeout` has no effect on this path.

Two chat UIs can drive the run — the CLI names both:

- **Studio Web** — open `Data.studioWebUrl` (`--open-in-browser` does it for you) and chat from its panel
- **UiPath Maestro VS Code extension** — open the flow and hit Debug

If the solution's `.uipx` already carries a `SolutionId`, the upload overwrites that solution rather than creating a second one.

## What NOT to Do

- **Do not stop at `context` and `conversationId`.** That combination validates clean and still ships an agent with no chat history — write all five.
- **Do not invent output paths.** `waitForMessage1.output.exchangeId` and `conversationalAgent1.output.response` do not exist, and validate accepts both.
- **Do not use `=js:` strings** for bindings in a `.flow`.
- **Do not carry one flavor's agent port across.** Inline continues on `success`, in-solution and published on `output`.
- **Do not add a send-message just to deliver the agent's reply.** The agent streams it.
- **Do not expect `flow debug` to run the conversation.** It hands off to Studio Web or the VS Code extension.
- **Do not leave the manual trigger in place.** Without `core.trigger.conversation` the package is not marked conversational, and nothing errors.
