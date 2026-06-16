# Critical Rules and Anti-Patterns - Conversational Low-Code Agents

These rules are the canonical source for rules specific to low-code conversational agent authoring, in addition to the shared rules defined in [critical-rules.md](critical-rules.md). Capability files cross-reference back here; they do not restate rules.

## Critical Rules

1. **Conversational agents support only Tool-scoped guardrails.** `selector.scopes` for conversational must be `["Tool"]` only — `"Agent"` and `"Llm"` scopes are not honored by the conversational runtime. `uip agent validate` accepts other scopes but they have no runtime effect. Author conversational guardrails in each affected tool's `resources/<Tool>/resource.json` under `guardrail.policies[]` (runtime-effective) AND mirror them at `agent.json` root `guardrails[]` (Studio Web display). See [../capabilities/guardrails/guardrails.md § Conversational Support](../capabilities/guardrails/guardrails.md#conversational-support).

## What NOT to Do

1. **Do not add properties to the `outputSchema` of a conversational agent.** After initialization, leave `outputSchema` empty. The conversational agent runtime streams responses/tool-call events during the execution, so the final output is not relevant for the end-user in the conversation.

2. **Do not set `selector.scopes` to anything other than `["Tool"]` for guardrails on a conversational agent, and do not put the guardrail only in `agent.json` root `guardrails[]`** — Agent- and Llm-scoped guardrails are not honored by the conversational runtime. The runtime reads guardrails from each tool's `resources/<Tool>/resource.json` → `guardrail.policies[]`; the `agent.json` root array is a Studio Web display mirror. Write to the tool resource (and mirror to agent.json root), per Critical Rule 1.

3. **Do not remove the user-message `messages[1]`, despite it being irrelevant for Conversational Agents.** Simply leave the message content fields blank. The runtime or other APIs may currently require its presence, so it should be simply left untouched with empty content after the conversational agent project is initialized.

4. **Do not add the field `messages` or any field representing chat-history or current user message/input to the `inputSchema` of the `agent.json`** — `messages` is a hidden, reserved input field for all conversational agents (regardless of `inputSchema`) which represents the current conversation-history when conversational agents are ran from the UiPath Conversational Service. This also means that there is no need to define any `inputSchema` field to represent the conversation history or current user message input.

5. **Do not add any fields with the `uipath__` prefix to the `inputSchema` of the `agent.json`** — the `uipath__` prefix is reserved for some internal inputs to every conversational agent execution.
