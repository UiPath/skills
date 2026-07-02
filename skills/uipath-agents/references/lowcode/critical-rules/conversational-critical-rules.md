# Critical Rules and Anti-Patterns - Conversational Low-Code Agents

These rules are the canonical source for rules specific to low-code conversational agent authoring, in addition to the shared rules defined in [critical-rules.md](critical-rules.md). Capability files cross-reference back here; they do not restate rules.

## Critical Rules

1. **Conversational agents support ONLY Custom (deterministic) guardrails scoped to a Tool.** Built-in validators (any `$guardrailType: "builtInValidator"` — the validators returned by `uip agent guardrails list`) are **autonomous-only**. Author only `$guardrailType: "custom"` deterministic rules (word/number/boolean/always) with `selector.scopes: ["Tool"]` at the `agent.json` root `guardrails[]` (authoritative for UI + runtime), mirrored into each affected tool's `resources/<Tool>/resource.json` → `guardrail.policies[]`. Write both (the CLI doesn't auto-sync), but treat the root as the source of truth — a guardrail only in the tool resource is invisible in Studio Web and does not run on the Unified (Python) runtime. `"Agent"` and `"Llm"` scopes are not available. If asked for PII / harmful-content / injection detection on a conversational agent, explain built-in validators are autonomous-only and offer a Custom deterministic Tool guardrail. See [../capabilities/guardrails/guardrails.md § Conversational Support](../capabilities/guardrails/guardrails.md#conversational-support).

## What NOT to Do

1. **Do not add properties to the `outputSchema` of a conversational agent.** After initialization, leave `outputSchema` empty. The conversational agent runtime streams responses/tool-call events during the execution, so the final output is not relevant for the end-user in the conversation.

2. **Do not author any `builtInValidator` guardrail on a conversational agent, and do not set `selector.scopes` to anything other than `["Tool"]`.** Built-in validators (any `$guardrailType: "builtInValidator"`) are autonomous-only; Agent- and Llm-scoped guardrails are likewise not honored. Author the Custom `Tool` guardrail at the `agent.json` root `guardrails[]` (authoritative for UI + runtime) and mirror it into the tool's `resources/<Tool>/resource.json` → `guardrail.policies[]`; a guardrail only in the tool resource is invisible in Studio Web and does not run on the Unified (Python) runtime, per Critical Rule 1.

3. **Do not remove the user-message `messages[1]`, despite it being irrelevant for Conversational Agents.** Simply leave the message content fields blank. The runtime or other APIs may currently require its presence, so it should be simply left untouched with empty content after the conversational agent project is initialized.

4. **Do not add the field `messages` or any field representing chat-history or current user message/input to the `inputSchema` of the `agent.json`** — `messages` is a hidden, reserved input field for all conversational agents (regardless of `inputSchema`) which represents the current conversation-history when conversational agents are ran from the UiPath Conversational Service. This also means that there is no need to define any `inputSchema` field to represent the conversation history or current user message input.

5. **Do not add any fields with the `uipath__` prefix to the `inputSchema` of the `agent.json`** — the `uipath__` prefix is reserved for some internal inputs to every conversational agent execution.
