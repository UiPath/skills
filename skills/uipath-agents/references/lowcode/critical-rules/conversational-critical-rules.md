# Critical Rules and Anti-Patterns - Conversational Low-Code Agents

These rules are canonical for low-code conversational agent authoring, in addition to [critical-rules.md](critical-rules.md). Capability files cross-reference this document rather than restating these rules.

## Critical Rules

1. **Use only Custom (deterministic) Tool-scoped guardrails for conversational agents.** Run `uip agent guardrails list` to identify built-in validators; any `$guardrailType: "builtInValidator"` is autonomous-only. Author only `$guardrailType: "custom"` deterministic rules (`word`, `number`, `boolean`, or `always`) with `selector.scopes: ["Tool"]` in the `agent.json` root `guardrails[]`. Mirror each affected guardrail into `resources/<Tool>/resource.json` → `guardrail.policies[]`; the root is authoritative for UI and runtime because the CLI does not auto-sync. A guardrail only in the tool resource is invisible in Studio Web and does not run on the Unified (Python) runtime. `"Agent"` and `"Llm"` scopes are unavailable. For PII, harmful-content, or injection detection, explain that built-in validators are autonomous-only and offer a Custom deterministic Tool guardrail. See [../capabilities/guardrails/guardrails.md § Conversational Support](../capabilities/guardrails/guardrails.md#overview).

## What NOT to Do

1. **Do not add properties to `outputSchema`.** After initialization, leave `outputSchema` empty because conversational agents stream responses and tool-call events during execution; the final output is not relevant to the end user.

2. **Do not author `builtInValidator` guardrails or use any `selector.scopes` other than `["Tool"]`.** Put each Custom Tool guardrail in the `agent.json` root `guardrails[]` and mirror it in the affected `resources/<Tool>/resource.json` → `guardrail.policies[]`.

3. **Do not remove `messages[1]`.** Leave its message content fields blank after initialization; the runtime or other APIs may require its presence.

4. **Do not add `messages`, chat-history, or current-user-message/input fields to `agent.json`'s `inputSchema`.** `messages` is a hidden, reserved input for every conversational agent and represents the current conversation history when run from UiPath Conversational Service. No `inputSchema` field is needed for conversation history or the current user message.

5. **Do not add fields beginning with `uipath__` to `agent.json`'s `inputSchema`.** The `uipath__` prefix is reserved for internal inputs to every conversational-agent execution.
