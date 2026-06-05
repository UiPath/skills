# Agent Prompting Guide

Robust prompts for low-code agents. This guide owns prompt **quality**; [agent-definition.md](agent-definition.md#contenttokens-construction) owns the `contentTokens` **mechanics** (keep `content` ↔ `contentTokens` in sync after every edit here).

"Coding-agent-centric" = the prompt makes the embedded agent behave like a disciplined tool-using agent: explicit tool-call criteria, stop conditions, structured output. Maps to the agent's `tool` artifact ports and `outputSchema`.

> Default scaffolds ship toy prompts ("You are an agentic assistant" / "What is the current date?"). Replace them. A placeholder system prompt is the single biggest quality gap in a scaffolded agent.

## 1. System-prompt skeleton

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

## 2. User-prompt anatomy

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

## 3. Grounding in wired data

Reference inputs through tokens — never restate their literal contents in prose. The runtime injects the value; restating it duplicates tokens and risks drift if the upstream field changes. Tell the agent *what the field is*, not *what it contains*.

## 4. Worked example — email triage

Realistic inline-in-flow agent. Note the **structured `outputSchema`**, not a bare `content` blob.

**Before (toy):**

```json
"settings": { "model": "gpt-4o-2024-11-20" },
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

## 5. Production checklist — adjacent `agent.json` quality fields

A robust agent is more than its prompt. Each field: default, and when to change.

| Field | Default | Change when |
|-------|---------|-------------|
| `outputSchema` | Scaffold gives a single `content` string | **Almost always** — define typed fields a downstream node can consume. Bare `content` forces brittle string-parsing. |
| `settings.temperature` | `0` | Keep `0` for extraction/classification/judgment. Raise only when output *variation* is wanted (drafting, brainstorming). |
| `settings.maxIterations` | `25` | Lower (≤5) for single-shot classification. Higher for multi-tool research loops. |
| `settings.maxTokens` | Scaffold value | Set ≤ the model's `MaxTokens` cap — see [model-selection-guide.md](model-selection-guide.md#1-discover-primary-path). |
| `settings.model` | `gpt-4o-2024-11-20` | **Always override** — discover + select per [model-selection-guide.md](model-selection-guide.md). |
| `guardrails` | `[]` | Add input/output policy enforcement (PII, content, escalation). See [capabilities/guardrails/guardrails.md](capabilities/guardrails/guardrails.md). |

## Anti-patterns

- **Vague role** — "You are an assistant." Name the role and bound the scope.
- **No output contract** — agent free-forms prose; downstream nodes can't parse it.
- **Bare `content` output** — a single string where typed fields belong. Define `outputSchema`.
- **No tool-call criteria** — agent over-calls tools or loops to `maxIterations`.
- **Prompt-injection-prone passthrough** — pasting untrusted input into the system prompt. Keep untrusted data in the user message; keep instructions in the system message.
- **Ignoring `outputSchema`** — prompt that doesn't tell the agent to conform to the declared schema.
- **Cargo-culted `temperature`** — copying a nonzero temperature into a deterministic classification task.
