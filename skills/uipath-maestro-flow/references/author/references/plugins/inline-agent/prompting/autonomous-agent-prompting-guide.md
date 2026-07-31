# Autonomous Agent Prompting Guide — Inline Agents

Prompting guide for inline autonomous agents (`uipath.agent.autonomous` node `inputs.systemPrompt` / `inputs.userPrompt`).

"Coding-agent-centric" = the prompt makes the embedded agent behave like a disciplined tool-using agent: explicit tool-call criteria, stop conditions, structured output. Maps to the agent's `tool` artifact port and `agentOutputVariables[]`.

## 1. System-prompt skeleton

Copy this skeleton into `inputs.systemPrompt`, fill every slot. Consistent structure → consistent runs. Put role/behavior here; data/task goes in the user prompt (§2).

```text
You are <ROLE> for <DOMAIN>. <ONE-LINE PURPOSE>.

Scope:
- In scope: <what the agent handles>
- Out of scope: <what to refuse or escalate>

Tools:
- <toolName>: call when <explicit condition>. Do not call when <condition>. Call at most <N> times (N ≤ 3 for a single decision).
- <toolName>: ...
Stop calling tools once <stop condition>; then produce the final answer.
If a tool result does not cover a detail, say so in <rationaleField>, lower <confidenceField>, and still return every declared output field. Never end a run without a final answer.

Output:
- Return a result conforming to the declared output variables. <field>: <how to fill it>.
- Never invent fields or values not grounded in the input or a tool result.

Uncertainty:
- If <required input> is missing or ambiguous, <ask | set field to null | escalate> — do not guess.
- If you cannot complete the task, return <explicit failure shape>, not a fabricated answer.
```

Slot rules:

- **Role + scope** — name the role, bound it. An unbounded agent answers off-task prompts.
- **Tool-call criteria** — one trigger condition per tool, plus a stop condition. Without this the agent over-calls or loops to `maxIterations`.
- **Output contract** — state that output MUST match the declared `agentOutputVariables`; map each field. Without it the agent free-forms prose.
- **Grounding** — forbid values not traceable to input or tool output. Cuts hallucination.
- **Iteration budget** — for multi-tool tasks, note the agent has limited iterations (`maxIterations`, default 25) and should act, not deliberate.

## 2. User-prompt anatomy

`inputs.userPrompt` carries the task and the data — not the role.

```text
<TASK INSTRUCTION>.

<LABEL>: {{ $vars.<flowNodeId>.output.<field> }}
<LABEL>: {{ $vars.<flowNodeId>.output.<field> }}

<EXPLICIT OUTPUT INSTRUCTION — e.g. "Return the category and a one-sentence reason.">
```

Tokens are the canvas form — spaced braces, `$vars`/`$metadata` namespace: `{{ $vars.<flowNodeId>.output.<field> }}`. Both prompts are plain strings; no `contentTokens`, no mirrors to maintain. Wiring prerequisites (trigger globals, real node ids): [impl.md § 4](../impl.md#4-wire-flow-data-into-prompts).

## 3. Grounding in wired data

Reference inputs through tokens — never restate their literal contents in prose. The runtime injects the value; restating it duplicates tokens and risks drift if the upstream field changes. Tell the agent *what the field is*, not *what it contains*.

## 4. Worked example — email triage

Realistic inline agent node. Note the **typed `agentOutputVariables`**, not a bare `content` blob.

**Before (toy):**

```json
"inputs": {
  "model": "gpt-5.4",
  "systemPrompt": "You are an assistant.",
  "userPrompt": "Triage this email.",
  "agentOutputVariables": [{ "id": "content", "type": "string" }]
}
```

**After (robust):**

```json
"inputs": {
  "model": "anthropic.claude-sonnet-4-6",
  "temperature": 0,
  "maxTokenPerResponse": 4096,
  "maxIterations": 10,
  "agentOutputVariables": [
    { "id": "category",   "type": "string",  "description": "One of: billing, technical, sales, other" },
    { "id": "priority",   "type": "string",  "description": "low | medium | high | urgent" },
    { "id": "reason",     "type": "string",  "description": "One sentence justifying the category" },
    { "id": "needsHuman", "type": "boolean", "description": "true if the email requires human review" }
  ]
}
```

System prompt (filled skeleton), in `inputs.systemPrompt`:

```text
You are a support-email triage classifier for a SaaS product. Classify each inbound email and flag those needing a human.

Scope:
- In scope: categorizing the email and assessing priority.
- Out of scope: replying to the customer or taking any action — only classify.

Output:
- Return a result conforming to the declared output variables. category MUST be one of billing, technical, sales, other. priority MUST be low, medium, high, or urgent.
- Set needsHuman=true for legal threats, churn risk, or anything outside the four categories.
- Never invent customer details not present in the email.

Uncertainty:
- If the email is empty or unintelligible, set category="other", needsHuman=true, reason="unintelligible input".
```

User prompt, in `inputs.userPrompt`:

```text
Classify the following email.

From: {{ $vars.emailReceived1.output.from }}
Subject: {{ $vars.emailReceived1.output.subject }}

{{ $vars.emailReceived1.output.body }}

Return category, priority, a one-sentence reason, and needsHuman.
```

## 5. Production checklist — adjacent node-`inputs` quality fields

A robust agent is more than its prompt. Each field: default, and when to change.

| Field | Default | Change when |
|-------|---------|-------------|
| `agentOutputVariables` | `[{"id": "content", "type": "string"}]` | **Almost always** — declare typed fields a downstream node can consume. Bare `content` forces brittle string-parsing. |
| `temperature` | `0` | Keep `0` for extraction/classification/judgment. Raise only when output *variation* is wanted (drafting, brainstorming). |
| `maxIterations` | `25` | `≤5` only if tool-less and single-shot. Kill switch, not a loop fix: without a per-tool cap the agent loops to the ceiling — observed dying at 5 and at 25 alike (`TERMINATION_MAX_ITERATIONS`). |
| `maxTokenPerResponse` | — | Set ≤ the model's `MaxTokens` cap — see [model-selection-guide.md](../model-selection-guide.md#1-discover-primary-path). |
| `model` | canvas-seeded / manifest default | **Always set explicitly** — discover + select per [model-selection-guide.md](../model-selection-guide.md). |
| `guardrails` | `[]` | Keep `[]` until the guardrails capability doc lands (per roadmap milestone). |

## Anti-patterns

- **Vague role** — "You are a helpful agentic assistant." Name the role and bound the scope.
- **No output contract** — agent free-forms prose; downstream nodes can't parse it.
- **Bare `content` output** — a single string where typed fields belong. Declare `agentOutputVariables`.
- **No tool-call criteria** — agent over-calls tools or loops to `maxIterations`.
- **Prompt-injection-prone passthrough** — pasting untrusted input into the system prompt. Keep untrusted data in the user prompt; keep instructions in the system prompt.
- **Ignoring the declared outputs** — prompt that doesn't tell the agent to conform to the declared output variables.
- **Cargo-culted `temperature`** — copying a nonzero temperature into a deterministic classification task.
- **Derived-namespace tokens** — `{{input.<flat>}}` / `{{ $agent.<flat> }}` belong to derived files only; flow prompts use `{{ $vars.* }}` (see [impl.md § 4](../impl.md#4-wire-flow-data-into-prompts)).
