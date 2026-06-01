# Agents Playbook Index

Covers errors from `uip agent` (low-code agents). Primary investigation surface: `uip traces spans get <traceId> --output json`.

## High Confidence

- [Input Schema Validation Failure](playbooks/input-schema-validation-failure.md) — `agent.json failed schema validation` (Variant A) or `Data failed json schema validation` for `DynamicType_0 BatchJson` (Variant B). Faults at agent startup before any LLM call.
- [Context Grounding Index Not Found](playbooks/context-grounding-index-not-found.md) — `ContextGroundingIndex not found Code: AGENT_RUNTIME.UNEXPECTED_ERROR`. Grounding index deleted or mis-referenced after publish.

## Medium Confidence

- [LLM Call Failed — Insufficient Information in Prompt](playbooks/llm-insufficient-information.md) — `{"detail":"Insufficient information..."}` on a `completion` or `agentRun` span. System prompt too vague or required input missing from caller payload.
