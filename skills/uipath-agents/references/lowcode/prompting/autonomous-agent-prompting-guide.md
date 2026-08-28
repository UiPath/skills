# Autonomous Agents Prompting Guide

Prompt low-code autonomous agents as disciplined, tool-using agents: define tool-call criteria, stop conditions, and structured output. This maps to the agent's `tool` artifact ports and `outputSchema`.

## 1. System-prompt skeleton

Use this structure and fill every slot. Keep role and behavior in the system prompt; put task data in the user message (§2).

```text
You are <ROLE> for <DOMAIN>. <ONE-LINE PURPOSE>.

Scope:
- In scope: <what the agent handles>
- Out of scope: <what to refuse or escalate>

Tools:
- <toolName>: call when <explicit condition>. Do not call when <condition>. Call at most <N> times (N ≤ 3 for a single decision).
- <toolName>: ...
Stop calling tools once <stop condition>; then produce the final answer.
If a tool result does not cover a detail, say so in <rationaleField>, lower <confidenceField>, and still return every outputSchema field. Never end a run without a final answer.

Output:
- Return a result conforming to the output schema. <field>: <how to fill it>.
- Never invent fields or values not grounded in the input or a tool result.

Uncertainty:
- If <required input> is missing or ambiguous, <ask | set field to null | escalate> — do not guess.
- If you cannot complete the task, return <explicit failure shape>, not a fabricated answer.
```

Slot rules:

- **Role + scope:** name and bound the role; unbounded agents answer off-task prompts.
- **Tool-call criteria:** give each tool one trigger, a stop condition, and a cap. Otherwise the agent may over-call or loop to `maxIterations`.
- **Output contract:** require `outputSchema` conformance and explain every field; otherwise the agent may free-form prose.
- **Grounding:** forbid values not traceable to input or tool output.
- **Iteration budget:** multi-tool agents have limited iterations (`maxIterations`, default 25); instruct them to act rather than deliberate.

## 2. User-prompt anatomy

The user message carries the task and data, not the role.

```text
<TASK INSTRUCTION>.

<LABEL>: {{ $vars.<flowNodeId>.output.<field> }}
<LABEL>: {{ $vars.<flowNodeId>.output.<field> }}

<EXPLICIT OUTPUT INSTRUCTION — e.g. "Return the category and a one-sentence reason.">
```

Token syntax:

- **Inline-in-flow agents:** reference upstream flow nodes with `{{ $vars.<flowNodeId>.output[.<field>] }}`. See the [uipath-maestro-flow inline-agent prompt-wiring guide](../../../../uipath-maestro-flow/references/author/plugins/inline-agent/impl.md#wiring-flow-variables-into-agent-prompts).
- **Standalone agents:** reference declared inputs with `{{input.<field>}}`.

Mirror every `{{ ... }}` in `contentTokens[]` per [agent-definition.md § contentTokens Construction](../agent-definition.md#messages-and-contenttokens).

## 3. Grounding in wired data

Reference inputs through tokens; never restate their literal contents in prose. Runtime injection avoids duplication and drift when upstream fields change. Describe what each field is, not what it contains. Keep untrusted data in the user message and instructions in the system message; do not paste untrusted input into the system prompt.

## 4. Typed output pattern

Use a typed schema rather than a bare `content` blob. Define fields that downstream nodes can consume, describe how to fill every field, and require the agent to return the schema exactly. For classification, constrain enum-like fields explicitly (for example, `category` values and `priority` values), include a concise `reason` when needed, and use a boolean escalation field such as `needsHuman` when review is required. If input is empty or unintelligible, use an explicit safe fallback, set escalation as appropriate, and do not invent details.

## 5. Production checklist — adjacent `agent.json` quality fields

| Field | Default | Change when |
|-------|---------|-------------|
| `outputSchema` | Scaffold gives a single `content` string | **Almost always** — define typed fields downstream nodes can consume; bare `content` requires brittle string parsing. |
| `settings.temperature` | `0` | Keep `0` for extraction/classification/judgment. Raise only when output variation is wanted (drafting, brainstorming). |
| `settings.maxIterations` | `25` | `≤5` only if tool-less and single-shot. This is a kill switch, not a loop fix: without a per-tool cap the agent loops to the ceiling — observed dying at 5 and at 25 alike (`TERMINATION_MAX_ITERATIONS`). |
| `settings.maxTokens` | Scaffold value | Set ≤ the model's `MaxTokens` cap — see [model-selection-guide.md](../model-selection-guide.md#1-discover). |
| `settings.model` | `gpt-5.4` | **Always override** — discover and select per [model-selection-guide.md](../model-selection-guide.md). |
| `guardrails` | `[]` | Add input/output policy enforcement (PII, content, escalation). See [capabilities/guardrails/guardrails.md](../capabilities/guardrails/guardrails.md). |

## Anti-patterns

- **Vague role:** “You are a helpful agentic assistant.” Name and bound the role.
- **No output contract:** free-form prose prevents downstream parsing.
- **Bare `content` output:** define typed `outputSchema` fields instead.
- **No tool-call criteria:** causes over-calling or loops to `maxIterations`.
- **Prompt-injection-prone passthrough:** keep untrusted data in the user message and instructions in the system message; do not paste untrusted input into the system prompt.
- **Ignoring `outputSchema`:** explicitly require conformity to the declared schema.
- **Cargo-culted `temperature`:** do not copy nonzero temperature into deterministic classification tasks.