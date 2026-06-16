# Conversational Agents Prompting Guide

This is the prompting guide for low-code conversational agents.

## 1. System-prompt skeleton

The nature of conversational agents means that they involve multi-turn interaction with the user with flexible response shapes. Thus, conversational system prompts are more flexible than autonomous prompts; the following system-prompt skeleton serves as a starting point, not a contract. Adapt this skeleton to the use case: slots can be dropped or extended based on requirements and domain-specific goal(s).

```text
You are <ROLE> for <DOMAIN>. <ONE-LINE PURPOSE>. <DESCRIBE TONE — e.g. warm, concise, professional>.

Scope:
- In scope: <topics or tasks you engage with>
- Out of scope: <what to refuse, deflect, or hand off>

Conversation behavior:
- Goals: <desired outcome(s) of the conversation>.
- Steps: <expected sequence; may not be needed for free-form chat>.
- Clarifications: <when to ask before answering>.
- Confirmations: <when to confirm before actions>.

Tools:
- <toolName>: call when <explicit condition>. Do not call when <condition>.
- <toolName>: ...
- After tool use, explain <what to summarize, recommend, or ask next>.

Response style:
- Default to <length — e.g. 2–4 sentences>; expand on request.
- Use <format — markdown, bullets, JSON, prose> when helpful.

Uncertainty:
- If <context> is missing or ambiguous, <ask clarifications / run tools> — do not guess.
```

Slot rules (flexible):
- **Role + tone** — name the role, set the voice.
- **Scope** — bound what the agent engages with. Without it the agent answers off-task prompts.
- **Conversation behavior** — desired conversational outcomes and steps for how the agent should drive the conversation. Slots can be omitted/modified based on use-case.
- **Tools** — Define use-case-specific triggers and non-triggers.
- **Response style** — Set default length and format.
- **Grounding** — State what the agent must not invent and which sources are authoritative for the domain. Cuts hallucination.

> For conversational agents, you may also template per-exchange `inputSchema` fields into the **system prompt** (not the user message, which stays blank for conversational agents). See [agent-definition.md § Input Schema](../agent-definition.md#input-schema). Only add `inputSchema` fields when the use case needs variable-based context from the chat-UI beyond the conversation history and the user's input messages (which are already captured in the implicit `messages` field for all conversational-agents). Reference them as `{{input.<field>}}` and mirror in `messages[0].contentTokens` per [agent-definition.md § contentTokens Construction](../agent-definition.md#contenttokens-construction).

> For low-code conversational agents, the above defined system-prompt within the `agent.json` will be wrapped by more prompt details in the agent-runtime which describes citation generation behavior (e.g. for web-urls and context-grounding results). Do not define citation-generation format in the system-prompt.

## 2. User-prompt

Leave user-message contents blank for low-code conversational agents in the `agent.json`. See [agent-definition.md § User Message](../agent-definition.md#user-message).

## 3. Worked example — customer support chat

Realistic conversational agent: an order-status helpdesk with one tool. Note `inputSchema` carrying a per-exchange `currentOrderNumber` (the order the user currently has open in the host UI) and **empty `outputSchema`** (runtime streams conversation events).

`agent.json` excerpt:

```json
"settings": { "model": "anthropic.claude-sonnet-4-6", "temperature": 0, "maxTokens": 64000, "engine": "conversational-v1", "mode": "standard" },
"inputSchema": {
  "type": "object",
  "properties": {
    "currentOrderNumber": { "type": "string", "description": "Order number currently open in the host UI; supplied by the client on every exchange" }
  },
  "required": ["currentOrderNumber"]
},
"outputSchema": { "type": "object", "properties": {} }
```

System prompt (filled skeleton):

```text
You are an company's customer support assistant for online retail. Help customers with order status, delivery, and returns. Tone: warm, concise, professional.

The customer currently has the following order open: {{input.currentOrderNumber}}.

Scope:
- In scope: order status, delivery estimates, returns and refunds, basic product questions.
- Out of scope: pricing negotiations, escalations requiring human review — hand off to a human agent.

Conversation behavior:
- Goals: resolve the customer's queries about the currently opened order in as few turns as possible.
- Steps: greet on turn 1, reference the opened order, and explain capabilities. Then answer the queries and confirm resolution.
- Clarifications: if the customer asks about a different order, ask once for that order number.
- Confirmations: confirm with the customer before initiating a return.

Tools:
- lookupOrder: call with the currently opened order number unless the customer specifies a different one. Use for status, delivery, or item details.
- initiateReturn: call only after the customer confirms in plain language they want to start a return.
- After tool use, summarize the result in 1-2 sentences and ask whether anything else is needed.

Response style:
- Default to 2-4 sentences; expand only when the customer asks for detail.
- Use plain prose; switch to bullets for multi-item summaries (e.g., multiple shipment events).

Uncertainty:
- If `lookupOrder` returns no record, ask the customer to verify the order number — do not guess details.
```

User message: `""` — left blank. The Conversational Service injects the user turn each exchange.

## 4. Production checklist — adjacent `agent.json` quality fields

| Field | Default | Change when |
|-------|---------|-------------|
| `inputSchema` | `{ "properties": {} }` | Add fields only when per-exchange, variable-based context beyond conversation history is genuinely needed. Reserved names: `messages`, `uipath__*` ([critical-rules/conversational-critical-rules.md](../critical-rules/conversational-critical-rules.md) Anti-patterns 4 and 5). |
| `outputSchema` | `{ "type": "object", "properties": {} }` | **Never populate** — runtime streams events, does not fill output ([critical-rules/conversational-critical-rules.md](../critical-rules/conversational-critical-rules.md) Anti-pattern 1). |
| `messages[1].content` | `""` | **Keep blank** — Conversational Service injects the user turn at runtime ([critical-rules/conversational-critical-rules.md](../critical-rules/conversational-critical-rules.md) Anti-pattern 3). |
| `settings.temperature` | `0` | Raise for open-ended brainstorming or casual chats. Keep `0` for factual support flows. |
| `settings.maxTokens` | `64000` | Set ≤ the model's `MaxTokens` cap — see [model-selection-guide.md](../model-selection-guide.md#1-discover-primary-path). |
| `settings.model` | `anthropic.claude-sonnet-4-5-20250929-v1:0` | **Always verify** — discover + select per [model-selection-guide.md](../model-selection-guide.md). |
| `guardrails` | `[]` | Tool-scope only; mirror in tool `resource.json`. See [capabilities/guardrails/guardrails.md](../capabilities/guardrails/guardrails.md) ([critical-rules/conversational-critical-rules.md](../critical-rules/conversational-critical-rules.md) Critical Rule 1). |

## Anti-patterns

- **Vague role** — "You are a helpful agentic assistant." Name the role and bound the scope.
- **No tool-call criteria** — agent over-calls or under-calls tools.
- **Long tool-call loops** - agent runtime may stop and require the user to confirm continuation after a single agent run (turn) consists of a series of over 8 steps that each involve tool-call(s). Note that this is not a limitation on total parallel tool-calls on any individual step, so aim to parallelize tool-calls when possible and/or ask for user-confirmation to break up long loops of sequential steps.
- **Populating `outputSchema`** — runtime streams events; populated schemas never get filled and confuse the agent ([critical-rules/conversational-critical-rules.md](../critical-rules/conversational-critical-rules.md) Anti-pattern 1).
- **Templating data into the user message** — the user message content stays blank; per-exchange context goes into the **system prompt** via `inputSchema` templating.
- **Adding `messages` or `uipath__*` to `inputSchema`** — reserved names; runtime injects ([critical-rules/conversational-critical-rules.md](../critical-rules/conversational-critical-rules.md) Anti-patterns 4 and 5).
- **Using `Agent` or `Llm` guardrail scopes** — silently ignored; only Tool-scope guardrails apply ([critical-rules/conversational-critical-rules.md](../critical-rules/conversational-critical-rules.md) Critical Rule 1).
- **Defining citation-generation format in the system prompt** — agent runtime wraps citation formatting around the prompt; redefining it conflicts or confuses citation generation (see § 1 callout).
- **Cargo-culted `temperature`** — copying a nonzero temperature into a deterministic, factual-based conversation task.
