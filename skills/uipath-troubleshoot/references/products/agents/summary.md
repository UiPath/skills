# Agents Playbooks

Covers errors from `uip agent` (low-code agents). Primary investigation surface: `uip traces spans get <trace-id> --output json`.

| Issue | Confidence | Description | Playbook |
|-------|:---:|-------------|----------|
| Input Schema Validation Failure | High | `agent.json failed schema validation` (Variant A: config schema) or `Data failed json schema validation DynamicType_0 BatchJson` (Variant B: input payload). Faults at agent startup before any LLM call. | [input-schema-validation-failure.md](./playbooks/input-schema-validation-failure.md) |
| Context Grounding Index Not Found | High | `ContextGroundingIndex not found Code: AGENT_RUNTIME.UNEXPECTED_ERROR` on a `contextGroundingTool` span. Grounding index deleted or mis-referenced after publish. | [context-grounding-index-not-found.md](./playbooks/context-grounding-index-not-found.md) |
| LLM Call Failed — Insufficient Information | Medium | `{"detail":"Insufficient information..."}` on a `completion` or `agentRun` span. System prompt too vague or required input missing from caller payload. | [llm-insufficient-information.md](./playbooks/llm-insufficient-information.md) |
| Guardrail Violation | High | `AGENT_RUNTIME.TERMINATION_GUARDRAIL_VIOLATION` on `agentRun` span or a `{agent\|llm\|tool}{Pre\|Post}Guardrails` container span. Pre-stage = input-side block; post-stage = output-side block. Trigger payload on `guardrailEvaluation`/`toolGuardrailEvaluation` child span. Also fires when Escalate action reviewer rejects. | [guardrail-violation.md](./playbooks/guardrail-violation.md) |
| IS Connection Forbidden (403) | Medium | IS Event call returns 403 — connection disabled after repeated failed attempts; IS locked out the connection. | [is-connection-forbidden.md](./playbooks/is-connection-forbidden.md) |
| IS Invalid Credentials (401) | High | IS call returns 401 — stored credentials (Org/User secret or Element token) were rotated, expired, or belong to the wrong environment. | [is-invalid-credentials.md](./playbooks/is-invalid-credentials.md) |
| IS Invalid Element Instance (404) | High | IS call returns 404 — Element Instance Id referenced in the agent was deleted, or the agent was deployed to an environment where the connection doesn't exist. | [is-invalid-element-instance.md](./playbooks/is-invalid-element-instance.md) |
