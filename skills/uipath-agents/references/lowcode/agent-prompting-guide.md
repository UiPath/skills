# Agent Prompting Guide

Robust prompts for low-code agents. This guide owns prompt **quality**; [agent-definition.md](agent-definition.md#contenttokens-construction) owns the `contentTokens` **mechanics** (keep `content` ↔ `contentTokens` in sync after every edit here).

> Default scaffolds ship toy or empty prompts ("You are a helpful agentic assistant" / "What is the current date?" / ""). Replace them. A placeholder system prompt is the single biggest quality gap in a scaffolded agent.

## Autonomous Agents

This section defines the prompting guide for low-code autonomous agents.

"Coding-agent-centric" = the prompt makes the embedded agent behave like a disciplined tool-using agent: explicit tool-call criteria, stop conditions, structured output. Maps to the agent's `tool` artifact ports and `outputSchema`.

### 1. System-prompt skeleton

Copy this skeleton, fill every slot. Consistent structure → consistent runs. Put role/behavior here; data/task goes in the user message (§2).

```text
You are <ROLE> for <DOMAIN>. <ONE-LINE PURPOSE>.

Scope:
- In scope: <what the agent handles>
- Out of scope: <what to refuse or escalate>

Tools:
- <toolName>: call when <explicit condition>. Do not call when <condition>.
- <toolName>: ...
Stop calling tools once <stop condition>; then produce the final answer.

Output:
- Return a result conforming to the output schema. <field>: <how to fill it>.
- Never invent fields or values not grounded in the input or a tool result.

Uncertainty:
- If <required input> is missing or ambiguous, <ask | set field to null | escalate> — do not guess.
- If you cannot complete the task, return <explicit failure shape>, not a fabricated answer.
```

Slot rules:

- **Role + scope** — name the role, bound it. An unbounded agent answers off-task prompts.
- **Tool-call criteria** — one trigger condition per tool, plus a stop condition. Without this the agent over-calls or loops to `maxIterations`.
- **Output contract** — state that output MUST match `outputSchema`; map each field. Without it the agent free-forms prose.
- **Grounding** — forbid values not traceable to input or tool output. Cuts hallucination.
- **Iteration budget** — for multi-tool tasks, note the agent has limited iterations (`maxIterations`, default 25) and should act, not deliberate.

### 2. User-prompt anatomy

The user message carries the task and the data — not the role.

```text
<TASK INSTRUCTION>.

<LABEL>: {{ $vars.<flowNodeId>.output.<field> }}
<LABEL>: {{ $vars.<flowNodeId>.output.<field> }}

<EXPLICIT OUTPUT INSTRUCTION — e.g. "Return the category and a one-sentence reason.">
```

Token form depends on context:

- **Inline-in-flow agents** reference upstream flow nodes: `{{ $vars.<flowNodeId>.output[.<field>] }}`. See the [uipath-maestro-flow inline-agent prompt-wiring guide](../../../uipath-maestro-flow/references/author/references/plugins/inline-agent/impl.md#wiring-flow-variables-into-agent-prompts).
- **Standalone agents** reference declared inputs: `{{input.<field>}}`.

Mirror every `{{ ... }}` in `contentTokens[]` per [agent-definition.md § contentTokens Construction](agent-definition.md#contenttokens-construction).

### 3. Grounding in wired data

Reference inputs through tokens — never restate their literal contents in prose. The runtime injects the value; restating it duplicates tokens and risks drift if the upstream field changes. Tell the agent *what the field is*, not *what it contains*.

### 4. Worked example — email triage

Realistic inline-in-flow agent. Note the **structured `outputSchema`**, not a bare `content` blob.

**Before (toy):**

```json
"settings": { "model": "gpt-5.4" },
"outputSchema": { "type": "object", "properties": { "content": { "type": "string" } } },
"messages": [
  { "role": "system", "content": "You are an assistant." },
  { "role": "user", "content": "Triage this email." }
]
```

**After (robust):**

```json
"settings": { "model": "anthropic.claude-sonnet-4-6", "temperature": 0, "maxTokens": 4096, "maxIterations": 10 },
"outputSchema": {
  "type": "object",
  "properties": {
    "category": { "type": "string", "description": "One of: billing, technical, sales, other" },
    "priority": { "type": "string", "description": "low | medium | high | urgent" },
    "reason":   { "type": "string", "description": "One sentence justifying the category" },
    "needsHuman": { "type": "boolean", "description": "true if the email requires human review" }
  },
  "required": ["category", "priority", "needsHuman"]
}
```

System prompt (filled skeleton):

```text
You are a support-email triage classifier for a SaaS product. Classify each inbound email and flag those needing a human.

Scope:
- In scope: categorizing the email and assessing priority.
- Out of scope: replying to the customer or taking any action — only classify.

Output:
- Return a result conforming to the output schema. category MUST be one of billing, technical, sales, other. priority MUST be low, medium, high, or urgent.
- Set needsHuman=true for legal threats, churn risk, or anything outside the four categories.
- Never invent customer details not present in the email.

Uncertainty:
- If the email is empty or unintelligible, set category="other", needsHuman=true, reason="unintelligible input".
```

User prompt:

```text
Classify the following email.

From: {{ $vars.emailReceived1.output.from }}
Subject: {{ $vars.emailReceived1.output.subject }}

{{ $vars.emailReceived1.output.body }}

Return category, priority, a one-sentence reason, and needsHuman.
```

### 5. Production checklist — adjacent `agent.json` quality fields

A robust agent is more than its prompt. Each field: default, and when to change.

| Field | Default | Change when |
|-------|---------|-------------|
| `outputSchema` | Scaffold gives a single `content` string | **Almost always** — define typed fields a downstream node can consume. Bare `content` forces brittle string-parsing. |
| `settings.temperature` | `0` | Keep `0` for extraction/classification/judgment. Raise only when output *variation* is wanted (drafting, brainstorming). |
| `settings.maxIterations` | `25` | Lower (≤5) for single-shot classification. Higher for multi-tool research loops. |
| `settings.maxTokens` | Scaffold value | Set ≤ the model's `MaxTokens` cap — see [model-selection-guide.md](model-selection-guide.md#1-discover-primary-path). |
| `settings.model` | `gpt-5.4` | **Always override** — discover + select per [model-selection-guide.md](model-selection-guide.md). |
| `guardrails` | `[]` | Add input/output policy enforcement (PII, content, escalation). See [capabilities/guardrails/guardrails.md](capabilities/guardrails/guardrails.md). |

### Anti-patterns

- **Vague role** — "You are a helpful agentic assistant." Name the role and bound the scope.
- **No output contract** — agent free-forms prose; downstream nodes can't parse it.
- **Bare `content` output** — a single string where typed fields belong. Define `outputSchema`.
- **No tool-call criteria** — agent over-calls tools or loops to `maxIterations`.
- **Prompt-injection-prone passthrough** — pasting untrusted input into the system prompt. Keep untrusted data in the user message; keep instructions in the system message.
- **Ignoring `outputSchema`** — prompt that doesn't tell the agent to conform to the declared schema.
- **Cargo-culted `temperature`** — copying a nonzero temperature into a deterministic classification task.


## Conversational Agents

This section defines the prompting guide for low-code conversational agents.

### 1. System-prompt skeleton

The nature of conversational agents means that they involve multi-turn interaction with the user with flexible response shapes. Thus, conversational system prompts are more flexible than autonomous prompts; the following system-prompt skeleton serves as a starting point, not a contract. Adapt this skeleton to the use case: slots can be dropped or extended based on requirements and domain-specific goal(s).

```text
You are <ROLE> for <DOMAIN>. <ONE-LINE PURPOSE>. <DESCRIBE TONE — e.g. warm, concise, professional>.

Scope:
- In scope: <topics or tasks you engage with>
- Out of scope: <what to refuse, deflect, or hand off>

Conversation behavior and steps:
- Goal: help the user to <desired conversation goal(s)>.
- Flow: <describe the expected conversation path, if any>.
- Clarifications/confirmations: <when to ask a question, obtain clarification, and confirm actions>.

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
- **Conversation behavior** — Specify the desired outcome and goals, expected flow, clarification policies, confirmation points.
- **Tools** — Define use-case-specific triggers and non-triggers.
- **Response style** — Set default length and format.
- **Grounding** — State what the agent must not invent and which sources are authoritative for the domain. Cuts hallucination.

> For conversational agents, you may also template per-exchange `inputSchema` fields into the **system prompt** (not the user message, which stays blank for conversational agents). See [agent-definition.md § Input Schema](agent-definition.md#input-schema). Only add `inputSchema` fields when the use case needs variable-based context beyond conversation history. Reference them as `{{input.<field>}}` and mirror in `messages[0].contentTokens` per [agent-definition.md § contentTokens Construction](agent-definition.md#contenttokens-construction).

> For low-code conversational agents, the above defined system-prompt within the `agent.json` will be wrapped by more prompt details in the agent-runtime which describes citation generation behavior (e.g. for web-urls and context-grounding results). Do not define citation-generation format in the system-prompt.

### 2. User-prompt

Leave user-message contents blank for low-code conversational agents in the `agent.json`. See [agent-definition.md § User Message](agent-definition.md#user-message).

### 3. Worked example — customer support chat

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

Conversation behavior and steps:
- Goal: resolve the customer's question about the currently opened order in as few turns as possible.
- Flow: greet on turn 1 and reference the opened order; answer the question; confirm resolution.
- Clarifications/confirmations: if the customer asks about a different order, ask once for that order number. Confirm with the customer before initiating a return.

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

### 4. Production checklist — adjacent `agent.json` quality fields

| Field | Default | Change when |
|-------|---------|-------------|
| `inputSchema` | `{ "properties": {} }` | Add fields only when per-exchange, variable-based context beyond conversation history is genuinely needed. Reserved names: `messages`, `uipath__*` ([critical-rules.md](critical-rules.md) Anti-pattern 29). |
| `outputSchema` | `{ "type": "object", "properties": {} }` | **Never populate** — runtime streams events, does not fill output ([critical-rules.md](critical-rules.md) Anti-pattern 26). |
| `messages[1].content` | `""` | **Keep blank** — Conversational Service injects the user turn at runtime ([critical-rules.md](critical-rules.md) Anti-pattern 28). |
| `settings.temperature` | `0` | Raise for open-ended brainstorming or casual chats. Keep `0` for factual support flows. |
| `settings.maxTokens` | `64000` | Set ≤ the model's `MaxTokens` cap — see [model-selection-guide.md](model-selection-guide.md#1-discover-primary-path). |
| `settings.model` | `anthropic.claude-sonnet-4-5-20250929-v1:0` | **Always verify** — discover + select per [model-selection-guide.md](model-selection-guide.md). |
| `guardrails` | `[]` | Tool-scope only; mirror in tool `resource.json`. See [capabilities/guardrails/guardrails.md](capabilities/guardrails/guardrails.md) ([critical-rules.md](critical-rules.md) Rule 23). |

### Anti-patterns

- **Vague role** — "You are a helpful agentic assistant." Name the role and bound the scope.
- **No tool-call criteria** — agent over-calls or under-calls tools.
- **Long tool-call loops** - agent runtime may stop and require the user to confirm continuation after a single agent run (turn) consists of a series of over 8 steps that each involve tool-call(s). Note that this is not a limitation on total parallel tool-calls on any individual step, so aim to parallelize tool-calls when possible and/or ask for user-confirmation to break up long loops of sequential steps.
- **Populating `outputSchema`** — runtime streams events; populated schemas never get filled and confuse the agent ([critical-rules.md](critical-rules.md) Anti-pattern 26).
- **Templating data into the user message** — the user message content stays blank; per-exchange context goes into the **system prompt** via `inputSchema` templating.
- **Adding `messages` or `uipath__*` to `inputSchema`** — reserved names; runtime injects ([critical-rules.md](critical-rules.md) Anti-pattern 29).
- **Using `Agent` or `Llm` guardrail scopes** — silently ignored; only Tool-scope guardrails apply ([critical-rules.md](critical-rules.md) Rule 23).
- **Defining citation-generation format in the system prompt** — agent runtime wraps citation formatting around the prompt; redefining it conflicts or confuses citation generation (see § 1 callout).
- **Cargo-culted `temperature`** — copying a nonzero temperature into a deterministic, factual-based conversation task.
