# Conversational Agents Prompting Guide

Prompting guidance for low-code conversational agents.

## 1. System-prompt skeleton

Use this as a starting point; adapt sections to the use case.

```text
You are <ROLE> for <DOMAIN>. <ONE-LINE PURPOSE>. <TONE — e.g. warm, concise, professional>.

Scope:
- In scope: <topics or tasks>
- Out of scope: <what to refuse, deflect, or hand off>

Conversation behavior:
- Goals: <desired outcome(s)>.
- Steps: <expected sequence; omit for free-form chat when appropriate>.
- Clarifications: <when to ask before answering>.
- Confirmations: <when to confirm before actions>.

Tools:
- <toolName>: call when <explicit condition>. Do not call when <condition>.
- <toolName>: ...
- After tool use, <summarize, recommend, or ask what comes next>.

Response style:
- Default to <length — e.g. 2–4 sentences>; expand on request.
- Use <format — markdown, bullets, JSON, or prose> when helpful.

Uncertainty:
- If <context> is missing or ambiguous, <ask for clarification / run tools>; do not guess.
```

Define the role and tone; bound in- and out-of-scope topics; specify goals, steps, clarifications, confirmations, tool triggers and non-triggers, post-tool behavior, response length and format, authoritative grounding sources, and information the agent must not invent.

For per-exchange `inputSchema` context beyond conversation history and user messages, template fields into the **system prompt**, not the user message. Reference them as `{{input.<field>}}` and mirror them in `messages[0].contentTokens` according to [agent-definition.md § Input Schema](../agent-definition.md#schemas) and [agent-definition.md § contentTokens Construction](../agent-definition.md#messages-and-contenttokens). User messages are already captured in the implicit `messages` field.

The runtime wraps the `agent.json` system prompt with citation-generation behavior for web URLs and context-grounding results. Do not define citation-generation format in the system prompt.

## 2. User prompt

Leave the user-message content blank in `agent.json`; Conversational Service injects each user turn at runtime. See [agent-definition.md § User Message](../agent-definition.md#messages-and-contenttokens).

## 3. Minimal configuration pattern

Use an empty `outputSchema`; conversational runtimes stream events rather than filling a declared output. Add `inputSchema` fields only for genuinely needed per-exchange context and reference them in the system prompt.

```json
"inputSchema": {
  "type": "object",
  "properties": {
    "<contextField>": { "type": "string", "description": "Per-exchange context supplied by the client" }
  }
},
"outputSchema": { "type": "object", "properties": {} }
```

Explicitly define role, scope, goals, tool-call conditions, confirmation requirements, response style, and uncertainty handling. For tool-enabled flows, call lookup or action tools only under their stated conditions, summarize results, and ask what is needed next. Confirm before consequential actions; request missing identifiers instead of guessing.

## 4. Production checklist — adjacent `agent.json` quality fields

| Field | Default | Change when |
|-------|---------|-------------|
| `inputSchema` | `{ "properties": {} }` | Add fields only when per-exchange, variable-based context beyond conversation history is genuinely needed. Reserved names: `messages`, `uipath__*` ([critical-rules/conversational-critical-rules.md](../critical-rules/conversational-critical-rules.md) Anti-patterns 4 and 5). |
| `outputSchema` | `{ "type": "object", "properties": {} }` | **Never populate** — runtime streams events, does not fill output ([critical-rules/conversational-critical-rules.md](../critical-rules/conversational-critical-rules.md) Anti-pattern 1). |
| `messages[1].content` | `""` | **Keep blank** — Conversational Service injects the user turn at runtime ([critical-rules/conversational-critical-rules.md](../critical-rules/conversational-critical-rules.md) Anti-pattern 3). |
| `settings.temperature` | `0` | Raise for open-ended brainstorming or casual chats. Keep `0` for factual support flows. |
| `settings.maxTokens` | `64000` | Set ≤ the model's `MaxTokens` cap — see [model-selection-guide.md](../model-selection-guide.md#1-discover). |
| `settings.model` | `anthropic.claude-sonnet-4-5-20250929-v1:0` | **Always verify** — discover + select per [model-selection-guide.md](../model-selection-guide.md). |
| `guardrails` | `[]` | Custom (deterministic) Tool guardrails only — no built-in validators; mirror in tool `resource.json`. See [capabilities/guardrails/guardrails.md](../capabilities/guardrails/guardrails.md) ([critical-rules/conversational-critical-rules.md](../critical-rules/conversational-critical-rules.md) Critical Rule 1). |

## Anti-patterns

- **Vague role:** do not use only “You are a helpful agentic assistant.” Name the role and bound the scope.
- **No tool-call criteria:** define when each tool is and is not called.
- **Long tool-call loops:** the agent runtime may stop and require the user to confirm continuation after a single agent run (turn) consists of a series of over 8 steps that each involve tool-call(s). This is not a limitation on total parallel tool-calls on any individual step; parallelize when possible and/or ask for user confirmation to break up long sequential loops.
- **Populating `outputSchema`:** runtime streams events; populated schemas never get filled and confuse the agent ([critical-rules/conversational-critical-rules.md](../critical-rules/conversational-critical-rules.md) Anti-pattern 1).
- **Templating data into the user message:** keep the user message blank; put per-exchange context in the **system prompt** through `inputSchema` templating.
- **Adding `messages` or `uipath__*` to `inputSchema`:** these are reserved names; runtime injects them ([critical-rules/conversational-critical-rules.md](../critical-rules/conversational-critical-rules.md) Anti-patterns 4 and 5).
- **Using unsupported guardrails:** built-in validators for PII, harmful content, and similar purposes, as well as `Agent`/`Llm` scopes, are autonomous-only and silently ignored. Conversational agents support only Custom deterministic `Tool`-scoped guardrails ([critical-rules/conversational-critical-rules.md](../critical-rules/conversational-critical-rules.md) Critical Rule 1).
- **Defining citation-generation format in the system prompt:** the runtime wraps citation formatting around the prompt; redefining it conflicts with or confuses citation generation.
- **Cargo-culted `temperature`:** do not copy a nonzero temperature into a deterministic, factual-based conversation task.
