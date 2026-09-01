# Critical Rules and Anti-Patterns - Autonomous Low-Code Agents

Canonical rules for low-code autonomous agent authoring. Capability files cross-reference this document rather than restating these rules. See [critical-rules.md](critical-rules.md).

## Critical Rules

1. **Use `uipath.agent.autonomous` for inline autonomous agents in flows.** Set the node's `inputs.source` to the inline agent's `projectId` UUID. Attached resource nodes (`uipath.agent.resource.tool.*`, `uipath.agent.resource.escalation`, `uipath.agent.resource.context.*`) use the same `inputs.source` convention to reference their `<RES_UUID>` subdirectory under `<projectId>/resources/`. The definition declares `model.source: true`; flow-core hoists the source identity to `inputs.source` for the node instance, so node instances must not contain an instance `model` block. Store the agent definition in a subdirectory of the flow project. See [../capabilities/inline-in-flow/inline-in-flow.md](../capabilities/inline-in-flow/inline-in-flow.md).

2. **Use `uip agent memory` for memory spaces and seed items.** These commands own `features/{FeatureName}/feature.json`, memory-item type validation, and generated `memorySpace` bindings. Attach existing memory spaces with `--memory-space` and literal `--folder-path`; add seed items with `--memory-type episodic|escalation`, and require `--feedback-id` for episodic seed items. After memory changes in a solution, run `uip agent refresh --output json`, run `uip agent validate --output json`, and then run `uip solution resources refresh --output json`. See [../capabilities/memory/memory.md](../capabilities/memory/memory.md).

## What NOT to Do

1. **Always include `"guardrail": { "policies": [] }` in every tool resource.json, and never populate `policies` with entries.** This field is required for backward-compatible solution loading; omitting it causes runtime failure. Configure all guardrails in the agent.json root `guardrails` array with `selector.scopes` and `selector.matchNames`. This anti-pattern applies only to autonomous agents; for conversational agents, populate `policies` per tool according to [conversational-critical-rules.md](conversational-critical-rules.md) Critical Rule 1 + Anti-pattern 2.

2. **Do not hand-edit memory feature files for routine changes.** Use `uip agent memory add/list/remove` and `uip agent memory item add/list/remove`. Hand-editing `features/{Name}/feature.json` or `bindings_v2.json` can desynchronize generated state and bypass CLI validation for search mode, field weights, metadata JSON, and memory item type.
