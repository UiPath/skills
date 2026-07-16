# Agents Playbooks

Covers errors from `uip agent` (low-code agents). Primary investigation surface: `uip traces spans get <trace-id> --output json`.

**Always check the `agentOutput` span even when the job reports success.** A run can complete without error while returning all-null output — this is a silent failure class not surfaced by Orchestrator job status.

**For multi-agent solutions, read the `.uis` / `.uipx` file before inspecting traces.** Unzip the solution file and compare the `outputSchema` of each upstream agent against the `inputSchema` of each downstream agent. Two failure classes are only visible at this layer:

- **Schema naming mismatch** — upstream outputs snake_case property names, downstream input schema defines PascalCase. The agent runtime populates schema-defined properties as null alongside the actual values, producing contradictory input to the model on every call.
- **Semantic contract mismatch** — upstream outputs a controlled-vocabulary value (a status marker, sentinel string, or code) that the downstream agent's prompt has no instruction for. Results in undefined model behavior on a specific input path. Detectable only by reading both prompts against the actual input values in the trace.

| Issue | Confidence | Description | Playbook |
|-------|:---:|-------------|----------|
| Input Schema Validation Failure | High | `agent.json failed schema validation` (Variant A: config schema) or `Data failed json schema validation DynamicType_0 BatchJson` (Variant B: input payload). Faults at agent startup before any LLM call. | [input-schema-validation-failure.md](./playbooks/input-schema-validation-failure.md) |
| Context Grounding Index Not Found | High | `ContextGroundingIndex not found Code: AGENT_RUNTIME.UNEXPECTED_ERROR` on a `contextGroundingTool` span. Grounding index deleted or mis-referenced after publish. | [context-grounding-index-not-found.md](./playbooks/context-grounding-index-not-found.md) |
| LLM Call Failed — Insufficient Information | Medium | `{"detail":"Insufficient information..."}` on a `completion` or `agentRun` span. System prompt too vague or required input missing from caller payload. | [llm-insufficient-information.md](./playbooks/llm-insufficient-information.md) |
| Guardrail Violation | High | `AGENT_RUNTIME.TERMINATION_GUARDRAIL_VIOLATION` on `agentRun` span or a `{agent\|llm\|tool}{Pre\|Post}Guardrails` container span. Pre-stage = input-side block; post-stage = output-side block. Trigger payload on `guardrailEvaluation`/`toolGuardrailEvaluation` child span. Also fires when Escalate action reviewer rejects. | [guardrail-violation.md](./playbooks/guardrail-violation.md) |
| IS Connection Disabled (403) | Medium | IS Event call returns 403 — connection disabled after consecutively failing to refresh the token; re-authenticate to restore. | [is-connection-disabled.md](./playbooks/is-connection-disabled.md) |
| IS Invalid Credentials (401) | High | IS call returns 401 — most common cause: connection in wrong folder or personal workspace (folder/scope mismatch). Also: Org/User secret or Element token rotated, expired, or sandbox/production mismatch. | [is-invalid-credentials.md](./playbooks/is-invalid-credentials.md) |
| IS Invalid Element Instance (404) | High | IS call returns 404 — Element Instance Id referenced in the agent was deleted, or the agent was deployed to an environment where the connection doesn't exist. | [is-invalid-element-instance.md](./playbooks/is-invalid-element-instance.md) |
